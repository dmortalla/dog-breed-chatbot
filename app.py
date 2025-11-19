from __future__ import annotations
import random
from typing import Dict
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

# Try voice input
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
except:
    HAS_MIC = False


# ============================================================
# THEMING
# ============================================================

def apply_theme(theme: str):
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


# ============================================================
# DOG FACTS
# ============================================================

def dog_fact():
    facts = [
        "A dog’s nose print is unique — like a fingerprint!",
        "Greyhounds can reach speeds up to 45 mph.",
        "The Basenji is known as the 'barkless dog.'",
        "Puppies are born blind and deaf, but develop quickly.",
        "Some dogs can learn more than 1,000 words."
    ]
    return random.choice(facts)


# ============================================================
# RECOMMENDER CARD
# ============================================================

def render_breed_card(breed: str, score: float):
    st.markdown(f"### 🐕 {breed} — Match score: {score:.1f}/100")

    img = image_url_for_breed(breed)
    if img:
        st.image(img, width=320, caption=breed)

    link = (
        "https://github.com/maartenvandenbroeck/"
        "Dog-Breeds-Dataset/tree/master/"
        f"{quote(folder_for_breed(breed))}"
    )
    st.markdown(f"[📸 More photos of **{breed}**]({link})")
    st.markdown("---")


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="centered",
)

state = st.session_state
state.setdefault("messages", [])
state.setdefault("preferences", {})
state.setdefault("step", 0)
state.setdefault("theme", "light")
state.setdefault("results", None)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🎛️ Controls")

    # Theme toggle
    theme = st.radio("Theme", ["Light", "Dark"])
    state.theme = "light" if theme == "Light" else "dark"

    st.markdown("---")

    # Voice input
    st.subheader("🎙️ Voice Input")
    if HAS_MIC:
        audio = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop",
            key="voice",
        )
        if isinstance(audio, dict) and audio.get("text"):
            state.messages.append({"role": "user", "content": audio["text"]})
            st.rerun()
    else:
        st.caption("Install streamlit-mic-recorder to enable voice input.")

    st.markdown("---")

    # Reset
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

    with st.expander("📜 Chat History"):
        for m in state.messages:
            who = "You" if m["role"] == "user" else "Dog Lover"
            st.markdown(f"**{who}:** {m['content']}")


apply_theme(state.theme)


# ============================================================
# MAIN CHAT UI
# ============================================================

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.caption("Tell me about your lifestyle and preferences — I'll match you with your ideal dog!")

if not state.messages:
    greeting = (
        "Hi there! I’m **Dog Lover**, your friendly dog-matching assistant. 🐾\n\n"
        "Tell me about your home, activity level, allergies, or kids — "
        "and I’ll ask a few simple questions to find perfect matching breeds!"
    )
    state.messages.append({"role": "assistant", "content": greeting})

# Render chat
for msg in state.messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.markdown(msg["content"])

user_input = st.chat_input("Describe your lifestyle or dream dog…")


# ============================================================
# CHAT LOGIC
# ============================================================

if user_input:
    state.messages.append({"role": "user", "content": user_input})

    step = state.step
    new_prefs = parse_preferences(user_input)

    # Off-topic filter
    if classify_off_topic(user_input, step, new_prefs):
        reply = (
            "I’m sorry, but that’s a bit outside what I can help with. "
            "Let’s get back to finding you the perfect dog! 🐾"
        )
        state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # Merge preferences
    state.preferences.update(new_prefs)

    # === STEP 0: Ask for energy level ===
    if step == 0:
        reply = (
            "Awesome! Let’s start with **energy level**.\n\n"
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 1
        st.rerun()

    # === STEP 1: Ask living situation (skip if known) ===
    elif step == 1:
        if "home" in state.preferences:
            reply = (
                "Great — I’ve already noted your living situation! 🏠\n\n"
                "Now let’s consider **allergies**. Do you prefer **low-shedding** "
                "or **hypoallergenic** dogs? 🌿🐕"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 2
            st.rerun()
        else:
            reply = (
                "Great! Now let’s consider your **living situation**.\n\n"
                "Do you live in a **small apartment**, a **standard apartment**, "
                "or a **house with a yard**? 🏠"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 2
            st.rerun()

    # === STEP 2: Ask allergies (skip if known) ===
    elif step == 2:
        if "allergies" in state.preferences:
            reply = (
                "Got it — I’ve already noted your allergy preferences. 🌿\n\n"
                "Now one last thing: **children**. Should your dog be especially "
                "good with **young kids**? (yes or no) 👶🐶"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 3
            st.rerun()
        else:
            reply = (
                "Let’s now consider **allergies**.\n\n"
                "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 3
            st.rerun()

    # === STEP 3: Ask kid-friendliness (skip if known) ===
    elif step == 3:
        if "kids" in state.preferences:
            # Enough info?
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
                    "We’re almost there! Tell me anything else about your lifestyle "
                    "and I’ll refine the match."
                )
                state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        else:
            reply = (
                "The presence of **children** could be a factor.\n\n"
                "Should your dog be especially good with **young children**? "
                "(yes or no) 👶🐶"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 4
            st.rerun()

    # === STEP 4+: Recommend ===
    else:
        scores = score_breeds(state.preferences)
        state.results = top_n_breeds(scores, n=3)
        reply = (
            "Amazing — I think I have enough information now! 🐾✨\n\n"
            "Here are your **top dog breed matches**:"
        )
        state.messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ============================================================
# SHOW RESULTS
# ============================================================

if state.results:
    st.markdown("## 🎯 Your Top Matches")

    for breed, score in state.results:
        render_breed_card(breed, score)

    st.markdown(f"**Bonus dog fact:** {dog_fact()}")

