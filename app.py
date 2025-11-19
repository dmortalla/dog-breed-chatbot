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

# ============================================================
#  IRRELEVANT MESSAGE DETECTION
# ============================================================
def is_irrelevant(message: str) -> bool:
    """
    Detects whether the message contains ANY meaningful dog-related
    preference traits. If not, it's considered irrelevant.

    Returns True = irrelevant.
    """
    text = message.lower()

    trait_keywords = [
        "energy", "active", "run", "jog", "walk",
        "kids", "children", "family",
        "apartment", "yard", "home",
        "allergy", "shedding", "hypoallergenic",
        "quiet", "barking",
        "train", "trainable", "easy to train",
        "affection", "cuddly", "independent",
        "calm", "relaxed", "chill",
    ]

    return not any(keyword in text for keyword in trait_keywords)


# ============================================================
#  TRAIT PARSING ENGINE
# ============================================================
def _level_from_words(text: str) -> int | None:
    text = text.lower()
    if "very low" in text:
        return 1
    if "low" in text:
        return 2
    if "medium" in text or "moderate" in text:
        return 3
    if "very high" in text:
        return 5
    if "high" in text:
        return 4
    return None


def infer_preferences_from_message(
    message: str, pending_key: str | None
) -> Tuple[Dict[str, int], Dict[str, float]]:
    text = message.lower()
    prefs = {}
    weights = {}

    # --- Pending trait handling first ---
    if pending_key is not None:
        lvl = _level_from_words(text)
        yes = any(w in text for w in ["yes", "yeah", "yep"])
        no = any(w in text for w in ["no", "nope"])

        if pending_key == "Energy Level" and lvl is not None:
            prefs["Energy Level"] = lvl
            weights["Energy Level"] = 1.0

        elif pending_key == "Shedding Level":
            if "hypoallergenic" in text or "allergy" in text:
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

        return prefs, weights

    # --------------------------------------------------------
    # GENERAL FREE-TEXT PARSING (no pending trait)
    # --------------------------------------------------------

    # Energy
    if any(k in text for k in ["very active", "marathon", "trail run"]):
        prefs["Energy Level"] = 5
        weights["Energy Level"] = 1.0
    elif any(k in text for k in ["active", "run", "jog", "hike"]):
        prefs["Energy Level"] = 4
        weights["Energy Level"] = 0.9
    elif "medium energy" in text:
        prefs["Energy Level"] = 3
        weights["Energy Level"] = 0.8
    elif any(k in text for k in ["low energy", "relaxed", "chill"]):
        prefs["Energy Level"] = 2
        weights["Energy Level"] = 0.9

    # Kids
    if any(k in text for k in ["kids", "children", "toddler", "baby"]):
        prefs["Good With Young Children"] = 5
        weights["Good With Young Children"] = 1.0

    # Allergies
    if any(k in text for k in ["allergy", "hypoallergenic", "allergic"]):
        prefs["Shedding Level"] = 1
        weights["Shedding Level"] = 1.0

    # Barking
    if any(k in text for k in ["quiet", "no barking"]):
        prefs["Barking Level"] = 2
        weights["Barking Level"] = 0.9

    # Trainability
    if any(k in text for k in ["easy to train", "first dog"]):
        prefs["Trainability Level"] = 5
        weights["Trainability Level"] = 0.9

    # Affection
    if any(k in text for k in ["cuddly", "affectionate"]):
        prefs["Affectionate With Family"] = 5
        weights["Affectionate With Family"] = 0.9

    # Space / Home
    if "apartment" in text:
        prefs["Energy Level"] = prefs.get("Energy Level", 3)  # nudging
        weights["Energy Level"] = max(weights.get("Energy Level", 0.8), 0.8)

    return prefs, weights


# ============================================================
#  FOLLOW-UP LOGIC
# ============================================================
FOLLOWUP_ORDER = [
    "Energy Level",
    "Shedding Level",
    "Good With Young Children",
    "Barking Level",
    "Trainability Level",
    "Affectionate With Family",
]

FOLLOWUP_QUESTIONS = {
    "Energy Level": "How energetic would you like your dog — low, medium, or high?",
    "Shedding Level": "Do you prefer low-shedding or hypoallergenic dogs?",
    "Good With Young Children": "Should your dog be good with young children? (yes/no)",
    "Barking Level": "How much barking is okay — low, medium, or high?",
    "Trainability Level": "How important is trainability — low, medium, or high?",
    "Affectionate With Family": "Would you like a very affectionate dog or a more independent one?",
}


def next_missing_trait(prefs: Dict[str, int]) -> str | None:
    for trait in FOLLOWUP_ORDER:
        if trait not in prefs:
            return trait
    return None


# ============================================================
#  UI HELPERS
# ============================================================
def render_breed_card(row, rank: int) -> None:
    breed = row["Breed"]
    score = row["score"]
    details = row["details"]

    st.markdown(f"### #{rank} — **{breed}** (match: {score:.1f}/100)")

    img = image_url_for_breed(breed)
    link = folder_url_for_breed(breed)

    if img:
        st.image(img, width=300)

    if link:
        st.markdown(f"[More photos of **{breed}** in the dataset]({link})")

    st.write("**Why this breed might fit you:**")
    for line in explain_match(details):
        st.markdown(line)

    st.markdown("---")


# ============================================================
#  MAIN APP
# ============================================================
def main():

    st.set_page_config(page_title="Dog Lover Chatbot", page_icon="🐶", layout="centered")

    # Load dataset
    if "traits_df" not in st.session_state:
        st.session_state.traits_df = load_breed_traits()

    df = st.session_state.traits_df

    # State
    state = st.session_state
    state.setdefault("chat", [])
    state.setdefault("prefs", {})
    state.setdefault("weights", {})
    state.setdefault("pending", None)
    state.setdefault("results", None)

    # Greeting
    if not state.chat:
        greeting = (
            "Hi there! I’m **Dog Lover** 🐾\n\n"
            "Tell me about your lifestyle and what kind of dog you'd love. "
            "I'll ask a few quick questions and then find your perfect match!"
        )
        state.chat.append(("assistant", greeting))

    # Show chat history
    for role, content in state.chat:
        with st.chat_message(role):
            st.markdown(content)

    # Input
    msg = st.chat_input("Tell me about your lifestyle or dog preferences...")
    if msg:
        # Show user
        state.chat.append(("user", msg))
        with st.chat_message("user"):
            st.markdown(msg)

        # Irrelevant message handling
        if is_irrelevant(msg) and state.pending is None:
            bot_reply = (
                "I'm sorry but that is beyond what I can do. "
                "Let's get back to choosing the best dog for you!"
            )
            state.chat.append(("assistant", bot_reply))
            with st.chat_message("assistant"):
                st.markdown(bot_reply)
            return

        # Parse message
        delta_prefs, delta_weights = infer_preferences_from_message(msg, state.pending)

        # Merge into stored prefs
        for k, v in delta_prefs.items():
            state.prefs[k] = v
        for k, w in delta_weights.items():
            state.weights[k] = max(state.weights.get(k, 0.7), w)

        # If this was a follow-up question, clear pending
        state.pending = None

        # DECISION: If fewer than 4 traits, only ask follow-up.
        if len(state.prefs) < 4:
            nxt = next_missing_trait(state.prefs)
            state.pending = nxt

            bot_msg = (
                f"Thanks! That helps a lot.\n\n"
                f"**One more quick question:** {FOLLOWUP_QUESTIONS[nxt]}"
            )
            state.chat.append(("assistant", bot_msg))
            with st.chat_message("assistant"):
                st.markdown(bot_msg)

            return  # ❗ EARLY RETURN — NO RECOMMENDATIONS YET

        # =====================================================
        # If we reach here → We have 4+ traits → recommend
        # =====================================================
        results = score_breeds(df, state.prefs, state.weights)
        top3 = results.head(3)
        state.results = top3

        bot_msg = (
            "Great! I think I have enough information to suggest some breeds.\n\n"
            "Here are your top matches:"
        )

        state.chat.append(("assistant", bot_msg))
        with st.chat_message("assistant"):
            st.markdown(bot_msg)

            for i, row in top3.iterrows():
                render_breed_card(row, rank=i + 1)


# Run
if __name__ == "__main__":
    main()
