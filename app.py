"""Streamlit app for the Dog Breed Matchmaker.

This app has two modes:

1. ⚡ Quick Match:
   - Uses easy dropdowns to describe your lifestyle.
   - Recommends top 3 dog breeds with photos + dataset links.

2. 💬 Chatbot Mode:
   - Rule-based natural-language chatbot.
   - Asks questions and builds a profile from conversation.
"""

from typing import Dict, List

import pandas as pd
import streamlit as st

from recommender_engine import (
    clean_breed_traits,
    compute_match_scores,
    get_breed_image_url,
    build_image_url,
)


# -------------------------------------------------------------------
# Load Data
# -------------------------------------------------------------------
@st.cache_data
def load_breed_data() -> pd.DataFrame:
    """Load dog breed traits from CSV."""
    return pd.read_csv("data/breed_traits.csv")


# -------------------------------------------------------------------
# Dropdown Utility
# -------------------------------------------------------------------
def dropdown(label: str) -> int:
    """Convert a human-friendly dropdown option into an integer (1–5)."""
    options = {
        "Very Low (1)": 1,
        "Low (2)": 2,
        "Medium (3)": 3,
        "High (4)": 4,
        "Very High (5)": 5,
    }
    choice = st.sidebar.selectbox(label, list(options.keys()))
    return options[choice]


# -------------------------------------------------------------------
# QUICK MATCH (Dropdown Version)
# -------------------------------------------------------------------
def build_user_profile_from_sidebar() -> Dict[str, int]:
    """Use dropdowns instead of sliders for Quick Match."""

    st.sidebar.header("🐾 Your Lifestyle & Preferences")

    user_profile = {
        "Energy Level": dropdown("Your activity level:"),
        "Good With Young Children": dropdown("Good with young children:"),
        "Good With Other Dogs": dropdown("Friendly with other dogs:"),
        "Shedding Level": dropdown("Shedding tolerance:"),
        "Barking Level": dropdown("Barking tolerance:"),
        "Openness To Strangers": dropdown("Friendliness with strangers:"),
    }

    return user_profile


# -------------------------------------------------------------------
# Chatbot Helpers
# -------------------------------------------------------------------
def parse_level_answer(text: str) -> int:
    """Convert free-text description to 1–5."""
    if not text:
        return 3

    text = text.lower()

    if text[0].isdigit():
        num = int(text[0])
        return max(1, min(5, num))

    if "very low" in text:
        return 1
    if "low" in text:
        return 2
    if "medium" in text:
        return 3
    if "high" in text:
        return 4
    if "very high" in text:
        return 5

    return 3


def build_user_profile_from_chat(answers: Dict[str, str]) -> Dict[str, int]:
    """Infer profile values from natural language chatbot responses."""
    return {
        "Energy Level": parse_level_answer(answers.get("energy", "")),
        "Good With Young Children": (
            5 if "kid" in answers.get("kids", "").lower() else 3
        ),
        "Good With Other Dogs": (
            5 if "yes" in answers.get("other_dogs", "").lower() else 3
        ),
        "Shedding Level": (
            1 if "allerg" in answers.get("shedding", "").lower() else parse_level_answer(answers.get("shedding", ""))
        ),
        "Barking Level": parse_level_answer(answers.get("barking", "")),
        "Openness To Strangers": parse_level_answer(answers.get("strangers", "")),
    }


# -------------------------------------------------------------------
# Display Breed Recommendation Card
# -------------------------------------------------------------------
def display_breed_card(rank: int, row: pd.Series) -> None:
    """Render a nicely formatted breed card."""
    breed = row["Breed"]
    score = float(row["score"])

    st.subheader(f"#{rank} — {breed}  (Match Score: {score:.1f})")

    image_url = get_breed_image_url(breed)
    folder_url = build_image_url(breed)

    st.image(image_url, width=320, caption=breed)
    st.markdown(f"[View more **{breed}** photos in dataset]({folder_url})")

    traits_to_show = [
        ("Energy Level", "Energy Level"),
        ("Good With Young Children", "Good with Children"),
        ("Good With Other Dogs", "Good with Other Dogs"),
        ("Shedding Level", "Shedding Level"),
        ("Barking Level", "Barking Level"),
    ]

    st.write("**Why this breed might fit you:**")
    bullets = []
    for col, label in traits_to_show:
        if col in row and not pd.isna(row[col]):
            bullets.append(f"- **{label}**: {int(row[col])}/5")

    st.markdown("\n".join(bullets))
    st.markdown("---")


# -------------------------------------------------------------------
# QUICK MATCH TAB
# -------------------------------------------------------------------
def render_quick_match(clean_df: pd.DataFrame) -> None:
    st.subheader("⚡ Quick Match")

    st.write("Select your preferences on the left and click the button.")

    profile = build_user_profile_from_sidebar()

    if st.button("✨ Show My Top 3 Breeds", key="quick_btn"):
        results = compute_match_scores(clean_df, profile)
        top3 = results.head(3)

        st.markdown("## 🎯 Your Top Matches")
        for i, (_, row) in enumerate(top3.iterrows(), start=1):
            display_breed_card(i, row)
    else:
        st.info("Adjust dropdowns on the left and click the button to see results.")


# -------------------------------------------------------------------
# CHATBOT MODE
# -------------------------------------------------------------------
def init_chat_state():
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_step" not in st.session_state:
        st.session_state.chat_step = 0
    if "chat_answers" not in st.session_state:
        st.session_state.chat_answers = {}


def render_chatbot(clean_df: pd.DataFrame) -> None:
    st.subheader("💬 Chatbot Mode")

    init_chat_state()
    msgs = st.session_state.chat_messages
    step = st.session_state.chat_step
    ans = st.session_state.chat_answers

    questions = [
        ("energy", "How would you describe your daily activity level? (low/medium/high)"),
        ("kids", "Do you live with young children?"),
        ("other_dogs", "Do you have other dogs at home?"),
        ("shedding", "How do you feel about shedding? Any allergies?"),
        ("barking", "How much barking can you tolerate?"),
        ("strangers", "Do you prefer a friendly or reserved dog with strangers?"),
    ]

    # Display existing messages
    for m in msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Greeting
    if step == 0 and not msgs:
        greet = (
            "Hello! I'm your Dog Matchmaker chatbot 🐾\n\n"
            "I'll ask you a few questions to help find the perfect dog breed."
        )
        msgs.append({"role": "assistant", "content": greet})
        with st.chat_message("assistant"):
            st.markdown(greet)

        # Ask first question
        msgs.append({"role": "assistant", "content": questions[0][1]})
        with st.chat_message("assistant"):
            st.markdown(questions[0][1])

    user_input = st.chat_input("Type your answer...")

    if user_input:
        msgs.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Save answer
        if step < len(questions):
            key = questions[step][0]
            ans[key] = user_input

        step += 1
        st.session_state.chat_step = step

        if step < len(questions):
            next_q = questions[step][1]
            msgs.append({"role": "assistant", "content": next_q})
            with st.chat_message("assistant"):
                st.markdown(next_q)
        else:
            profile = build_user_profile_from_chat(ans)
            results = compute_match_scores(clean_df, profile)
            top3 = results.head(3)

            summary = "Here are your best matches:\n\n"
            for _, row in top3.iterrows():
                breed = row["Breed"]
                score = float(row["score"])
                url = build_image_url(breed)
                summary += f"- **{breed}** — {score:.1f}\n  [Photos]({url})\n"

            msgs.append({"role": "assistant", "content": summary})
            with st.chat_message("assistant"):
                st.markdown(summary)

            st.info("Refresh the page to restart the chat.")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Dog Breed Matchmaker",
        page_icon="🐕",
        layout="centered",
    )

    st.title("🐕 Dog Breed Matchmaker")
    st.write(
        "Use **Quick Match** for fast dropdown-based recommendations, or "
        "**Chatbot Mode** for natural conversation."
    )

    raw_df = load_breed_data()
    clean_df = clean_breed_traits(raw_df)

    quick_tab, chat_tab = st.tabs(["⚡ Quick Match", "💬 Chatbot Mode"])

    with quick_tab:
        render_quick_match(clean_df)

    with chat_tab:
        render_chatbot(clean_df)


if __name__ == "__main__":
    main()

