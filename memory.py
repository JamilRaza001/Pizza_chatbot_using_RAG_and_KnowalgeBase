"""
Broadway Pizza Chatbot - Memory Management
===========================================
Handles persistent chat history, summarization, and context window management.
"""

import json
import logging
import time
from datetime import datetime
from functools import wraps
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
import os

from config import (
    setup_logging,
    MEMORY_BUFFER_SIZE,
    MEMORY_SUMMARY_THRESHOLD,
    LLM_SUMMARIZATION_MODEL,
    LLM_MAX_RETRIES,
    LLM_BASE_DELAY
)
from database import DatabaseConnection, DatabaseError, execute_query

# Setup logging
logger = setup_logging(__name__)


def retry_with_backoff(max_retries: int = LLM_MAX_RETRIES, base_delay: float = LLM_BASE_DELAY):
    """Decorator for exponential backoff retry on API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

class ChatMemory:
    """
    Manages chat history persistence and summarization.
    """
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        
        # If user_id wasn't provided, try to fetch it from existing session
        if not self.user_id:
            row = execute_query("SELECT user_id FROM chat_sessions WHERE session_id = ?", (self.session_id,), fetch_one=True)
            if row and row['user_id']:
                self.user_id = row['user_id']
                
        self._ensure_session()
        
    def _ensure_session(self):
        """Ensure the session exists in the database."""
        try:
            # We use INSERT OR IGNORE so we don't overwrite if exists
            # But if we have a user_id now, we should ensure it's recorded?
            # Actually associate_user handles updates. This just ensures row existence.
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO chat_sessions (session_id, user_id) VALUES (?, ?)",
                    (self.session_id, self.user_id)
                )
                conn.commit()
        except DatabaseError as e:
            logger.error(f"Failed to ensure session: {e}")

    def associate_user(self, phone: str):
        """Link current session to a phone number (user_id)."""
        if not phone: return
        
        # Normalize phone if needed (stripping spaces etc is done by caller usually)
        self.user_id = phone
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                # Update current session
                cursor.execute(
                    "UPDATE chat_sessions SET user_id = ? WHERE session_id = ?",
                    (self.user_id, self.session_id)
                )
                conn.commit()
            logger.info(f"Associated session {self.session_id} with user {self.user_id}")
        except DatabaseError as e:
            logger.error(f"Failed to associate user: {e}")

    def save_message(self, role: str, content: str):
        """Save a new message to the database."""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
                    (self.session_id, role, content)
                )
                conn.commit()
        except DatabaseError as e:
            logger.error(f"Failed to save message: {e}")

    def get_recent_history(self, limit: int = MEMORY_BUFFER_SIZE) -> List[Dict[str, str]]:
        """Get the most recent N messages, prioritizing current session but falling back to user history."""
        try:
            # Strategies:
            # 1. Just current session (Simple, safe)
            # 2. Merged history of all sessions for this user (Complex, confusion risk)
            # Given we want "Context", getting the *very last* messages is most important.
            # If I just linked my account, I might want the LAST session's context? 
            # For now, let's stick to CURRENT session for "Recent History" to avoid disjointed chats.
            # BUT, for the Summary, we definitely want global context.
            
            rows = execute_query(
                """
                SELECT role, content 
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (self.session_id, limit)
            )
            # Reverse to get chronological order (oldest -> newest)
            return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        except DatabaseError as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def get_all_history(self) -> List[Dict[str, str]]:
        """Get full history for UI display (Current Session Only)."""
        # We generally only show the current session's chat log in the UI
        # Showing 5 year old messages might be confusing.
        try:
            rows = execute_query(
                "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (self.session_id,)
            )
            return [{"role": row["role"], "content": row["content"]} for row in rows]
        except DatabaseError as e:
            logger.error(f"Failed to get full history: {e}")
            return []

    def get_summary(self) -> Optional[str]:
        """Get the globally relevant summary for this user (or session)."""
        try:
            if self.user_id:
                # If identified, get the LATEST updated summary from ANY of their sessions
                # This is the "Primary Key" feature - linking history.
                query = """
                    SELECT summary FROM chat_summaries cs
                    JOIN chat_sessions s ON cs.session_id = s.session_id
                    WHERE s.user_id = ?
                    ORDER BY cs.last_updated DESC
                    LIMIT 1
                """
                row = execute_query(query, (self.user_id,), fetch_one=True)
                if row: return row["summary"]
            
            # Fallback to current session
            row = execute_query(
                "SELECT summary FROM chat_summaries WHERE session_id = ?",
                (self.session_id,),
                fetch_one=True
            )
            return row["summary"] if row else None
        except DatabaseError as e:
            logger.error(f"Failed to get summary: {e}")
            return None

    def update_summary(self, new_summary: str):
        """Update the conversation summary."""
        try:
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO chat_summaries (session_id, summary, last_updated) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(session_id) DO UPDATE SET 
                        summary = excluded.summary,
                        last_updated = CURRENT_TIMESTAMP
                    """,
                    (self.session_id, new_summary)
                )
                conn.commit()
        except DatabaseError as e:
            logger.error(f"Failed to update summary: {e}")

    def get_total_message_count(self) -> int:
        """Count total messages in session."""
        try:
            row = execute_query(
                "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?",
                (self.session_id,),
                fetch_one=True
            )
            return row["count"] if row else 0
        except DatabaseError as e:
            logger.error(f"Failed to count messages: {e}")
            return 0

    def generate_summary(self, model_api_key: str):
        """
        Generate a summary of older messages if threshold reached.
        Uses exponential backoff retry for API resilience.
        """
        count = self.get_total_message_count()
        
        # Only summarize when threshold is crossed (Fix #2)
        if count < MEMORY_SUMMARY_THRESHOLD:
            logger.debug(f"Skipping summarization: {count} < {MEMORY_SUMMARY_THRESHOLD} threshold")
            return
        
        if count <= MEMORY_BUFFER_SIZE:
            return

        current_summary = self.get_summary() or "No previous summary."
        limit = count - MEMORY_BUFFER_SIZE
        if limit <= 0: return

        try:
            rows = execute_query(
                """
                SELECT role, content 
                FROM chat_messages 
                WHERE session_id = ? 
                ORDER BY timestamp ASC 
                LIMIT ?
                """,
                (self.session_id, limit)
            )
            messages_to_summarize = [{"role": row["role"], "content": row["content"]} for row in rows]
        except DatabaseError: return

        if not messages_to_summarize: return

        # Call summarization with retry logic
        self._call_summarization_api(model_api_key, current_summary, messages_to_summarize)

    @retry_with_backoff()
    def _call_summarization_api(self, api_key: str, current_summary: str, messages: List[Dict]):
        """Call Gemini API for summarization with retry logic."""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(LLM_SUMMARIZATION_MODEL)
        
        prompt = f"""
        Summarize the following conversation history into a concise context for a chatbot. 
        Focus on user preferences, current order details, name, phone, and key questions asked.
        Ignore casual greetings if they don't add value.
        
        Previous User Summary:
        {current_summary}
        
        Recent Conversation (To be merged):
        {messages}
        
        New Summary:
        """
        
        response = model.generate_content(prompt)
        if response.text is None:
            raise ValueError("Empty response from Gemini summarization API")
        
        new_summary = response.text.strip()
        self.update_summary(new_summary)
        logger.info(f"Updated summary for session {self.session_id}")

    def build_context_window(self) -> List[Dict[str, str]]:
        """
        Construct the context window for the LLM.
        """
        context_messages = []
        
        # Add summary (Global user context if available)
        summary = self.get_summary()
        if summary:
            # We explicitly label this as "Long Term Memory"
            summary_msg = f"LONG TERM MEMORY (PREVIOUS CONVERSATIONS):\n{summary}\n\n(Use this to remember user context, orders, and name)"
            context_messages.append({"role": "user", "parts": [summary_msg]})
            context_messages.append({"role": "model", "parts": ["Understood. I have the context."]})
            
        # Add recent history (Current Session)
        recent = self.get_recent_history(MEMORY_BUFFER_SIZE)
        for msg in recent:
            role = "model" if msg["role"] == "assistant" else "user"
            context_messages.append({"role": role, "parts": [msg["content"]]})
            
        return context_messages
