"""
Dog Breed Chatbot — "Dog Lover"

This Streamlit app:

- Greets the user as a friendly chatbot called "Dog Lover".
- Lets the user chat in natural language about lifestyle and preferences.
- Extracts simple signals (energy, kids, allergies, noise, etc.) from text.
- Asks short follow-up questions only when needed to fill missing traits.
- Builds a preference profile on 1–5 trait scales.
- Uses the recommender engine to:
    * Restrict to breeds that have image folders in the GitHub dataset.
    * Score all valid breeds.
    * Recommend the top 3 breeds.
- Shows one photo per breed (Image_1.jpg variants) plus a link to the full dataset folder.

This version does not use any external AI APIs. It is fully deterministic and
runs on Streamlit Cloud as-is.
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
def _level_from_words(text: str) -> int | None:
    """Convert words like 'low', 'medium', 'high' into a 1–5 scale value.

    Args:
        text: User message in lowercase.

    Returns:
        Integer from 1 to 5, or None if no clear level is found.
    """
    if any(w in text for w in ["very low"]):
        return 1
    if any(w in text for w in ["low"]):
        return 2
    if any(w in text for w in ["medium", "moderate", "average"]):
        return 3
    if any(w in text for w in ["very high"]):
        return 5
    if any(w in text for w in ["high"]):
        return 4
    return None


def infer_preferences_from_message(
    message: str,
    pending_key: str | None = None,
) -> Tuple[Dict[str, int], Dict[str, float]]:
    """Infer trait preferences and weights from a chat message.

    This is a hybrid rules-based parser. It looks for keywords and phrases
    and maps them to traits like "Energy Level", "Shedding Level", etc.
    If there is a pending follow-up question (pending_key), it tries to
    interpret the message primarily as an answer to that question.

    Args:
        message: User message (any text).
        pending_key: Optional trait key we are currently asking about.

    Returns:
        (prefs_delta, weights_delta):
            prefs_delta:   trait -> preferred level (1–5)
            weights_delta: trait -> importance weight (0–1)
    """
    text = message.lower()
    prefs: Dict[str, int] = {}
    weights: Dict[str, float] = {}

    # If answering a specific follow-up, handle that first.
    if pending_key is not None:
        lvl = _level_from_words(text)
        yes = any(word in text for word in ["yes", "yeah", "yep", "of course"])
        no = any(word in text for word in ["no", "nope"])

        if pending_key == "Energy Level" and lvl is not None:
            prefs["Energy Level"] = lvl
            weights["Energy Level"] = 1.0
        elif pending_key == "Shedding Level":
            if "hypoallergenic" in text or "allergy" in text or "allergic" in text:
                prefs["Shedding Level"] = 1
                weights["Shedding Level"] = 1.0
            elif lvl is not None:
                prefs["Shedding Level"] = lvl
                weights["Shedding Level"] = 0.9
        elif pending_key == "Good With Young Children":
            if yes:
                prefs["Good With Young Children"] = 5
                weights["Good With Young Children"] = 1.0
            elif no:
                prefs["Good With Young Children"] = 3
                weights["Good With Young Children"] = 0.5
        elif pending_key == "Barking Level" and lvl is not None:
            prefs["Barking Level"] = lvl
            weights["Barking Level"] = 0.9
        elif pending_key == "Trainability Level" and lvl is not None:
            prefs["Trainability Level"] = lvl
            weights["Trainability Level"] = 0.8
        elif pending_key == "Affectionate With Family" and lvl is not None:
            prefs["Affectionate With Family"] = lvl
            weights["Affectionate With Family"] = 0.8

    # General free-text parsing (works even without pending question).
    # Energy / activity
    if any(k in text for k in ["very active", "marathon", "trail run", "high energy"]):
        prefs["Energy Level"] = 5
        weights["Energy Level"] = 1.0
    elif any(k in text for k in ["active", "jog", "run", "hike", "gym", "sporty"]):
        prefs["Energy Level"] = 4
        weights["Energy Level"] = max(weights.get("Energy Level", 0.0), 0.9)
    elif any(k in text for k in ["medium energy", "moderate energy"]):
        prefs["Energy Level"] = 3
        weights["Energy Level"] = max(weights.get("Energy Level", 0.0), 0.8)
    elif any(k in text for k in ["low energy", "couch", "relaxed", "chill"]):
        prefs["Energy Level"] = 2
        weights["Energy Level"] = max(weights.get("Energy Level", 0.0), 0.9)
    elif any(k in text for k in ["very calm", "really calm", "sedentary"]):
        prefs["Energy Level"] = 1
        weights["Energy Level"] = max(weights.get("Energy Level", 0.0), 1.0)

    # Children / family
    if any(k in text for k in ["kids", "children", "family", "toddler", "baby"]):
        prefs["Good With Young Children"] = 5
        weights["Good With Young Children"] = 1.0
    if "no kids" in text or "no children" in text:
        prefs["Good With Young Children"] = 3
        weights["Good With Young Children"] = max(
            weights.get("Good With Young Children", 0.0), 0.5
        )

    # Other dogs / social (we parse this but do not ask follow-ups for now)
    if any(k in text for k in ["other dog", "other dogs", "dog park", "play with dogs"]):
        prefs["Good With Other Dogs"] = 5
        weights["Good With Other Dogs"] = 0.8

    # Shedding / allergies
    if any(k in text for k in ["allergy", "allergies", "allergic", "hypoallergenic"]):
        prefs["Shedding Level"] = 1
        weights["Shedding Level"] = 1.0
    elif any(
        k in text
        for k in [
            "okay with shedding",
            "dont mind fur",
            "don't mind fur",
            "fur is fine",
        ]
    ):
        prefs["Shedding Level"] = 4
        weights["Shedding Level"] = max(weights.get("Shedding Level", 0.0), 0.7)

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
    if any(k in text for k in ["experienced owner", "had many dogs", "ive had many dogs"]):
        prefs["Trainability Level"] = 3
        weights["Trainability Level"] = max(
            weights.get("Trainability Level", 0.0), 0.5
        )

    # Affection / independence
    if any(k in text for k in ["very affectionate", "cuddly", "lap dog"]):
        prefs["Affectionate With Family"] = 5
        weights["Affectionate With Family"] = 0.9
    if any(k in text for k in ["independent", "not clingy", "more independent"]):
        prefs["Affectionate With Family"] = 3
        weights["Affectionate With Family"] = max(
            weights.get("Affectionate With Family", 0.0), 0.7
        )

    return prefs, weights


# -------------------------------------------------------------------
# Follow-up question logic
# -------------------------------------------------------------------
FOLLOWUP_ORDER = [
    "Energy Level",
    "Shedding Level",
    "Good With Young Children",
    "Barking Level",
    "Trainability Level",
    "Affectionate With Family",
]

FOLLOWUP_QUESTIONS = {
    "Energy Level": (
        "About how energetic would you like your dog to be — "
        "**low**, **medium**, or **high**?"
    ),
    "Shedding Level": (
        "Do you prefer a **low-shedding or hypoallergenic** dog, or is "
        "shedding okay (low/medium/high)?"
    ),
    "Good With Young Children": (
        "Do you have or expect to have **young children**, and should your dog "
        "be especially good with kids? (yes / no / doesn't matter)"
    ),
    "Barking Level": (
        "How much **barking** is okay in your home — **low**, **medium**, or **high**?"
    ),
    "Trainability Level": (
        "How important is it that your dog is **easy to train** — "
        "**low**, **medium**, or **high** importance?"
    ),
    "Affectionate With Family": (
        "Would you like a very **cuddly and affectionate** dog, or a more "
        "independent one (low/medium/high)?"
    ),
}


def choose_next_followup(prefs: Dict[str, int]) -> str | None:
    """Choose the next trait to ask about, based on what is missing.

    Args:
        prefs: Current preference dictionary.

    Returns:
        Trait label for follow-up question, or None if nothing to ask.
    """
    for trait in FOLLOWUP_ORDER:
        if trait not in prefs:
            return trait
    return None


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
    """Run the friendly 'Dog Lover' chatbot app."""
    st.set_page_config(
        page_title="Dog Lover — Dog Breed Chatbot",
        page_icon="🐕",
        layout="centered",
    )

    # Load traits once per session
    if "traits_df" not in st.session_state:
        st.session_state.traits_df = load_breed_traits()

    traits_df = st.session_state.traits_df

    # Initialize chat-related state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "prefs" not in st.session_state:
        st.session_state.prefs = {}
    if "weights" not in st.session_state:
        st.session_state.weights = {}
    if "last_results" not in st.session_state:
        st.session_state.last_results = None
    if "pending_trait" not in st.session_state:
        st.session_state.pending_trait = None

    # Friendly greeting from Dog Lover
    if not st.session_state.chat_history:
        greeting = (
            "Hi there! I am your chatbot **Dog Lover** 🐶 and I am here to help you "
            "pick your dream dog that matches your preferences and lifestyle.\n\n"
            "Just describe your life — your home, family, activity level, and any "
            "special wishes like low shedding or quiet — and I'll ask you for more "
            "details only when necessary."
        )
        st.session_state.chat_history.append(("assistant", greeting))

    st.title("🐕 Dog Lover — Dog Breed Matchmaker")
    st.write(
        "Chat with Dog Lover about your lifestyle and preferences, "
        "and get real dog breed suggestions with photos."
    )

    # Display chat history
    for speaker, text in st.session_state.chat_history:
        with st.chat_message(speaker):
            st.markdown(text)

    # Chat input
    user_message = st.chat_input("Tell Dog Lover about your lifestyle and dream dog...")
    if user_message:
        # Show user message
        st.session_state.chat_history.append(("user", user_message))
        with st.chat_message("user"):
            st.markdown(user_message)

        # Infer new prefs/weights from this message
        pending_trait = st.session_state.pending_trait
        delta_prefs, delta_weights = infer_preferences_from_message(
            user_message, pending_trait
        )

        # Merge into overall profile
        prefs = st.session_state.prefs
        weights = st.session_state.weights
        prefs.update(delta_prefs)
        for trait, w in delta_weights.items():
            weights[trait] = max(weights.get(trait, 0.6), w)

        st.session_state.prefs = prefs
        st.session_state.weights = weights

        # After answering a follow-up, clear it
        st.session_state.pending_trait = None

        # Decide if we should ask another follow-up
        # We only ask follow-ups while we have fewer than 4 core traits.
        next_trait = None
        if len(prefs) < 4:
            next_trait = choose_next_followup(prefs)
            st.session_state.pending_trait = next_trait

        # Compute recommendations
        results = score_breeds(traits_df, prefs, weights)
        top3 = results.head(3)
        st.session_state.last_results = top3

        # Build assistant summary
        if delta_prefs:
            described_traits = ", ".join(delta_prefs.keys())
            summary_intro = (
                f"Thanks, that helps a lot! I'll factor in: **{described_traits}**.\n\n"
            )
        else:
            summary_intro = (
                "Thanks for sharing! Even if I did not catch any new specific "
                "traits in that message, I am using everything you've told me so far."
                "\n\n"
            )

        if next_trait is None:
            summary_body = (
                "I think I have enough information to suggest some breeds for you. "
                "Here are your current top matches:"
            )
        else:
            question = FOLLOWUP_QUESTIONS.get(next_trait, "")
            summary_body = (
                "Here are your current top matches based on what I know so far. "
                "After that, I have one quick follow-up question for you:\n\n"
                f"> {question}"
            )

        assistant_text = summary_intro + summary_body

        st.session_state.chat_history.append(("assistant", assistant_text))
        with st.chat_message("assistant"):
            st.markdown(assistant_text)

        # Show cards under the assistant message
        if not top3.empty:
            for idx, row in top3.iterrows():
                render_breed_card(row, rank=idx + 1)
        else:
            st.write(
                "I couldn't find any matching breeds yet — try telling me a bit more "
                "about your home, activity level, kids, or allergy needs."
            )

    elif st.session_state.last_results is not None:
        # If no new message but we already have results, show them below the chat
        st.markdown("---")
        st.subheader("Current Top Matches")
        top3 = st.session_state.last_results
        for idx, row in top3.iterrows():
            render_breed_card(row, rank=idx + 1)


if __name__ == "__main__":
    main()

