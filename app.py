import streamlit as st
import time
import random

from recommender_engine import (
    extract_preferences,
    score_breeds,
    top_n_breeds,
    image_url_for_breed,
)

# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def typing_text(message, delay=0.015):
    """Simulates typing animation by printing one character at a time."""
    placeholder = st.empty()
    text = ""
    for char in message:
        text += char
        placeholder.markdown(text)
        time.sleep(delay)
    return placeholder

def dog_fact():
    """Returns a random fun dog fact."""
    facts = [
        "A dog’s nose print is unique — just like a human fingerprint.",
        "Dogs can understand over 150 words.",
        "Some dogs can learn more than 1,000 words!",
        "The Basenji is known as the 'barkless dog.'",
        "A Greyhound can run up to 45 miles per hour!",
    ]
    return random.choice(facts)

def is_off_topic(user_message: str) -> bool:
    """Detect messages that contain no dog-related preference keywords."""
    keywords = [
        "energy", "active", "calm",
        "shed", "shedding", "allerg",
        "child", "kids", "apartment",
        "yard", "space", "train",
        "protective", "friendly",
    ]
    msg = user_message.lower()
    return not any(k in msg for k in keywords)

# -------------------------------------------------------------------
# Session State Setup
# -------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "preferences" not in st.session_state:
    st.session_state.preferences = {}

if "conversation_step" not in st.session_state:
    st.session_state.conversation_step = 0

# -------------------------------------------------------------------
# Header UI
# -------------------------------------------------------------------

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.caption("Tell me about your lifestyle and preferences. I’ll match you with the best breed!")

# Reset button
if st.button("🔄 Reset Conversation"):
    st.session_state.messages = []
    st.session_state.preferences = {}
    st.session_state.conversation_step = 0
    st.rerun()

# Chat container
chat_container = st.container()

# -------------------------------------------------------------------
# Display Past Messages
# -------------------------------------------------------------------

with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown(f"💬 **Dog Lover:** {msg['content']}")
        else:
            st.markdown(f"🧑 **You:** {msg['content']}")

# -------------------------------------------------------------------
# User Input
# -------------------------------------------------------------------

user_message = st.chat_input("Tell me something about yourself, your lifestyle, or your dog preferences…")

# -------------------------------------------------------------------
# Bot Logic
# -------------------------------------------------------------------

if user_message:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_message})

    # Off-topic protection
    if is_off_topic(user_message) and st.session_state.conversation_step > 0:
        bot_reply = (
            "I’m sorry, but that’s a little beyond what I can help with. "
            "Let’s get back to finding the perfect dog for you! 🐾💛"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.rerun()

    prefs = st.session_state.preferences

    # Extract new preferences from the message
    new_prefs = extract_preferences(user_message)
    prefs.update({k: v for k, v in new_prefs.items() if v is not None})

    # Determine conversation step
    step = st.session_state.conversation_step

    # -------------------------------------------------------------------
    # Step 0 — Greeting + initial acknowledgment
    # -------------------------------------------------------------------
    if step == 0:
        bot_msg = (
            "Hi there! I’m **Dog Lover**, your friendly dog-matching assistant! 🐶✨ "
            "Tell me a bit about your lifestyle — what’s your activity level, living situation, and what kind of dog you imagine yourself having?"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
        st.session_state.conversation_step = 1
        st.rerun()

    # -------------------------------------------------------------------
    # Step 1 — Ask about energy level
    # -------------------------------------------------------------------
    if step == 1:
        bot_msg = (
            "Thanks for sharing! Let’s talk about **energy level**. "
            "Would your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
        st.session_state.conversation_step = 2
        st.rerun()

    # -------------------------------------------------------------------
    # Step 2 — Ask about home size
    # -------------------------------------------------------------------
    if step == 2:
        bot_msg = (
            "Let’s now consider your **living situation**. "
            "Do you live in a **small apartment**, **standard apartment**, or **home with a yard**? 🏡"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
        st.session_state.conversation_step = 3
        st.rerun()

    # -------------------------------------------------------------------
    # Step 3 — Ask about allergies (your custom phrasing)
    # -------------------------------------------------------------------
    if step == 3:
        bot_msg = (
            "Let’s now consider the issue of **allergies**. "
            "Do you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
        st.session_state.conversation_step = 4
        st.rerun()

    # -------------------------------------------------------------------
    # Step 4 — Ask about kid-friendliness (your custom phrasing)
    # -------------------------------------------------------------------
    if step == 4:
        bot_msg = (
            "The presence of **children** could be a factor. "
            "Should your dog be especially **good with young children**? (yes or no) 👶🐶"
        )
        st.session_state.messages.append({"role": "assistant", "content": bot_msg})
        st.session_state.conversation_step = 5
        st.rerun()

    # -------------------------------------------------------------------
    # Step 5 — Enough info → compute recommendations
    # -------------------------------------------------------------------

    if step == 5 and len(prefs) >= 4:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Awesome, I think I have enough information now! 🐾✨\n\n"
                "Here are your **top dog breed matches** based on everything you’ve told me:\n\n"
            )
        })

        # Generate matches
        scores = score_breeds(prefs)
        top = top_n_breeds(scores, n=3)

        # Display dog matches
        for rank, (breed, score) in enumerate(top, start=1):
            st.markdown(f"### #{rank} — **{breed}** (Match score: {score:.1f}/100)")
            url = image_url_for_breed(breed)
            if url:
                st.image(url, width=350, caption=breed)
            st.markdown(
                f"[More photos of **{breed}** in the dataset](https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset/tree/master/{breed.lower()}%20dog)"
            )
            st.markdown("---")

        # Add a fun dog fact
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Bonus dog fact:** {dog_fact()}"
        })

        st.rerun()
