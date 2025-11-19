# 🐶 Dog Breed Matchmaker – AI-Powered Chatbot
### Find the perfect dog breed based on your lifestyle, personality, and needs!

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_APP_URL_HERE)

---

## 🌟 Overview

The **Dog Breed Matchmaker** is a smart, Streamlit-based web app that helps users
discover dog breeds that best fit their lifestyle, family situation, activity
level, allergies, and more.

Using trait data for many breeds plus human-readable trait descriptions, the app
recommends the **top 3 matching breeds**—complete with links to images and short
explanations for each suggestion.

This project shows how to build a simple AI-style recommender with:
- Clean, beginner-friendly Python code.
- A web UI using Streamlit.
- Data-driven scoring logic using pandas.

---

## 🧠 Features

- **Interactive preference selection** in the sidebar.
- **Trait-based scoring** for:
  - Activity level
  - Shedding tolerance
  - Barking tolerance
  - Good with kids
  - Good with other dogs
  - Friendliness to strangers
  - Adaptability
  - Trainability
  - Mental stimulation needs
  - Playfulness
- **Top 3 breed recommendations** with:
  - Match score (0–100)
  - Clickable GitHub links to images
  - Simple textual explanations

---

## 📂 Project Structure

```text
dog-breed-chatbot/
│
├── app.py                    # Streamlit app entrypoint
├── recommender_engine.py     # Match scoring and image URL helpers
├── chatbot_utils.py          # Data loading and simple NLP utilities
├── README.md                 # Project documentation
├── requirements.txt          # Dependencies
└── data/
    ├── breed_traits.csv      # Dog breed trait data
    └── trait_description.csv # Trait explanations
```

---

## 🔧 Installation

### 1️⃣ Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/dog-breed-chatbot.git
cd dog-breed-chatbot
```

### 2️⃣ Create a virtual environment (optional but recommended)

```bash
python -m venv venv
# Mac / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run the App

From the project folder, run:

```bash
streamlit run app.py
```

Streamlit will open your browser at:

```text
http://localhost:8501
```

Then:

1. Use the left sidebar to set your preferences.
2. Click **“Find My Top 3 Breeds! 🐾”**.
3. Explore the recommended breeds and follow the image links.

---

## 🚀 Optional: Deploy to Streamlit Cloud

1. Push your project to GitHub.
2. Go to https://share.streamlit.io
3. Create a new app and point it to this repository.
4. Set:
   - Branch: `main`
   - File: `app.py`
5. Click **Deploy**.

Update the badge link at the top of this README with your live app URL.

---

## 🤝 Contributing

Pull requests and suggestions are welcome. Feel free to:
- Add more traits.
- Improve scoring logic.
- Enhance UI/UX in Streamlit.

---

## 📜 License

This project is open-source under the MIT License.
