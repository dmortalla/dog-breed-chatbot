from __future__ import annotations

import random
import time
from typing import Dict, List, Tuple
from urllib.parse import quote

import streamlit as st

from recommender_engine import (
    extract_preferences,
    score_breeds,
    top_n_breeds,
    image_url_for_breed,
    folder_for_breed,
)

# Optional voice input
try:
    from streamlit_mic_recorder import mic_recorder  # type: ignore[import]
    HAS_MIC = True
except Exception:
    HAS_MIC = False


# ============================================================
# Helper functions
# ============================================================

def apply_theme(theme: str) -> None:
    """Inject simple CSS for light / dark theme."""
    if theme == "dark":
        css = """
        <style>
        body { background-color: #0f172a; color: #e5e7eb; }
        [data-testid="stSidebar"] { background-color: #020617; }
        </style>
        """
    else:
        css = """
        <style>
        body { background-color: #ffffff; color: #111827; }
        [data-testid="stSidebar"] { background-color: #f9fafb; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def dog_fact() -> str:
    facts = [
        "A dog’s nose print is unique — just like a human fingerprint.",
        "Dogs can understand over 150 words and gestures.",
        "Some dogs can learn more than 1,000 words!",
        "The Basenji is known as the 'barkless dog.'",
        "A Greyhound can reach speeds up to 45 mph.",
        "Puppies are born deaf and blind but develop quickly.",
    ]
    return random.choice(facts)


def is_off_topic(text: str) -> bool:
    """Very simple filter to nudge user back to the dog-matching task."""
    keywords = [
        "energy", "active", "calm",
        "apartment", "yard", "house",
        "kids", "children", "family",
        "allergy", "allergies", "hypoallergenic", "shedding",
        "train", "trainable", "bark", "quiet",
    ]
    t = text.lower()
    return not any(k in t for k in keywords)


def summarize_preferences(prefs: Dict[str, int]) -> str:
    """Short natural-language summary of what Dog Lover knows so far."""
    if not prefs:
        return "I don’t know much yet. Tell me about your energy level, home, allergies, or kids."

    parts: List[str] = []

    energy = prefs.get("energy")
    if energy is not None:
        if energy <= 2:
            parts.append("You prefer a calmer, lower-energy dog.")
        elif energy == 3:
            parts.append("You’re okay with a medium-energy dog.")
        else:
            parts.append("You’d like a high-energy, active dog.")

    home = prefs.get("home")
    if home is not None:
        if home <= 2:
            parts.append("You mentioned living in an apartment.")
        else:
            parts.append("You seem to have more space, like a house with a yard.")

    allergies = prefs.get("allergies")
    if allergies is not None:
        if allergies <= 2:
            parts.append("Low shedding or hypoallergenic coats matter to you.")
        else:
            parts.append("You’re flexible about shedding.")

    kids = prefs.get("kids")
    if kids is not None:
        if kids >= 4:
            parts.append("Being good with young children is important.")
        else:
            parts.append("Kid-friendliness is less critical.")

    return " ".join(parts)


def render_breed_card(breed: str, score: float) -> None:
    """Display one breed recommendation with image and optional link."""
    st.markdown(f"### 🐕 {breed} — Match score: {score:.1f}/100")

    img_url = image_url_for_breed(breed)
    if img_url:
        st.image(img_url, width=320, caption=breed)

    # Link to dataset folder for more photos
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
# Session state initialization
# ============================================================

state = st.session_state
state.setdefault("messages", [])             # list of {"role": "user"/"assistant", "content": str}
state.setdefault("preferences", {})          # extracted preference dict
state.setdefault("step", 0)                  # conversation step
state.setdefault("theme", "light")           # "light" or "dark"
state.setdefault("results", None)            # cached top matches


# ============================================================
# Sidebar: theme, voice, reset, memory, chat history
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

    # Voice input (optional)
    st.subheader("🎙️ Voice Input")
    if HAS_MIC:
        st.caption("Record a short description; if transcribed, I’ll treat it like a chat message.")
        audio = mic_recorder(
            start_prompt="Start recording",
            stop_prompt="Stop",
            key="voice_input",
        )
        if isinstance(audio, dict) and audio.get("text"):
            voice_text = audio["text"]
            st.success(f"Transcribed: {voice_text}")
            # Push into messages as if user typed it
            state.messages.append({"role": "user", "content": voice_text})
            st.experimental_rerun()
    else:
        st.caption("Voice input is optional. Install `streamlit-mic-recorder` to enable it.")

    st.markdown("---")

    # Reset button
    if st.button("🔄 Reset Conversation"):
        state.messages = []
        state.preferences = {}
        state.step = 0
        state.results = None
        st.experimental_rerun()

    st.markdown("---")

    # Persistent memory indicator
    st.subheader("🧠 What I Know So Far")
    st.write(summarize_preferences(state.preferences))

    st.markdown("---")

    # Collapsible chat history
    with st.expander("📜 Chat history"):
        if not state.messages:
            st.write("No messages yet. Say hi to Dog Lover!")
        else:
            for m in state.messages:
                role = "You" if m["role"] == "user" else "Dog Lover"
                st.markdown(f"**{role}:** {m['content']}")


# Apply theme after reading choice
apply_theme(state.theme)

# ============================================================
# Main UI
# ============================================================

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.caption("Tell me about your lifestyle and preferences. I’ll match you with the best breed!")

# Initial greeting
if not state.messages:
    greeting = (
        "Hi there! I’m **Dog Lover**, your friendly dog-matching assistant. 🐾\n\n"
        "Tell me a bit about your lifestyle — how active you are, where you live, "
        "and any allergy or family considerations — and I’ll start narrowing down the perfect breed."
    )
    state.messages.append({"role": "assistant", "content": greeting})

# Show existing messages in chat format
for msg in state.messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.markdown(msg["content"])

# Chat input
user_message = st.chat_input("Describe your lifestyle or dream dog…")

# ============================================================
# Conversation logic
# ============================================================

if user_message:
    # Log user message
    state.messages.append({"role": "user", "content": user_message})

    # Off-topic handling (after we’ve started the flow)
    if is_off_topic(user_message) and state.step > 0:
        reply = (
            "I’m sorry, but that’s a bit outside what I can help with. "
            "Let’s get back to finding the best dog for you! 🐾"
        )
        state.messages.append({"role": "assistant", "content": reply})
        st.experimental_rerun()

    # Extract and merge preferences
    new_prefs = extract_preferences(user_message)
    state.preferences.update({k: v for k, v in new_prefs.items() if v is not None})

    step = state.step

    # Step 0 → after first message, ask about energy level
    if step == 0:
        reply = (
            "Thanks for sharing! Let’s start with **energy level**. "
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 1
        st.experimental_rerun()

    # Step 1 → ask about home size / living situation
    elif step == 1:
        reply = (
            "Great! Now let’s consider your **living situation**. "
            "Do you live in a **small apartment**, a **standard apartment**, "
            "or a **house with a yard**? 🏠"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 2
        st.experimental_rerun()

    # Step 2 → ask about allergies/shedding
    elif step == 2:
        reply = (
            "Let’s now consider the issue of **allergies**. "
            "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 3
        st.experimental_rerun()

    # Step 3 → ask about children
    elif step == 3:
        reply = (
            "The presence of **children** could be a factor. "
            "Should your dog be especially **good with young children**? (yes or no) 👶🐶"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 4
        st.experimental_rerun()

    # Step 4+ → if enough info, compute recommendations
    else:
        if len(state.preferences) >= 4:
            scores = score_breeds(state.preferences)
            top = top_n_breeds(scores, n=3)
            state.results = top

            reply = (
                "Awesome, I think I have enough information now! 🐾✨\n\n"
                "Here are your **top dog breed matches** based on everything you’ve told me:"
            )
            state.messages.append({"role": "assistant", "content": reply})
        else:
            # If somehow still not enough prefs, gently ask for more general info
            reply = (
                "I’m getting closer! Tell me a bit more about your activity level, home, "
                "allergies, or whether you have kids, and I’ll refine your matches."
            )
            state.messages.append({"role": "assistant", "content": reply})

        st.experimental_rerun()

# ============================================================
# Show recommendations (if any)
# ============================================================

if state.results:
    st.markdown("## 🎯 Your Top Matches")
    for breed, score in state.results:
        render_breed_card(breed, score)

    st.markdown(f"**Bonus dog fact:** {dog_fact()}")

