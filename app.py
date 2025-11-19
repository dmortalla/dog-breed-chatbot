from __future__ import annotations

import random
import time
from typing import Dict, List, Tuple
from urllib.parse import quote

import streamlit as st

# Import your recommender engine exactly as your repo defines it
from recommender_engine import (
    extract_preferences,
    score_breeds,
    top_n_breeds,
    image_url_for_breed,
    folder_for_breed,
)

# Optional voice input
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
except Exception:
    HAS_MIC = False


# ============================================================
# Helper functions
# ============================================================

def apply_theme(theme: str) -> None:
    """Simple light/dark theme override."""
    if theme == "dark":
        css = """
        <style>
        body { background-color: #0f172a !important; color: #e5e7eb !important; }
        [data-testid="stSidebar"] { background-color: #020617 !important; }
        </style>
        """
    else:
        css = """
        <style>
        body { background-color: #ffffff !important; color: #111827 !important; }
        [data-testid="stSidebar"] { background-color: #f9fafb !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def dog_fact() -> str:
    """Random dog fact for fun."""
    facts = [
        "A dog’s nose print is unique — like a fingerprint!",
        "Some dogs can learn more than 1,000 words.",
        "Greyhounds can reach speeds up to 45 mph.",
        "The Basenji is known as the 'barkless dog.'",
        "Puppies are born blind and deaf, but develop quickly.",
    ]
    return random.choice(facts)


def is_off_topic(text: str) -> bool:
    """Detect messages that don’t relate to dog-matching."""
    keywords = [
        "energy", "active", "calm",
        "apartment", "yard", "house",
        "kids", "children", "family",
        "allergy", "hypoallergenic", "shedding",
        "train", "bark", "quiet",
    ]
    t = text.lower()
    return not any(k in t for k in keywords)


def summarize_preferences(prefs: Dict[str, int]) -> str:
    """Short English summary of what Dog Lover knows so far."""
    if not prefs:
        return "No preferences detected yet. Tell me about your home, allergies, kids, or energy level."

    parts = []

    # ENERGY
    if "energy" in prefs:
        if prefs["energy"] <= 2:
            parts.append("You prefer a calmer, low-energy dog.")
        elif prefs["energy"] == 3:
            parts.append("You’re okay with a medium-energy dog.")
        else:
            parts.append("You prefer a high-energy, active dog.")

    # HOME
    if "home" in prefs:
        if prefs["home"] <= 2:
            parts.append("You live in an apartment.")
        else:
            parts.append("You seem to have more space at home.")

    # ALLERGIES
    if "allergies" in prefs:
        if prefs["allergies"] <= 2:
            parts.append("Low-shedding or hypoallergenic coats matter to you.")
        else:
            parts.append("You’re flexible about shedding.")

    # KIDS
    if "kids" in prefs:
        if prefs["kids"] >= 4:
            parts.append("Being good with children is important.")
        else:
            parts.append("Kid-friendliness is less critical.")

    return " ".join(parts)


def render_breed_card(breed: str, score: float) -> None:
    """Display one breed recommendation with image and link."""
    st.markdown(f"### 🐕 {breed} — Match score: {score:.1f}/100")

    img_url = image_url_for_breed(breed)
    if img_url:
        st.image(img_url, width=320, caption=breed)

    folder = folder_for_breed(breed)
    gh_url = (
        "https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset/tree/master/"
        f"{quote(folder)}"
    )
    st.markdown(f"[📸 More photos of **{breed}** in the dataset]({gh_url})")
    st.markdown("---")


# ============================================================
# Streamlit page config
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot — Find Your Perfect Dog Breed",
    page_icon="🐶",
    layout="centered",
)


# ============================================================
# Session state storage
# ============================================================

state = st.session_state
state.setdefault("messages", [])
state.setdefault("preferences", {})
state.setdefault("step", 0)
state.setdefault("theme", "light")
state.setdefault("results", None)


# ============================================================
# Sidebar UI: Theme, Voice Input, Memory, Reset
# ============================================================

with st.sidebar:
    st.header("🎛️ Controls")

    # Theme toggle
    theme_choice = st.radio(
        "Theme",
        ["Light", "Dark"],
        index=0 if state.theme == "light" else 1,
    )
    state.theme = "light" if theme_choice == "Light" else "dark"

    st.markdown("---")

    # Voice input
    st.subheader("🎙️ Voice Input")
    if HAS_MIC:
        st.caption("Record a short message and I’ll treat it as chat input.")
        audio = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop",
            key="voice",
        )
        if isinstance(audio, dict) and audio.get("text"):
            voice_text = audio["text"]
            state.messages.append({"role": "user", "content": voice_text})
            st.rerun()
    else:
        st.caption("Install `streamlit-mic-recorder` to enable voice input.")

    st.markdown("---")

    # Reset conversation
    if st.button("🔄 Reset Conversation"):
        state.messages = []
        state.preferences = {}
        state.step = 0
        state.results = None
        st.rerun()

    st.markdown("---")

    # Memory summary
    st.subheader("🧠 What I Know So Far")
    st.write(summarize_preferences(state.preferences))

    st.markdown("---")

    # Collapsible chat history
    with st.expander("📜 Chat History"):
        if not state.messages:
            st.write("No messages yet.")
        else:
            for m in state.messages:
                role = "You" if m["role"] == "user" else "Dog Lover"
                st.markdown(f"**{role}:** {m['content']}")


# Apply theme AFTER reading sidebar state
apply_theme(state.theme)


# ============================================================
# Main Chat UI
# ============================================================

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.caption("Tell me about your lifestyle and preferences. I’ll match you with the best breed!")

# Initial greeting
if not state.messages:
    greeting = (
        "Hi there! I’m **Dog Lover**, your friendly dog-matching companion. 🐾\n\n"
        "Tell me a little about yourself — your home, your activity level, allergies, "
        "or whether you have kids — and I’ll ask a few follow-up questions to find the perfect breed."
    )
    state.messages.append({"role": "assistant", "content": greeting})

# Render past messages
for msg in state.messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.markdown(msg["content"])


# Chat input box
user_message = st.chat_input("Describe your lifestyle or dream dog…")


# ============================================================
# Chatbot Logic
# ============================================================

if user_message:
    state.messages.append({"role": "user", "content": user_message})

    # Off-topic message (but only after step 0)
    if is_off_topic(user_message) and state.step > 0:
        reply = (
            "I’m sorry, but that’s a bit outside what I can help with. "
            "Let’s get back to finding you the perfect dog! 🐾"
        )
        state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # Extract preferences
    new_prefs = extract_preferences(user_message)
    state.preferences.update({k: v for k, v in new_prefs.items() if v is not None})

    step = state.step

    # ===========================
    # Step 0 → Ask about energy
    # ===========================
    if step == 0:
        reply = (
            "Awesome! Let’s start with **energy level**.\n\n"
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 1
        st.rerun()

    # ===========================
    # Step 1 → Ask about home size
    # ===========================
    elif step == 1:
        reply = (
            "Great! Now let’s consider your **living situation**.\n\n"
            "Do you live in a **small apartment**, a **standard apartment**, "
            "or a **house with a yard**? 🏠"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 2
        st.rerun()

    # ===========================
    # Step 2 → Ask about allergies
    # ===========================
    elif step == 2:
        reply = (
            "Let’s now consider the issue of **allergies**.\n\n"
            "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 3
        st.rerun()

    # ===========================
    # Step 3 → Ask about kids
    # ===========================
    elif step == 3:
        reply = (
            "The presence of **children** could be a factor.\n\n"
            "Should your dog be especially **good with young children**? (yes or no) 👶🐶"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 4
        st.rerun()

    # ===========================
    # Step 4+ → Evaluate preferences
    # ===========================
    else:
        if len(state.preferences) >= 4:
            scores = score_breeds(state.preferences)
            state.results = top_n_breeds(scores, n=3)

            reply = (
                "Amazing — I think I have enough information now! 🐾✨\n\n"
                "Here are your **top dog breed matches**:"
            )
            state.messages.append({"role": "assistant", "content": reply})
        else:
            reply = (
                "I’m getting close! Tell me a bit more about your activity level, home, "
                "allergies, or whether you have kids, and I’ll refine the match."
            )
            state.messages.append({"role": "assistant", "content": reply})

        st.rerun()


# ============================================================
# Show final recommendations
# ============================================================

if state.results:
    st.markdown("## 🎯 Your Top Matches")
    for breed, score in state.results:
        render_breed_card(breed, score)

    st.markdown(f"**Bonus dog fact:** {dog_fact()}")

