import streamlit as st
from chatbot_utils import (
    add_user_msg,
    add_assistant_msg,
    render_chat_history,
    load_data,
    init_memory,
    update_memory,
    memory_summary,
    classify_off_topic
)
from recommender_engine import recommend_breeds_with_cards


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="wide"
)


# ============================================================
# INITIALIZATION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    init_memory()

if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1  # 1–5

dog_breeds, trait_descriptions = load_data()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        init_memory()
        st.session_state.wizard_step = 1
        st.rerun()

    st.markdown("### 🧠 Your Preferences")
    st.info(memory_summary())

    st.markdown("---")
    render_chat_history()


# ============================================================
# INTRO MESSAGE (only once)
# ============================================================

if len(st.session_state.messages) == 0:
    intro = (
        "👋 **Hi there! I'm Dog Lover**, your friendly dog-match chatbot!\n\n"
        "Tell me about your **energy level**, **living space**, **allergies**, **kids**, "
        "and **preferred dog size**.\n\n"
        "I'll recommend the best dog breeds along with images and social-style summaries.\n\n"
        "**Let's start with your energy level. Select one from the options shown in the drop-down menu.**"
    )
    add_assistant_msg(intro)
    st.chat_message("assistant").markdown(intro)


# ============================================================
# WIZARD STEP LAYOUT
# ============================================================

def ask_energy():
    st.markdown("### 1️⃣ Select your **energy level**")
    choice = st.selectbox(
        "How energetic are you?",
        ["Select one...", "Low", "Medium", "High"],
        key="energy_input"
    )
    if st.button("Next ➜", key="next1"):
        if choice == "Select one...":
            st.warning("Please choose an option to continue.")
            return
        update_memory("energy", choice.lower())
        st.session_state.wizard_step = 2
        st.rerun()


def ask_living():
    st.markdown("### 2️⃣ Select your **living situation**")
    choice = st.selectbox(
        "Where do you live?",
        ["Select one...", "Small apartment", "Apartment", "House with yard"],
        key="living_input"
    )
    if st.button("Next ➜", key="next2"):
        if choice == "Select one...":
            st.warning("Please choose an option to continue.")
            return
        update_memory("living", choice.lower())
        st.session_state.wizard_step = 3
        st.rerun()


def ask_allergies():
    st.markdown("### 3️⃣ Select your **allergy / shedding preference**")
    choice = st.selectbox(
        "Do you have allergy preferences?",
        ["Select one...", "Hypoallergenic", "Low-shedding", "No special requirement"],
        key="allergy_input"
    )
    if st.button("Next ➜", key="next3"):
        if choice == "Select one...":
            st.warning("Please choose an option to continue.")
            return
        update_memory("allergies", choice.lower())
        st.session_state.wizard_step = 4
        st.rerun()


def ask_children():
    st.markdown("### 4️⃣ Are **kids** part of your home?")
    choice = st.selectbox(
        "Good with children?",
        ["Select one...", "Yes", "No"],
        key="children_input"
    )
    if st.button("Next ➜", key="next4"):
        if choice == "Select one...":
            st.warning("Please choose an option to continue.")
            return
        update_memory("children", choice.lower())
        st.session_state.wizard_step = 5
        st.rerun()


def ask_size():
    st.markdown("### 5️⃣ What **dog size** do you prefer?")
    choice = st.selectbox(
        "Choose a size:",
        ["Select one...", "Small", "Medium", "Large"],
        key="size_input"
    )
    if st.button("Show Recommendations 🐶", key="next5"):
        if choice == "Select one...":
            st.warning("Please choose an option to continue.")
            return
        update_memory("size", choice.lower())
        st.session_state.wizard_step = 6
        st.rerun()


def show_recommendations():
    mem = st.session_state.memory

    st.markdown("## 🎉 Your Top 3 Dog Matches!")

    recs = recommend_breeds_with_cards(
        dog_breeds,
        energy=mem["energy"],
        living=mem["living"],
        allergies=mem["allergies"],
        children=mem["children"],
        size=mem["size"],
    )

    if not recs:
        st.error("No matches found — try adjusting your answers in the sidebar.")
        return

    for card in recs:
        breed = card["breed"]
        st.markdown(f"### 🐕 **{breed}**")
        if card["image_url"]:
            st.image(card["image_url"], width=400)
        st.markdown(card["summary"])
        st.markdown(
            f"[View more {breed} photos ↗]({card['dataset_link']})"
        )


# ============================================================
# BLOCK USER TYPING DURING WIZARD
# ============================================================

user_msg = st.chat_input("You can type here, but selections happen above...")

if user_msg:
    # Redirect off-topic or free text during wizard to keep user on track
    add_user_msg(user_msg)

    if st.session_state.wizard_step <= 5:
        polite = (
            "😊 We're selecting your perfect dog one step at a time.\n"
            "Please use the **dropdown menu above** to continue."
        )
        add_assistant_msg(polite)
        st.chat_message("assistant").markdown(polite)

    else:
        # After wizard finishes, typing is allowed
        if classify_off_topic(user_msg):
            reply = (
                "😅 I can only help with choosing your ideal dog.\n"
                "Try asking about dog traits or ask to restart."
            )
            add_assistant_msg(reply)
            st.chat_message("assistant").markdown(reply)
        else:
            reply = "You're all set! Want to restart and try different preferences?"
            add_assistant_msg(reply)
            st.chat_message("assistant").markdown(reply)


# ============================================================
# WIZARD FLOW CONTROL
# ============================================================

step = st.session_state.wizard_step

if step == 1:
    ask_energy()
elif step == 2:
    ask_living()
elif step == 3:
    ask_allergies()
elif step == 4:
    ask_children()
elif step == 5:
    ask_size()
elif step == 6:
    show_recommendations()

