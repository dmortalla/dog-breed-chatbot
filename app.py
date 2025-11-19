"""Streamlit app for the Dog Breed Matchmaker.

This app has two modes:

1. ⚡ Quick Match:
   - Use sidebar sliders to describe your lifestyle.
   - Get the top 3 matching dog breeds with photos and links.

2. 💬 Chatbot Mode:
   - Answer natural-language questions about your lifestyle.
   - A simple rule-based chatbot converts your answers into a profile.
   - Then it recommends the top 3 breeds.
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
# Data loading
# -------------------------------------------------------------------
@st.cache_data
def load_breed_data() -> pd.DataFrame:
    """Load the dog breed traits from CSV.

    Returns:
        DataFrame containing all dog breeds and their traits.
    """
    return pd.read_csv("data/breed_traits.csv")


# -------------------------------------------------------------------
# Helper: parse free-text level descriptions
# -------------------------------------------------------------------
def parse_level_answer(text: str) -> int:
    """Convert a free-text answer into a level from 1 to 5.

    Examples:
        "low"    -> 1
        "medium" -> 3
        "high"   -> 5
        "4"      -> 4

    Args:
        text: User-provided text.

    Returns:
        Integer value between 1 and 5.
    """
    if not text:
        return 3

    text = text.strip().lower()

    # If it starts with a digit, try to use that directly.
    if text[0].isdigit():
        try:
            value = int(text[0])
            return max(1, min(5, value))
        except ValueError:
            return 3

    if "low" in text:
        return 1
    if "high" in text:
        return 5
    if "medium" in text:
        return 3

    # Fallback / default
    return 3


# -------------------------------------------------------------------
# Quick Match: build user profile from sidebar sliders
# -------------------------------------------------------------------
def build_user_profile_from_sidebar() -> Dict[str, int]:
    """Collect user preferences from sidebar sliders for Quick Match.

    Returns:
        Dictionary mapping trait names to integer values in [1, 5].
    """
    st.sidebar.header("🐾 Your Lifestyle & Preferences")

    user_profile = {
        "Energy Level": st.sidebar.slider(
            "Your energy level (1 = couch potato, 5 = always active)",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Good With Young Children": st.sidebar.slider(
            "How important is being good with young children?",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Good With Other Dogs": st.sidebar.slider(
            "How important is being friendly with other dogs?",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Shedding Level": st.sidebar.slider(
            "Shedding tolerance (1 = almost no hair, 5 = fur everywhere)",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Barking Level": st.sidebar.slider(
            "Barking tolerance (1 = very quiet, 5 = okay with lots of barking)",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Openness To Strangers": st.sidebar.slider(
            "Preference for friendliness with strangers "
            "(1 = very reserved, 5 = very friendly)",
            min_value=1,
            max_value=5,
            value=3,
        ),
    }

    st.sidebar.caption(
        "Tip: 1 means “very low / not important”, 5 means “very high / very important”."
    )

    return user_profile


# -------------------------------------------------------------------
# Chatbot: build profile from free-text answers
# -------------------------------------------------------------------
def build_user_profile_from_chat(answers: Dict[str, str]) -> Dict[str, int]:
    """Create a user profile from chatbot answers.

    This is a hybrid (rule-based) approach:
    - It looks for words like "low", "medium", "high".
    - It looks for hints like "apartment", "small house" -> lower energy.
    - It looks for "kids", "children" -> higher child-friendliness.
    - It looks for "allergies", "allergic" -> low shedding.

    Args:
        answers: Dictionary with keys like "energy", "kids", "shed", etc.

    Returns:
        Dictionary mapping trait names to integer values in [1, 5].
    """
    energy_text = answers.get("energy", "")
    kids_text = answers.get("kids", "")
    dogs_text = answers.get("other_dogs", "")
    shed_text = answers.get("shedding", "")
    bark_text = answers.get("barking", "")
    stranger_text = answers.get("strangers", "")

    # Base values using simple parsing.
    energy_level = parse_level_answer(energy_text)
    shedding_level = parse_level_answer(shed_text)
    barking_level = parse_level_answer(bark_text)
    openness_level = parse_level_answer(stranger_text)

    # Kids / children
    kids_lower = kids_text.lower()
    if "no" in kids_lower:
        good_with_kids = 3
    elif any(word in kids_lower for word in ["baby", "child", "children", "kids"]):
        good_with_kids = 5
    else:
        good_with_kids = 3

    # Other dogs
    dogs_lower = dogs_text.lower()
    if "no" in dogs_lower:
        good_with_dogs = 3
    elif "yes" in dogs_lower or "have" in dogs_lower or "already" in dogs_lower:
        good_with_dogs = 5
    else:
        good_with_dogs = 3

    # Allergy / hair sensitivity: force low shedding if allergies mentioned.
    shed_lower = shed_text.lower()
    if any(word in shed_lower for word in ["allergy", "allergies", "allergic"]):
        shedding_level = 1

    profile: Dict[str, int] = {
        "Energy Level": energy_level,
        "Good With Young Children": good_with_kids,
        "Good With Other Dogs": good_with_dogs,
        "Shedding Level": shedding_level,
        "Barking Level": barking_level,
        "Openness To Strangers": openness_level,
    }

    return profile


# -------------------------------------------------------------------
# Display helper: breed card
# -------------------------------------------------------------------
def display_breed_card(rank: int, row: pd.Series) -> None:
    """Render a single result card for a breed.

    Args:
        rank: Rank (1, 2, 3) in the recommendation results.
        row: One row from the scored DataFrame.
    """
    breed = row["Breed"]
    score = float(row["score"])

    st.subheader(f"#{rank} — {breed}  (Match Score: {score:.1f} / 100)")

    # Image + dataset link
    image_url = get_breed_image_url(breed)
    folder_url = build_image_url(breed)
    st.image(image_url, width=320, caption=breed)
    st.markdown(
        f"[View more **{breed}** photos in the dataset]({folder_url})"
    )

    # Show a few key trait values (if present)
    bullets: List[str] = []

    def add_trait(col_name: str, label: str) -> None:
        if col_name in row and pd.notna(row[col_name]):
            bullets.append(f"- **{label}**: {int(row[col_name])} / 5")

    add_trait("Energy Level", "Energy level")
    add_trait("Good With Young Children", "Good with children")
    add_trait("Good With Other Dogs", "Good with other dogs")
    add_trait("Shedding Level", "Shedding level")
    add_trait("Barking Level", "Barking level")

    if bullets:
        st.markdown("**Why this breed might fit you:**")
        st.markdown("\n".join(bullets))

    st.markdown("---")


# -------------------------------------------------------------------
# Quick Match tab
# -------------------------------------------------------------------
def render_quick_match(clean_df: pd.DataFrame) -> None:
    """Render the Quick Match tab with sliders and result cards.

    Args:
        clean_df: Cleaned dog breed DataFrame with numeric trait columns.
    """
    st.subheader("⚡ Quick Match")

    st.write(
        "Use the sliders in the sidebar to describe your lifestyle and "
        "preferences. Then click the button to see your top 3 dog breeds."
    )

    user_profile = build_user_profile_from_sidebar()

    if st.button("✨ Show My Top 3 Breeds (Quick Match)", key="quick_match_button"):
        scored = compute_match_scores(clean_df, user_profile)
        top3 = scored.head(3)

        if top3.empty:
            st.warning("No breeds matched your filters. Try relaxing some preferences.")
        else:
            st.markdown("## 🎯 Your Top Matches")
            for rank, (_, row) in enumerate(top3.iterrows(), start=1):
                display_breed_card(rank, row)
    else:
        st.info("Set your preferences on the left and click the button to see results.")


# -------------------------------------------------------------------
# Chatbot Mode tab
# -------------------------------------------------------------------
def init_chat_state() -> None:
    """Initialize Streamlit session state for the chatbot."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_step" not in st.session_state:
        st.session_state.chat_step = 0
    if "chat_answers" not in st.session_state:
        st.session_state.chat_answers = {}


def render_chatbot(clean_df: pd.DataFrame) -> None:
    """Render the Chatbot Mode tab.

    This chatbot is rule-based and does not call any external API.
    It asks a fixed series of questions, stores the answers, and then
    recommends dog breeds based on the final profile.
    """
    st.subheader("💬 Chatbot Mode")

    init_chat_state()
    messages = st.session_state.chat_messages
    step = st.session_state.chat_step
    answers = st.session_state.chat_answers

    # Predefined question flow
    questions = [
        (
            "energy",
            "First, how would you describe your daily activity level? "
            "(low, medium, high)",
        ),
        (
            "kids",
            "Do you live with young children? "
            "You can answer like 'yes, 2 kids' or 'no children'.",
        ),
        (
            "other_dogs",
            "Do you already have other dogs at home? (yes or no, you can add details)",
        ),
        (
            "shedding",
            "How sensitive are you to dog hair and shedding? Any allergies?",
        ),
        (
            "barking",
            "How much barking can you tolerate? (low, medium, high)",
        ),
        (
            "strangers",
            "Do you prefer a dog that is very friendly with strangers, "
            "more reserved, or somewhere in between?",
        ),
    ]

    # Show existing messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # On first load, greet the user and ask the first question.
    if step == 0 and not messages:
        greeting = (
            "Hi! I'm your Dog Matchmaker chatbot 🐶.\n\n"
            "I'll ask a few quick questions about your lifestyle and then "
            "suggest dog breeds that match you."
        )
        first_question = questions[0][1]
        combined = f"{greeting}\n\n{first_question}"
        messages.append({"role": "assistant", "content": combined})
        with st.chat_message("assistant"):
            st.markdown(combined)

    # Get user input
    user_input = st.chat_input("Type your answer here...")

    if user_input:
        # Show user message
        with st.chat_message("user"):
            st.markdown(user_input)
        messages.append({"role": "user", "content": user_input})

        # Store answer for current step
        if step < len(questions):
            key = questions[step][0]
            answers[key] = user_input

        # Move to next step
        step += 1
        st.session_state.chat_step = step

        if step < len(questions):
            # Ask the next question
            _, next_q = questions[step]
            messages.append({"role": "assistant", "content": next_q})
            with st.chat_message("assistant"):
                st.markdown(next_q)
        else:
            # We have all answers: build profile and recommend breeds.
            profile = build_user_profile_from_chat(answers)
            scored = compute_match_scores(clean_df, profile)
            top3 = scored.head(3)

            if top3.empty:
                reply = (
                    "Thanks for your answers! I tried to match you, but I could not "
                    "find any breeds that fit these preferences. You can refresh the "
                    "page to try again with different answers."
                )
                messages.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)
            else:
                # Text summary in chat
                lines = [
                    "Thanks for your answers! Based on your lifestyle, here are "
                    "your top matches:",
                    "",
                ]
                for _, row in top3.iterrows():
                    breed = row["Breed"]
                    score = float(row["score"])
                    folder_url = build_image_url(breed)
                    lines.append(f"- **{breed}** — match score: **{score:.1f} / 100**")
                    lines.append(f"  [More photos]({folder_url})")

                summary = "\n".join(lines)
                messages.append({"role": "assistant", "content": summary})
                with st.chat_message("assistant"):
                    st.markdown(summary)

            st.info("Scroll up to review the conversation. Refresh the page to start over.")


# -------------------------------------------------------------------
# Main app
# -------------------------------------------------------------------
def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(
        page_title="Dog Breed Matchmaker",
        page_icon="🐕",
        layout="centered",
    )

    st.title("🐕 Dog Breed Matchmaker")
    st.write(
        "Use **Quick Match** for fast slider-based recommendations, or "
        "**Chatbot Mode** to answer questions in natural language."
    )

    # Load and clean data
    raw_df = load_breed_data()
    clean_df = clean_breed_traits(raw_df)

    # Two tabs: Quick Match and Chatbot Mode
    quick_tab, chat_tab = st.tabs(["⚡ Quick Match", "💬 Chatbot Mode"])

    with quick_tab:
        render_quick_match(clean_df)

    with chat_tab:
        render_chatbot(clean_df)


# -------------------------------------------------------------------
# Script entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
    
