from __future__ import annotations

import random
from typing import Dict, List, Tuple
from urllib.parse import quote

import streamlit as st

from recommender_engine import (
    score_breeds,
    top_n_breeds,
    image_url_for_breed,
    folder_for_breed,
)

from trait_engine import (
    parse_preferences,
    classify_off_topic,
    summarize_preferences,
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
# Sidebar UI: Theme, Voice Input, Memory, Reset, History
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

    # Memory summary (now using trait_engine)
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
# Chatbot Logic using trait_engine
# ============================================================

if user_message:
    state.messages.append({"role": "user", "content": user_message})

    # First, parse preferences from this message
    step = state.step
    new_prefs = parse_preferences(user_message)
    # Decide if it's off-topic (step-aware)
    if classify_off_topic(user_message, step, new_prefs):
        reply = (
            "I’m sorry, but that’s a bit outside what I can help with. "
            "Let’s get back to how I can help you pick the best dog for you. 🐾"
        )
        state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # Merge new prefs into global preferences
    state.preferences.update(new_prefs)

    # Conversation flow
    if step == 0:
        reply = (
            "Awesome! Let’s start with **energy level**.\n\n"
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 1
        st.rerun()

    elif step == 1:
        reply = (
            "Great! Now let’s consider your **living situation**.\n\n"
            "Do you live in a **small apartment**, a **standard apartment**, "
            "or a **house with a yard**? 🏠"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 2
        st.rerun()

    elif step == 2:
        reply = (
            "Let’s now consider the issue of **allergies**.\n\n"
            "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 3
        st.rerun()

    elif step == 3:
        reply = (
            "The presence of **children** could be a factor.\n\n"
            "Should your dog be especially **good with young children**? (yes or no) 👶🐶"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 4
        st.rerun()

    else:
        # Final step(s): if enough info, score breeds
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
                "I’m getting closer! Tell me a bit more about your activity level, home, "
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

