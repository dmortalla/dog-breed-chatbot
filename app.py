from __future__ import annotations

from typing import Dict, Tuple
import random
import time

import streamlit as st

from recommender_engine import (
    load_breed_traits,
    score_breeds,
    image_url_for_breed,
    folder_url_for_breed,
    explain_match,
)

# Try to enable optional voice input if the package is available.
try:  # Optional dependency
    from streamlit_mic_recorder import mic_recorder  # type: ignore[import]
    HAS_MIC = True
except Exception:  # noqa: BLE001
    HAS_MIC = False


# ============================================================
#  DOG FACTS
# ============================================================
DOG_FACTS = [
    "Dogs have about 300 million scent receptors, compared to around 6 million in humans.",
    "A dog’s nose print is unique—just like a human fingerprint.",
    "Many dogs dream during sleep; you can sometimes see their paws twitching.",
    "Some breeds, like the Basenji, rarely bark but can yodel!",
    "Puppies are born deaf and blind, and develop senses as they grow.",
    "Dogs can understand hundreds of words and gestures with training.",
]


# ============================================================
#  IRRELEVANT MESSAGE DETECTION
# ============================================================
def is_irrelevant(message: str) -> bool:
    """Return True if the message does not look related to dog traits/lifestyle."""
    text = message.lower()

    trait_keywords = [
        "energy",
        "active",
        "run",
        "jog",
        "walk",
        "kids",
        "children",
        "family",
        "toddler",
        "baby",
        "apartment",
        "yard",
        "garden",
        "home",
        "house",
        "allergy",
        "shedding",
        "hypoallergenic",
        "fur",
        "quiet",
        "barking",
        "noise",
        "train",
        "trainable",
        "obedient",
        "affection",
        "cuddly",
        "lap dog",
        "independent",
        "calm",
        "relaxed",
        "chill",
        "guard dog",
        "watchdog",
        "protective",
    ]

    return not any(keyword in text for keyword in trait_keywords)


# ============================================================
#  TRAIT PARSING ENGINE
# ============================================================
def _level_from_words(text: str) -> int | None:
    """Map phrases like 'low/medium/high' to a 1–5 scale."""
    text = text.lower()
    if "very low" in text:
        return 1
    if "low" in text:
        return 2
    if "medium" in text or "moderate" in text or "average" in text:
        return 3
    if "very high" in text:
        return 5
    if "high" in text:
        return 4
    return None


def infer_preferences_from_message(
    message: str, pending_key: str | None
) -> Tuple[Dict[str, int], Dict[str, float]]:
    """Infer trait preferences and weights from a user message."""
    text = message.lower()
    prefs: Dict[str, int] = {}
    weights: Dict[str, float] = {}

    # ---------- Answering a pending follow-up question ----------
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

    # ---------- General free-text parsing (no pending trait) ----------
    # Energy
    if any(k in text for k in ["very active", "marathon", "trail run"]):
        prefs["Energy Level"] = 5
        weights["Energy Level"] = 1.0
    elif any(k in text for k in ["active", "run", "jog", "hike", "gym"]):
        prefs["Energy Level"] = 4
        weights["Energy Level"] = 0.9
    elif "medium energy" in text:
        prefs["Energy Level"] = 3
        weights["Energy Level"] = 0.8
    elif any(k in text for k in ["low energy", "relaxed", "chill", "couch"]):
        prefs["Energy Level"] = 2
        weights["Energy Level"] = 0.9

    # Kids / family
    if any(k in text for k in ["kids", "children", "toddler", "baby", "family"]):
        prefs["Good With Young Children"] = 5
        weights["Good With Young Children"] = 1.0

    # Allergies / shedding
    if any(k in text for k in ["allergy", "allergies", "hypoallergenic", "allergic"]):
        prefs["Shedding Level"] = 1
        weights["Shedding Level"] = 1.0

    # Barking / noise
    if any(k in text for k in ["quiet", "no barking", "noise sensitive"]):
        prefs["Barking Level"] = 2
        weights["Barking Level"] = 0.9

    # Trainability
    if any(k in text for k in ["easy to train", "first dog", "beginner"]):
        prefs["Trainability Level"] = 5
        weights["Trainability Level"] = 0.9

    # Affection
    if any(k in text for k in ["cuddly", "affectionate", "lap dog"]):
        prefs["Affectionate With Family"] = 5
        weights["Affectionate With Family"] = 0.9
    if any(k in text for k in ["independent", "not clingy"]):
        prefs["Affectionate With Family"] = 3
        weights["Affectionate With Family"] = 0.7

    # Space / home
    if "apartment" in text:
        prefs.setdefault("Energy Level", 3)
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
    "Energy Level": "How energetic would you like your dog — **low**, **medium**, or **high**?",
    "Shedding Level": "Do you prefer **low-shedding or hypoallergenic** dogs?",
    "Good With Young Children": "Should your dog be especially good with **young children**? (yes/no)",
    "Barking Level": "How much **barking** is okay — low, medium, or high?",
    "Trainability Level": "How important is **trainability** — low, medium, or high?",
    "Affectionate With Family": "Would you like a very **affectionate** dog or a more independent one (low/medium/high)?",
}


def next_missing_trait(prefs: Dict[str, int]) -> str | None:
    """Return the next trait we should ask about, or None if all covered."""
    for trait in FOLLOWUP_ORDER:
        if trait not in prefs:
            return trait
    return None


# ============================================================
#  UI HELPERS
# ============================================================
def typing_message(role: str, text: str, delay: float = 0.02) -> None:
    """Render a typing-style message for the given role."""
    with st.chat_message(role):
        placeholder = st.empty()
        displayed = ""
        words = text.split(" ")
        for i, word in enumerate(words):
            displayed += word + " "
            # Small cursor effect on last partial update
            if i < len(words) - 1:
                placeholder.markdown(displayed + "▌")
            else:
                placeholder.markdown(displayed)
            time.sleep(delay)


def render_breed_card(row, rank: int) -> None:
    """Display a single recommended breed card."""
    breed = row["Breed"]
    score = row["score"]
    details = row["details"]

    st.markdown(f"### #{rank} — **{breed}** (match score: {score:.1f}/100)")

    img_url = image_url_for_breed(breed)
    folder = folder_url_for_breed(breed)

    if img_url:
        st.image(img_url, width=320, caption=breed)

    if folder:
        st.markdown(f"[📸 More photos of **{breed}** in the dataset]({folder})")

    st.write("**Why this breed might fit you:**")
    for line in explain_match(details):
        st.markdown(line)

    st.markdown("---")


def summarize_prefs(prefs: Dict[str, int]) -> str:
    """Create a short natural-language summary of current preferences."""
    if not prefs:
        return "I don't know much yet. Tell me about your home, energy level, kids, or allergies!"

    parts = []

    energy = prefs.get("Energy Level")
    if energy:
        if energy <= 2:
            parts.append("You’d like a calmer, lower-energy dog.")
        elif energy == 3:
            parts.append("You’re okay with a medium-energy dog.")
        else:
            parts.append("You’d like a pretty active dog.")

    shed = prefs.get("Shedding Level")
    if shed:
        if shed <= 2:
            parts.append("Low shedding seems important to you.")
        elif shed >= 4:
            parts.append("You don’t mind a bit of shedding.")

    kids = prefs.get("Good With Young Children")
    if kids:
        if kids >= 4:
            parts.append("Being gentle with children matters.")
        else:
            parts.append("Kids aren’t a top concern.")

    bark = prefs.get("Barking Level")
    if bark:
        if bark <= 2:
            parts.append("You prefer a quieter dog.")
        elif bark >= 4:
            parts.append("You’re okay with a dog that’s more vocal.")

    train = prefs.get("Trainability Level")
    if train:
        if train >= 4:
            parts.append("You’d like a dog that’s easier to train.")
        else:
            parts.append("Trainability is less critical.")

    aff = prefs.get("Affectionate With Family")
    if aff:
        if aff >= 4:
            parts.append("You want a very affectionate, cuddly dog.")
        elif aff <= 2:
            parts.append("You’re okay with a more independent dog.")

    return " ".join(parts)


# ============================================================
#  MAIN APP
# ============================================================
def main() -> None:
    st.set_page_config(
        page_title="Dog Lover — Dog Breed Chatbot",
        page_icon="🐶",
        layout="centered",
    )

    # Load traits once
    if "traits_df" not in st.session_state:
        st.session_state.traits_df = load_breed_traits()

    df = st.session_state.traits_df

    # Conversation state
    state = st.session_state
    state.setdefault("chat", [])
    state.setdefault("prefs", {})
    state.setdefault("weights", {})
    state.setdefault("pending", None)
    state.setdefault("results", None)

    # ---------------- Sidebar: memory + controls + voice ----------------
    with st.sidebar:
        st.markdown("## 🧠 What I Know About You")
        st.write(summarize_prefs(state.prefs))

        if st.button("🔁 Reset conversation"):
            for key in ["chat", "prefs", "weights", "pending", "results"]:
                if key in state:
                    del state[key]
            st.experimental_rerun()

        st.markdown("---")
        st.markdown("### 🐕 Fun Dog Fact")
        st.write(random.choice(DOG_FACTS))

        st.markdown("---")
        st.markdown("### 🎙️ Optional Voice Input")
        if HAS_MIC:
            st.write("Click to record, then I’ll transcribe and use it as your message.")
            audio = mic_recorder(
                start_prompt="Start recording",
                stop_prompt="Stop",
                key="voice_input",
            )
            if audio and audio.get("text"):
                # This library can return a 'text' field with transcription
                state.setdefault("voice_queue", []).append(audio["text"])
                st.write("Captured voice input. Send it from the main chat box if needed.")
        else:
            st.caption(
                "Voice input is optional. To enable it, install `streamlit-mic-recorder` "
                "in your environment and redeploy the app."
            )

    # ---------------- Greeting ----------------
    if not state.chat:
        greeting = (
            "Hi there! I’m **Dog Lover** 🐾\n\n"
            "Tell me about your lifestyle and what kind of dog you’d love. "
            "I’ll ask a few quick questions and then find your best matches!"
        )
        state.chat.append(("assistant", greeting))

    st.title("🐾 Dog Lover — Dog Breed Matchmaker")
    st.write(
        "Describe your home, family, activity level, allergy needs, and personality preferences. "
        "Dog Lover will guide you and recommend real breeds with photos."
    )

    # Show chat history (no typing animation for past messages)
    for role, content in state.chat:
        with st.chat_message(role):
            st.markdown(content)

    # Main chat input
    message = st.chat_input("Tell Dog Lover about your lifestyle or dream dog...")

    if message:
        # Show user message
        state.chat.append(("user", message))
        with st.chat_message("user"):
            st.markdown(message)

        # Off-topic handling (only if not answering a pending question)
        if is_irrelevant(message) and state.pending is None:
            reply = (
                "I’m sorry but that is beyond what I can do. "
                "Let’s get back to how I can help you pick the best dog for you."
            )
            state.chat.append(("assistant", reply))
            typing_message("assistant", reply)
            return

        # Parse preferences
        delta_prefs, delta_weights = infer_preferences_from_message(
            message, state.pending
        )

        # Merge into state
        for k, v in delta_prefs.items():
            state.prefs[k] = v
        for k, w in delta_weights.items():
            state.weights[k] = max(state.weights.get(k, 0.7), w)

        # Clear pending trait (if we were asking a follow-up)
        state.pending = None

        # ---------- Decide whether to ask follow-up or recommend ----------
        MIN_TRAITS_FOR_RECOMMENDATION = 4

        if len(state.prefs) < MIN_TRAITS_FOR_RECOMMENDATION:
            nxt = next_missing_trait(state.prefs)
            state.pending = nxt

            bot_msg = (
                "Thanks! That helps a lot. 🐕\n\n"
                f"**One more quick question:** {FOLLOWUP_QUESTIONS[nxt]}"
            )
            state.chat.append(("assistant", bot_msg))
            typing_message("assistant", bot_msg)
            return  # No recommendations yet

        # ---------- We have enough info — recommend breeds ----------
        results = score_breeds(df, state.prefs, state.weights)
        top3 = results.head(3)
        state.results = top3

        intro = (
            "Awesome, I think I have enough information now. 🐶✨\n\n"
            "Here are your top dog breed matches based on everything you’ve told me:"
        )
        state.chat.append(("assistant", intro))
        typing_message("assistant", intro)

        with st.chat_message("assistant"):
            for i, row in top3.iterrows():
                render_breed_card(row, rank=i + 1)

            # Fun dog fact after recommendations
            st.markdown(
                f"**Bonus dog fact:** {random.choice(DOG_FACTS)}"
            )

    # If no new message but we already have results, show them below
    elif state.results is not None:
        st.markdown("---")
        st.subheader("🐶 Your Current Top Matches")
        for i, row in state.results.iterrows():
            render_breed_card(row, rank=i + 1)


if __name__ == "__main__":
    main()

