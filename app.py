# -------------------------------------------------------
# Dog Lover Chatbot — Streamlit Frontend
#
# This app helps match users with the best dog breeds
# based on lifestyle preferences such as:
# - energy level
# - living situation
# - allergies / shedding
# - good with kids
#
# Sidebar provides:
# - Theme toggle
# - Reset conversation
#
# Chat area:
# - Greeting
# - Conversation flow
# -------------------------------------------------------

import streamlit as st
from trait_engine import (
    extract_traits_from_message,
    merge_traits,
    classify_off_topic
)
from recommender_engine import recommend_breeds
from chatbot_utils import typing_response

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="wide"
)

# -------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "traits" not in st.session_state:
    st.session_state.traits = {}

if "theme" not in st.session_state:
    st.session_state.theme = "light"

# -------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------
with st.sidebar:
    st.markdown("## 🐾 Dog Lover Settings")

    # Theme toggle
    st.markdown("**Theme:**")
    theme_choice = st.radio("Theme", ["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
    st.session_state.theme = theme_choice

    # Reset conversation
    st.markdown(" ")
    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.traits = {}
        st.experimental_rerun()

# -------------------------------------------------------
# APPLY THEME
# -------------------------------------------------------
if st.session_state.theme == "dark":
    st.markdown("""
    <style>
        body, [class*="stApp"] {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
        }
        .stChatMessage {
            background-color: #2c2c2c !important;
        }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------------
# HEADER
# -------------------------------------------------------
st.markdown("# 🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.markdown("Tell me about your lifestyle and preferences. I’ll match you with the perfect dog!")

# -------------------------------------------------------
# CHAT DISPLAY
# -------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------------------------------------
# PROCESSING LOGIC
# -------------------------------------------------------
def process_message(user_msg: str):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # 1. Off-topic check
    if classify_off_topic(user_msg):
        bot_reply = "I’m sorry, but that’s a bit outside what I can help with. Let’s stay focused on finding your perfect dog. 🐾"
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        return

    # 2. Extract traits
    new_traits = extract_traits_from_message(user_msg)

    # Merge traits
    st.session_state.traits = merge_traits(st.session_state.traits, new_traits)

    # 3. If we have enough info → Recommend
    if len(st.session_state.traits) >= 3:
        st.session_state.messages.append({
            "role": "assistant",
            "content": typing_response("Here’s what I currently know about you:\n" +
                                      "\n".join([f"• **{k}**: {v}" for k, v in st.session_state.traits.items()]) +
                                      "\n\nLet me suggest some breeds for you! 🐕✨")
        })

        recs = recommend_breeds(st.session_state.traits)
        rec_text = typing_response("Here are my top matches:\n" + "\n".join([f"🐶 {r}" for r in recs]))
        st.session_state.messages.append({"role": "assistant", "content": rec_text})
        return

    # 4. Otherwise continue asking questions
    next_q = next_question(st.session_state.traits)
    st.session_state.messages.append({"role": "assistant", "content": typing_response(next_q)})

# -------------------------------------------------------
# NEXT QUESTION FLOW
# -------------------------------------------------------
def next_question(traits):
    if "energy" not in traits:
        return "Awesome! Let’s start with **energy level**.\n\nWould your ideal dog be **low**, **medium**, or **high** energy? 🐕‍🦺⚡"

    if "living_space" not in traits:
        return "Great — I’ve already noted your living situation. 🏡\n\nDo you live in a **small apartment**, **standard apartment**, or a **house with a yard**? 🏠"

    if "shedding" not in traits:
        return "Let’s talk about **allergies** and **shedding**.\n\nDo you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐩"

    if "children" not in traits:
        return "The presence of **children** could be a factor.\n\nShould your dog be especially **good with young children**? (yes or no) 👶🐶"

    return "Tell me anything else about your ideal dog!"

# -------------------------------------------------------
# USER INPUT
# -------------------------------------------------------
user_msg = st.chat_input("Tell me about your lifestyle or dog preferences...")

if user_msg:
    process_message(user_msg)
    st.experimental_rerun()
