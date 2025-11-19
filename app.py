from __future__ import annotations

import random
import time
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

# Try voice input (optional)
try:
    from streamlit_mic_recorder import mic_recorder
    HAS_MIC = True
except Exception:
    HAS_MIC = False


# ============================================================
# THEMING & BASIC STYLING
# ============================================================

def apply_theme(theme: str) -> None:
    """Apply improved light/dark theme with readable contrast."""
    if theme == "dark":
        css = """
        <style>
        /* === Main background === */
        body {
            background-color: #1e293b !important;  /* Soft slate gray */
            color: #f1f5f9 !important;             /* Bright text */
        }

        /* === Sidebar === */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;  /* Dark navy */
            color: #f8fafc !important;
        }

        /* === Chat bubbles === */
        [data-testid="stChatMessage"] {
            margin-bottom: 0.4rem;
        }

        [data-testid="stChatMessage"] > div {
            border-radius: 16px;
            padding: 8px 12px;
        }

        /* User bubble */
        [data-testid="stChatMessage"][data-testid="stChatMessage-user"] > div {
            background: #334155 !important;   /* Slate gray */
            color: #f1f5f9 !important;        /* Soft white */
        }

        /* Assistant bubble */
        [data-testid="stChatMessage"][data-testid="stChatMessage-assistant"] > div {
            background: #0f172a !important;   /* Dark navy */
            color: #f1f5f9 !important;
        }

        /* Inputs */
        .stTextInput input, .stChatInput textarea {
            background: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #475569 !important;
        }
        </style>
        """
    else:
        css = """
        <style>
        body {
            background-color: #ffffff !important;
            color: #111827 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #f9fafb !important;
        }
        [data-testid="stChatMessage"] {
            margin-bottom: 0.4rem;
        }
        [data-testid="stChatMessage"] > div {
            border-radius: 16px;
            padding: 8px 12px;
        }
        [data-testid="stChatMessage"][data-testid="stChatMessage-user"] > div {
            background: #e5f3ff !important;
        }
        [data-testid="stChatMessage"][data-testid="stChatMessage-assistant"] > div {
            background: #f3f4f6 !important;
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

# ============================================================
# DOG FACTS
# ============================================================

def dog_fact() -> str:
    facts = [
        "A dog’s nose print is unique — like a fingerprint!",
        "Greyhounds can reach speeds up to 45 mph.",
        "The Basenji is known as the 'barkless dog.'",
        "Puppies are born blind and deaf, but develop quickly.",
        "Some dogs can learn more than 1,000 words.",
    ]
    return random.choice(facts)


# ============================================================
# RECOMMENDER DISPLAY
# ============================================================

def render_breed_card(breed: str, score: float) -> None:
    """Display one breed recommendation with image and dataset link."""
    st.markdown(f"### 🐕 {breed} — Match score: {score:.1f}/100")

    img_url = image_url_for_breed(breed)
    if img_url:
        st.image(img_url, width=320, caption=breed)

    folder = folder_for_breed(breed)
    gh_url = (
        "https://github.com/maartenvandenbroeck/"
        "Dog-Breeds-Dataset/tree/master/"
        f"{quote(folder)}"
    )
    st.markdown(f"[📸 More photos of **{breed}** in the dataset]({gh_url})")
    st.markdown("---")


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot — Find Your Perfect Dog Breed",
    page_icon="🐶",
    layout="centered",
)

state = st.session_state
state.setdefault("messages", [])
state.setdefault("preferences", {})
state.setdefault("step", 0)
state.setdefault("theme", "light")
state.setdefault("results", None)
state.setdefault("animate_last", False)  # for typing animation


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("🎛️ Controls")

    # Theme toggle
    theme_choice = st.radio("Theme", ["Light", "Dark"])
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
            state.messages.append({"role": "user", "content": audio["text"]})
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
        state.animate_last = False
        st.rerun()

    st.markdown("---")

    # Memory summary (sidebar)
    st.subheader("🧠 What I Know So Far")
    st.write(summarize_preferences(state.preferences))

    st.markdown("---")

    # Collapsible chat history
    with st.expander("📜 Chat History"):
        if not state.messages:
            st.write("No messages yet.")
        else:
            for m in state.messages:
                who = "You" if m["role"] == "user" else "Dog Lover"
                st.markdown(f"**{who}:** {m['content']}")


# Apply theme after sidebar
apply_theme(state.theme)


# ============================================================
# MAIN CHAT UI
# ============================================================

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.caption("Tell me about your lifestyle and preferences — I’ll match you with your ideal dog!")

# Small “memory snapshot” indicator in the main area
prefs = state.preferences
snapshot_labels = []
if "energy" in prefs:
    snapshot_labels.append("⚡ Energy")
if "home" in prefs:
    snapshot_labels.append("🏠 Home")
if "allergies" in prefs:
    snapshot_labels.append("🌿 Allergies")
if "kids" in prefs:
    snapshot_labels.append("👶 Kids")

if snapshot_labels:
    st.markdown("**Memory snapshot:** " + " · ".join(snapshot_labels))
else:
    st.markdown("_Memory snapshot: I’m still getting to know you…_")

st.markdown("---")

# Initial greeting
if not state.messages:
    greeting = (
        "Hi there! I’m **Dog Lover**, your friendly dog-matching companion. 🐾\n\n"
        "Tell me about your home, activity level, allergies, or children — "
        "and I’ll ask a few follow-up questions to find your perfect breed."
    )
    state.messages.append({"role": "assistant", "content": greeting})

# Render chat messages with typing animation for the latest assistant reply
messages = state.messages
for idx, msg in enumerate(messages):
    role = msg["role"]
    is_last_assistant = (
        state.animate_last
        and role == "assistant"
        and idx == len(messages) - 1
    )

    with st.chat_message("assistant" if role == "assistant" else "user"):
        if is_last_assistant:
            # Typing animation for the latest assistant message only
            placeholder = st.empty()
            text = msg["content"]
            typed = ""
            for word in text.split(" "):
                typed += word + " "
                placeholder.markdown(typed + "▌")
                time.sleep(0.03)
            placeholder.markdown(text)
        else:
            st.markdown(msg["content"])

# Once drawn, turn off animation for next rerun
state.animate_last = False

# Chat input
user_input = st.chat_input("Describe your lifestyle or dream dog…")


# ============================================================
# CHAT / CONVERSATION LOGIC
# ============================================================

if user_input:
    state.messages.append({"role": "user", "content": user_input})

    step = state.step
    new_prefs: Dict[str, int] = parse_preferences(user_input)

    # Off-topic detection
    if classify_off_topic(user_input, step, new_prefs):
        reply = (
            "I’m sorry, but that’s a bit outside what I can do. "
            "Let’s get back to how I can help you pick the best dog for you. 🐾"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.animate_last = True
        st.rerun()

    # Merge newly extracted preferences
    state.preferences.update(new_prefs)

    # === STEP 0: Ask about energy level ===
    if step == 0:
        reply = (
            "Awesome! Let’s start with **energy level**.\n\n"
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.step = 1
        state.animate_last = True
        st.rerun()

    # === STEP 1: Ask about living situation (skip if already known) ===
    elif step == 1:
        if "home" in state.preferences:
            reply = (
                "Great — I’ve already noted your living situation. 🏠\n\n"
                "Let’s now consider the issue of **allergies**.\n\n"
                "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 2
            state.animate_last = True
            st.rerun()
        else:
            reply = (
                "Great! Now let’s consider your **living situation**.\n\n"
                "Do you live in a **small apartment**, a **standard apartment**, "
                "or a **house with a yard**? 🏠"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 2
            state.animate_last = True
            st.rerun()

    # === STEP 2: Ask about allergies (skip if already known) ===
    elif step == 2:
        if "allergies" in state.preferences:
            reply = (
                "Got it — I’ve already noted your allergy preferences. 🌿✅\n\n"
                "The presence of **children** could be a factor.\n\n"
                "Should your dog be especially **good with young children**? "
                "(yes or no) 👶🐶"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 3
            state.animate_last = True
            st.rerun()
        else:
            reply = (
                "Let’s now consider the issue of **allergies**.\n\n"
                "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 3
            state.animate_last = True
            st.rerun()

    # === STEP 3: Ask about kid-friendliness (skip if already known) ===
    elif step == 3:
        if "kids" in state.preferences:
            # Already know about kids — either recommend or ask for a bit more
            if len(state.preferences) >= 4:
                scores = score_breeds(state.preferences)
                state.results = top_n_breeds(scores, n=3)
                reply = (
                    "Amazing — I think I have enough information now! 🐾✨\n\n"
                    "Here are your **top dog breed matches**:"
                )
                state.messages.append({"role": "assistant", "content": reply})
                state.animate_last = True
            else:
                reply = (
                    "We’re almost there! Tell me anything else about your lifestyle "
                    "and I’ll refine the match."
                )
                state.messages.append({"role": "assistant", "content": reply})
                state.animate_last = True
            st.rerun()
        else:
            reply = (
                "The presence of **children** could be a factor.\n\n"
                "Should your dog be especially **good with young children**? "
                "(yes or no) 👶🐶"
            )
            state.messages.append({"role": "assistant", "content": reply})
            state.step = 4
            state.animate_last = True
            st.rerun()

    # === STEP 4+: Compute recommendations ===
    else:
        scores = score_breeds(state.preferences)
        state.results = top_n_breeds(scores, n=3)
        reply = (
            "Awesome, I think I have enough information now! 🐾✨\n\n"
            "Here are your **top dog breed matches** based on everything you’ve told me:"
        )
        state.messages.append({"role": "assistant", "content": reply})
        state.animate_last = True
        st.rerun()


# ============================================================
# SHOW RESULTS
# ============================================================

if state.results:
    st.markdown("## 🎯 Your Top Matches (with photos)")
    for breed, score in state.results:
        render_breed_card(breed, score)

    st.markdown(f"**Bonus dog fact:** {dog_fact()}")
