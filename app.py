import streamlit as st
from chatbot_utils import (
    add_user_msg,
    add_assistant_msg,
    render_chat_history,
    load_data,
    init_memory,
    update_memory,
    memory_summary,
    extract_traits,
    typing_response,
    classify_off_topic
)
from recommender_engine import recommend_breeds


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="centered"
)


# ============================================================
# INITIALIZATION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    init_memory()

dog_breeds, trait_descriptions = load_data()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    reset = st.button("🔄 Reset Conversation")
    if reset:
        st.session_state.messages = []
        init_memory()
        st.experimental_rerun()

    st.markdown("### 🧠 Your Preferences")
    st.info(memory_summary())

    st.markdown("---")
    st.markdown("### 🌗 Theme")
    theme_choice = st.radio("Choose theme:", ["Light", "Dark"], index=0)
    if theme_choice == "Dark":
        st.markdown(
            """
            <style>
            body, .stApp { 
                background-color: #1a1a1a !important;
                color: #f2f2f2 !important;
            }
            .stChatMessage, .stMarkdown { color: #f2f2f2 !important; }
            </style>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    render_chat_history()


# ============================================================
# GREETING (only once)
# ============================================================

if len(st.session_state.messages) == 0:
    intro = (
        "👋 **Hi there! I'm Dog Lover**, your friendly dog-match chatbot!\n\n"
        "Tell me a little about your lifestyle and preferences — "
        "your energy level, where you live, allergies, children, or anything else.\n\n"
        "I'll ask follow-up questions when needed and recommend the best dog breeds for you!"
    )
    add_assistant_msg(intro)
    st.chat_message("assistant").markdown(intro)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

def process_message(user_msg: str):
    """Main message-processing pipeline."""

    # If message is off-topic → gently redirect
    if classify_off_topic(user_msg):
        reply = (
            "😅 I’m sorry, but that’s outside what I can help with.\n\n"
            "Let’s get back to finding the *perfect dog* for you! 🐶❤️"
        )
        add_assistant_msg(reply)
        st.chat_message("assistant").markdown(reply)
        return

    # Extract traits
    new_traits = extract_traits(user_msg)

    # Update memory ONLY for traits the user mentioned
    for key, value in new_traits.items():
        update_memory(key, value)

    # If no new traits were detected → ask for clarification
    if not new_traits:
        reply = (
            "Thanks! Could you tell me a bit more about your lifestyle "
            "or preferences? For example:\n"
            "• your energy level\n"
            "• where you live\n"
            "• allergies / shedding\n"
            "• children\n"
            "• preferred dog size"
        )
        add_assistant_msg(reply)
        st.chat_message("assistant").markdown(reply)
        return

    # If all major traits are collected → offer summary + recommendations
    mem = st.session_state.memory
    ready = all([
        mem.get("energy"),
        mem.get("living"),
        mem.get("allergies"),
        mem.get("children"),
        mem.get("size")
    ])

    if ready:
        summary = (
            "✨ **Here’s what I currently know about you:**\n\n"
            f"{memory_summary()}\n\n"
            "If I missed something, just let me know!"
        )
        add_assistant_msg(summary)
        st.chat_message("assistant").markdown(summary)

        # Now recommend
        recs = recommend_breeds(
            dog_breeds,
            mem.get("energy"),
            mem.get("living"),
            mem.get("allergies"),
            mem.get("children"),
            mem.get("size")
        )

        if len(recs) == 0:
            msg = "Hmm… I don’t have any perfect matches yet. Tell me more!"
            add_assistant_msg(msg)
            st.chat_message("assistant").markdown(msg)
            return

        msg = "🐾 **Here are the top dog breeds that match your preferences:**"
        add_assistant_msg(msg)
        st.chat_message("assistant").markdown(msg)

        # Show list (no images here — images handled by recommender_engine)
        for breed in recs:
            st.chat_message("assistant").markdown(f"• **{breed}**")

        return

    # If some traits still missing → keep chatting
    reply = "Great! Tell me more about your preferences 😊"
    add_assistant_msg(reply)
    st.chat_message("assistant").markdown(reply)


# ============================================================
# CHAT INPUT
# ============================================================

user_msg = st.chat_input("Type your message here…")

if user_msg:
    add_user_msg(user_msg)
    st.chat_message("user").markdown(user_msg)
    process_message(user_msg)

