# 🍕 Broadway Pizza Chatbot

A smart, AI-powered customer service chatbot for **Broadway Pizza Pakistan**. This application uses **Google Gemini (Generative AI)** to provide natural, helpful responses and **RAG (Retrieval-Augmented Generation)** to fetch real-time data from a local SQLite database, ensuring customers get accurate information about menus, deals, and restaurant services.

---

## ✨ Features

- **🤖 AI-Powered Conversations:** Powered by Google's Gemini Flash model for natural, friendly assistance.
- **📚 RAG Architecture:** Queries a local SQLite database for factual grounding—no hallucinations about menu items or prices!
- **🍕 Comprehensive Menu Knowledge:** Knows details about:
  - Pizzas (Royale, Specialty, King Crust)
  - Sides (Wings, Garlic Bread, Calzones)
  - Deals & Combos
  - Dips, Sauces & Crust Options
- **🛒 Interactive Cart System:**
  - Add items to cart naturally ("I want a large Peperoni Pizza")
  - View cart summary
  - Clear cart
  - Calculate totals automatically
- **📝 Order Placement:** Collects customer details (Name, Phone) and saves confirmed orders to the database.
- **🏨 Restaurant Info:** Provides details on locations, services (Dine-in, Delivery, etc.), and payment methods.

---

## 🛠️ Tech Stack

- **Frontend:** [Streamlit](https://streamlit.io/) (Python Web Framework)
- **AI Model:** [Google Gemini API](https://ai.google.dev/) (`gemini-flash-latest`)
- **Database:** SQLite (Lightweight, serverless relational DB)
- **Language:** Python 3.8+

---

## 🚀 Setup & Installation

Follow these steps to get the chatbot running locally on your machine.

### 1. Prerequisites
- Python 3.8 or higher installed.
- A **Google API Key** for Gemini. You can get one [here](https://aistudio.google.com/app/apikey).

### 2. Clone the Repository
```bash
git clone <repository-url>
cd ChatBot
```
*(Or simply navigate to the project directory if you have the files locally)*

### 3. Create a Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
Install the required Python packages using `pip`:
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
1. Create a new file named `.env` in the root directory.
2. Add your Google API Key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### 6. Initialize the Database
Run the setup script to create the database and seed it with the menu data:
```bash
python setup_db.py
```
*You should see a success message indicating the tables have been created and data seeded.*

---

## ▶️ Usage

### Run the Application
Start the Streamlit app:
```bash
streamlit run app.py
```

### Interact with the Chatbot
- **Browse:** "Show me the menu", "What specialty pizzas do you have?"
- **Deals:** "Any ongoing deals?", "Tell me about the My Box deal."
- **Order:** "I want a small Wicked Blend pizza", "Add a Garlic Mayo dip."
- **Checkout:** "I'm done", "Place order", "Checkout".
- **Info:** "What payment methods do you accept?", "Do you deliver?"

---

## 📂 Project Structure

```
ChatBot/
│
├── app.py                # Main Streamlit application file (Chatbot Logic + UI)
├── setup_db.py           # Database setup script (Schema + Seed Data)
├── broadway_pizza.db     # SQLite Database (Created after running setup_db.py)
├── requirements.txt      # List of Python dependencies
├── .env                  # Environment variables (API Key) - Keep confidential!
└── README.md             # Project documentation
```

---

## ❓ Troubleshooting

**Q: I see a "GOOGLE_API_KEY not found" error.**
A: Make sure you created the `.env` file in the same directory as `app.py` and pasted your valid API Key inside it.

**Q: The bot says "Restaurant information not available."**
A: You likely haven't run the database setup script. Run `python setup_db.py` to populate the database.

**Q: How do I view the orders?**
A: Orders are saved in the `orders` table of `broadway_pizza.db`. You can view them using any SQLite viewer or by adding a simple admin page to `app.py`.

---

## 🌐 Deployment on Streamlit Cloud

1.  **Push to GitHub:**
    - Create a repository on GitHub.
    - Push your code (including `requirements.txt` and `setup_db.py`).
    - *Note: `broadway_pizza.db` and `.env` are git-ignored and won't be pushed.*

2.  **Deploy:**
    - Go to [share.streamlit.io](https://share.streamlit.io/).
    - Click "New App".
    - Select your GitHub repository, branch, and `app.py`.

3.  **Configure Secrets:**
    - In your deployed app's settings, go to **Secrets**.
    - Add your API key like this:
      ```toml
      GOOGLE_API_KEY = "your_actual_api_key_here"
      ```

4.  **Launch!**
    - The app will automatically initialize the database on the first run.

---

## 📜 License
This project is for educational and portfolio purposes.
