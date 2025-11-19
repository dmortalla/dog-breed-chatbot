"""
Streamlit app for the Dog Breed Matchmaker.

This app has two modes:
- Quick Match: use the sidebar to set preferences and see visual cards
  with images and explanations.
- Chatbot Mode: chat in natural language and answer questions step-by-step
  to get recommendations.
"""

from typing import Dict, List

import streamlit as st
import pandas as pd

from recommender_engine import (
    clean_breed_traits,
    compute_match_scores,
    build_image_url,
    get_breed_image_url,
)
from chatbot_utils import parse_level_answer, describe_trait, load_data


def build_user_profile(
    energy: str,
    children: str,
    other_dogs: str,
    shedding_tolerance: str,
    barking: str,
    stranger: str,
) -> Dict[str, int]:
    """Build a simple user profile from sidebar answers.

    Args:
        energy: Text describing energy level (Low, Medium, High).
        children: "Yes" if user has young children, otherwise "No".
        other_dogs: "Yes" if user owns other dogs, otherwise "No".
        shedding_tolerance: Text on sensitivity to dog hair.
        barking: Text describing barking tolerance.
        stranger: Text describing friendliness to strangers.

    Returns:
        Dictionary mapping trait names to desired numeric levels (1–5).
    """
    profile: Dict[str, int] = {
        "Energy Level": parse_level_answer(energy),
        "Playfulness Level": parse_level_answer(energy),
        "Mental Stimulation Needs": parse_level_answer(energy),
        "Good With Young Children": 5 if children == "Yes" else 3,
        "Good With Other Dogs": 5 if other_dogs == "Yes" else 3,
        "Shedding Level": parse_level_answer(shedding_tolerance),
        "Barking Level": parse_level_answer(barking),
        "Openness To Strangers": parse_level_answer(stranger),
        # Reasonable defaults that work for many users.
        "Adaptability Level": 4,
        "Trainability Level": 4,
    }
    return profile


def build_user_profile_from_chat(answers: Dict[str, str]) -> Dict[str, int]:
    """Build a user profile from free-text chatbot answers.

    Args:
        answers: Dictionary with keys like "energy", "children", etc.
            Values are the raw user responses as strings.

    Returns:
        Dictionary mapping trait names to desired numeric levels (1–5).
    """
    energy = answers.get("energy", "medium")
    children_raw = answers.get("children", "no").strip().lower()
    other_dogs_raw = answers.get("other_dogs", "no").strip().lower()
    shedding = answers.get("shedding", "medium")
    barking = answers.get("barking", "medium")
    stranger = answers.get("stranger", "medium")

    children = "Yes" if "y" in children_raw else "No"
    other_dogs = "Yes" if "y" in other_dogs_raw else "No"

    return build_user_profile(
        energy=energy,
        children=children,
        other_dogs=other_dogs,
        shedding_tolerance=shedding,
        barking=barking,
        stranger=stranger,
    )


def render_quick_match(
    numeric_breeds: pd.DataFrame,
    trait_descriptions: pd.DataFrame,
) -> None:
    """Render the quick-match UI with sidebar controls and result cards.

    Args:
        numeric_breeds: Cleaned numeric dog breed DataFrame.
        trait_descriptions: DataFrame of trait explanations.
    """
    st.subheader("⚡ Quick Match (Sidebar Controls)")

    st.write(
        "Use the sidebar on the left to set your lifestyle and preferences, "
        "then click the button to see your top dog breed matches."
    )

    st.sidebar.header("Your Lifestyle & Preferences")

    energy = st.sidebar.selectbox(
        "Your daily activity level",
        ["Low", "Medium", "High"],
    )
    children = st.sidebar.selectbox(
        "Do you have young children?",
        ["No", "Yes"],
    )
    other_dogs = st.sidebar.selectbox(
        "Do you own other dogs?",
        ["No", "Yes"],
    )
    shedding_tolerance = st.sidebar.selectbox(
        "How sensitive are you to dog hair around the home?",
        ["Low", "Medium", "High"],
    )
    barking = st.sidebar.selectbox(
        "How much barking can you tolerate?",
        ["Low", "Medium", "High"],
    )
    stranger = st.sidebar.selectbox(
        "How friendly should your dog be with strangers?",
        ["Low", "Medium", "High"],
    )

    st.sidebar.write("---")

    if st.sidebar.button("Find My Top 3 Breeds! 🐾"):
        user_profile = build_user_profile(
            energy=energy,
            children=children,
            other_dogs=other_dogs,
            shedding_tolerance=shedding_tolerance,
            barking=barking,
            stranger=stranger,
        )

        results = compute_match_scores(numeric_breeds, user_profile)
        top3 = results.head(3)

        st.subheader("🎯 Your Top Matches (with photos)")

        traits_to_show: List[str] = [
            "Energy Level",
            "Playfulness Level",
            "Good With Young Children",
            "Good With Other Dogs",
            "Shedding Level",
            "Barking Level",
        ]

        for _, row in top3.iterrows():
            breed = row["Breed"]
            score = round(row["score"], 1)
            search_url = build_image_url(breed)
            image_url = get_breed_image_url(breed)

            cols = st.columns([1, 2])
            with cols[0]:
                st.image(
                    image_url,
                    caption=breed,
                    use_container_width=True,
                )

            with cols[1]:
                st.markdown(f"### **{breed}** — Match Score: **{score}/100**")
                st.markdown(f"[View more {breed} photos on dataset]({search_url})")

                descriptions: List[str] = []
                for trait in traits_to_show:
                    if trait in row.index:
                        descriptions.append(
                            describe_trait(trait_descriptions, trait, row[trait])
                        )

                st.write("**Why this breed could fit you:**")
                if descriptions:
                    st.write("• " + "\n• ".join(descriptions[:4]))
                else:
                    st.write("Trait information not available for this breed.")

            st.write("---")
    else:
        st.info(
            "Use the sidebar to enter your preferences, then click "
            "**Find My Top 3 Breeds! 🐾**"
        )


def render_chatbot(
    numeric_breeds: pd.DataFrame,
    trait_descriptions: pd.DataFrame,
) -> None:
    """Render a simple step-by-step chatbot experience.

    The chatbot asks a series of questions about the user's lifestyle.
    Answers are stored in session state and used to build a user profile.
    """
    st.subheader("💬 Chatbot Mode")

    # Initialize session state for chat, if missing.
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_step" not in st.session_state:
        st.session_state.chat_step = 0
    if "chat_answers" not in st.session_state:
        st.session_state.chat_answers = {}

    messages: List[Dict[str, str]] = st.session_state.chat_messages
    step: int = st.session_state.chat_step
    answers: Dict[str, str] = st.session_state.chat_answers

    # Pre-defined questions in order.
    questions = [
        (
            "energy",
            "First, how would you describe your daily activity level? "
            "(low, medium, high)",
        ),
        (
            "children",
            "Do you live with young children? (yes or no)",
        ),
        (
            "other_dogs",
            "Do you already have other dogs at home? (yes or no)",
        ),
        (
            "shedding",
            "How sensitive are you to dog hair and shedding? (low, medium, high)",
        ),
        (
            "barking",
            "How much barking can you tolerate? (low, medium, high)",
        ),
        (
            "stranger",
            "Do you prefer a dog that is very friendly with strangers, more "
            "reserved, or in between? (low, medium, high)",
        ),
    ]

    # Show existing chat history.
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # On first load, show greeting and first question.
    if step == 0 and not messages:
        greeting = (
            "Hi! I'm your Dog Matchmaker 🐶.\n\n"
            "I'll ask you a few quick questions about your lifestyle, and then "
            "I'll recommend dog breeds that match you."
        )
        first_question = questions[0][1]
        full_message = f"{greeting}\n\n{first_question}"
        messages.append({"role": "assistant", "content": full_message})
        with st.chat_message("assistant"):
            st.markdown(full_message)

    # Get user input.
    user_input = st.chat_input("Type your answer here...")

    if user_input:
        # Show user's message.
        with st.chat_message("user"):
            st.markdown(user_input)
        messages.append({"role": "user", "content": user_input})

        # Store the answer for the current step.
        if step < len(questions):
            key = questions[step][0]
            answers[key] = user_input

        # Move to the next step.
        st.session_state.chat_step += 1
        step = st.session_state.chat_step

        # If there are more questions, ask the next one.
        if step < len(questions):
            _, next_q = questions[step]
            messages.append({"role": "assistant", "content": next_q})
            with st.chat_message("assistant"):
                st.markdown(next_q)
        else:
            # We have all answers: build profile and recommend breeds.
            profile = build_user_profile_from_chat(answers)
            results = compute_match_scores(numeric_breeds, profile)
            top3 = results.head(3)

            # Build a simple text summary for the chat.
            lines = ["Here are your top matches based on your answers:\n"]
            for _, row in top3.iterrows():
                breed = row["Breed"]
                score = round(row["score"], 1)
                search_url = build_image_url(breed)
                lines.append(f"- **{breed}** — match score: **{score}/100**")
                lines.append(f"  [See photos]({search_url})")

            summary = "\n".join(lines)
            messages.append({"role": "assistant", "content": summary})
            with st.chat_message("assistant"):
                st.markdown(summary)

            st.info(
                "Scroll up to review the conversation, or refresh the page "
                "to start a new chat."
            )


def main() -> None:
    """Run the Streamlit web application."""
    st.set_page_config(
        page_title="Dog Breed Matchmaker",
        page_icon="🐶",
        layout="centered",
    )

    st.title("🐕 Dog Breed Matchmaker")
    st.write(
        "Use **Quick Match** for fast results with sliders, or **Chatbot Mode** "
        "to talk through your preferences step by step."
    )

    # Load data.
    dog_breeds, trait_descriptions = load_data()
    numeric_breeds = clean_breed_traits(dog_breeds)

    # Tabs for the two main modes.
    quick_tab, chat_tab = st.tabs(["⚡ Quick Match", "💬 Chatbot Mode"])

    with quick_tab:
        render_quick_match(numeric_breeds, trait_descriptions)

    with chat_tab:
        render_chatbot(numeric_breeds, trait_descriptions)


if __name__ == "__main__":
    main()
