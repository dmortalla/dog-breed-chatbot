"""
Dog Breed Chatbot (Hybrid rule-based, serverless version).

This Streamlit app:

- Lets the user chat in natural language about lifestyle & preferences.
- Extracts simple signals (energy, kids, allergies, noise, etc.) using
  keyword-based rules (no external APIs required).
- Builds a preference profile on 1–5 trait scales.
- Uses the recommender engine to:
    * Restrict to breeds that have image folders in the GitHub dataset.
    * Score all valid breeds.
    * Recommend the top 3 breeds.
- Shows one photo per breed (1.jpg) plus a link to the full dataset folder.
"""

from __future__ import annotations

from typing import Dict, Tuple

import streamlit as st

from recommender_engine import (
    load_breed_traits,
    score_breeds,
    image_url_for_breed,
    folder_url_for_breed,
    explain_match,
)


# -------------------------------------------------------------------
# Preference parsing from chat
# -------------------------------------------------------------------
def infer_preferences_from_message(message: str) -> Tuple[Dict[str, int], Dict[str, float]]:
    """Infer trait preferences and weights from a single chat message.

    This is a hybrid rule-based parser. It looks for keywords and phrases
    and maps them to traits like "Energy Level", "Shedding Level", etc.

    Args:
        message: The user's chat message.

    Returns:
        (prefs_delta, weights_delta):
            prefs_delta:   trait -> preferred level (1–5)
            weights_delta: trait -> additional importance weight (0–1)
    """
    text = message.lower()
    prefs: Dict[str, int] = {}
    weights: Dict[str, float] = {}

    # Energy / activity
    if any(k in text for k in ["very active", "marathon", "trail run", "high energy"]):
        prefs["Energy Level"] = 5
        weights["Energy Level"] = 1.0
    elif any(k in text for k in ["active", "jog", "run", "hike", "gym"]):
        prefs["Energy Level"] = 4
        weights["Energy Level"] = 0.9
    elif any(k in text for k in ["medium energy", "moderate energy"]):
        prefs["Energy Level"] = 3
        weights["Energy Level"] = 0.8
    elif any(k in text for k in ["low energy", "couch", "relaxed", "apartment"]):
        prefs["Energy Level"] = 2
        weights["Energy Level"] = 0.9
    elif any(k in text for k in ["very calm", "really calm", "sedentary"]):
        prefs["Energy Level"] = 1
        weights["Energy Level"] = 1.0

    # Children / family
    if any(k in text for k in ["kids", "children", "family", "toddler", "baby"]):
        prefs["Good With Young Children"] = 5
        weights["Good With Young Children"] = 1.0
    if "no kids" in text or "no children" in text:
        prefs["Good With Young Children"] = 3
        weights["Good With Young Children"] = 0.5

    # Other dogs / social
    if any(k in text for k in ["other dog", "other dogs", "dog park", "play with dogs"]):
        prefs["Good With Other Dogs"] = 5
        weights["Good With Other Dogs"] = 0.9

    # Shedding / allergies
    if any(k in text for k in ["allergy", "allergies", "allergic", "hypoallergenic"]):
        prefs["Shedding Level"] = 1
        weights["Shedding Level"] = 1.0
    elif any(k in text for k in ["okay with shedding", "dont mind fur", "don't mind fur"]):
        prefs["Shedding Level"] = 4
        weights["Shedding Level"] = 0.7

    # Barking / noise
    if any(k in text for k in ["quiet", "noise sensitive", "thin walls", "no barking"]):
        prefs["Barking Level"] = 2
        weights["Barking Level"] = 0.9
    if any(k in text for k in ["guard dog", "watchdog", "protective"]):
        prefs["Watchdog/Protective Nature"] = 5
        weights["Watchdog/Protective Nature"] = 0.8

    # Trainability / experience
    if any(k in text for k in ["first dog", "new owner", "beginner"]):
        prefs["Trainability Level"] = 5
        weights["Trainability Level"] = 0.9
    if any(k in text for k in ["experienced owner", "i've had many dogs", "ive had many dogs"]):
        prefs["Trainability Level"] = 3
        weights["Trainability Level"] = 0.5

    # Affection / independence
    if any(k in text for k in ["very affectionate", "cuddly", "lap dog"]):
        prefs["Affectionate With Family"] = 5
        weights["Affectionate With Family"] = 0.9
    if any(k in text for k in ["independent", "not clingy", "more independent"]):
        prefs["Affectionate With Family"] = 3
        weights["Affectionate With Family"] = 0.7

    return prefs, weights


# -------------------------------------------------------------------
# Display helper
# -------------------------------------------------------------------
def render_breed_card(breed_row, rank: int) -> None:
    """Render a single recommendation card in the chat output area."""
    breed_name = breed_row["Breed"]
    score = breed_row["score"]
    details = breed_row["details"]

    img_url = image_url_for_breed(breed_name)
    folder_url = folder_url_for_breed(breed_name)

    st.markdown(f"### #{rank} — **{breed_name}** (match score: {score:.1f}/100)")
    if img_url:
        st.image(img_url, width=300, caption=breed_name)
    if folder_url:
        st.markdown(f"[More photos of **{breed_name}** in the dataset]({folder_url})")

    st.write("**Why this breed might fit you:**")
    for line in explain_match(details):
        st.markdown(line)
    st.markdown("---")


# -------------------------------------------------------------------
# Main app
# -------------------------------------------------------------------
def main() -> None:
    """Run the hybrid chatbot app."""
    st.set_page_config(page_title="Dog Breed Chatbot", page_icon="🐕", layout="centered")

    st.title("🐕 Dog Breed Matchmaker Chatbot")
    st.write(
        "Tell me about your lifestyle, space, family, and preferences, "
        "and I'll recommend real dog breeds that could fit you."
    )

    # Load traits once per session
    if "traits_df" not in st.session_state:
        st.session_state.traits_df = load_breed_traits()

    traits_df = st.session_state.traits_df

    # Initialize chat state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "prefs" not in st.session_state:
        st.session_state.prefs = {}
    if "weights" not in st.session_state:
        st.session_state.weights = {}
    if "last_results" not in st.session_state:
        st.session_state.last_results = None

    # Display history
    for speaker, text in st.session_state.chat_history:
        with st.chat_message(speaker):
            st.markdown(text)

    # First assistant message
    if not st.session_state.chat_history:
        intro = (
            "Hi! I'm your dog breed matchmaker 🐶\n\n"
            "Tell me things like:\n"
            "- *\"I live in an apartment and work from home.\"*\n"
            "- *\"We have two young kids and want a friendly dog.\"*\n"
            "- *\"I have allergies and prefer a low-shedding dog.\"*\n\n"
            "You can send multiple messages; I'll update your profile as we chat."
        )
        st.session_state.chat_history.append(("assistant", intro))
        with st.chat_message("assistant"):
            st.markdown(intro)

    # Chat input
    user_message = st.chat_input("Describe your lifestyle and dream dog...")
    if user_message:
        # Show user message
        st.session_state.chat_history.append(("user", user_message))
        with st.chat_message("user"):
            st.markdown(user_message)

        # Infer new prefs/weights from this message
        delta_prefs, delta_weights = infer_preferences_from_message(user_message)

        # Merge into overall profile
        prefs = st.session_state.prefs
        weights = st.session_state.weights
        prefs.update(delta_prefs)
        for trait, w in delta_weights.items():
            weights[trait] = max(weights.get(trait, 0.6), w)

        st.session_state.prefs = prefs
        st.session_state.weights = weights

        # Compute recommendations
        results = score_breeds(traits_df, prefs, weights)
        top3 = results.head(3)
        st.session_state.last_results = top3

        # Build assistant summary
        if not delta_prefs:
            summary = (
                "Thanks! I didn't detect any new specific preferences from that, "
                "but I'll keep it in mind. Here's how your matches look right now:"
            )
        else:
            described_traits = ", ".join(delta_prefs.keys())
            summary = (
                f"Got it — I'll factor in: **{described_traits}**.\n\n"
                "Based on everything you've told me so far, here are your "
                "current top matches:"
            )

        st.session_state.chat_history.append(("assistant", summary))
        with st.chat_message("assistant"):
            st.markdown(summary)

        # Show cards under the assistant message
        if not top3.empty:
            for idx, row in top3.iterrows():
                render_breed_card(row, rank=idx + 1)
        else:
            st.write("I couldn't find any matching breeds yet — try adding more details.")

    # If there are existing results and the user hasn't just sent a message,
    # show the current top matches under the chat.
    elif st.session_state.last_results is not None:
        st.markdown("---")
        st.subheader("Current Top Matches")
        top3 = st.session_state.last_results
        for idx, row in top3.iterrows():
            render_breed_card(row, rank=idx + 1)


if __name__ == "__main__":
    main()
