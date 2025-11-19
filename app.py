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
# SESSION STATE INIT
# ============================================================

if "step" not in st.session_state:
    st.session_state.step = 1

if "memory" not in st.session_state:
    init_memory()

dog_breeds, trait_descriptions = load_data()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🔄 Reset Conversation"):
        st.session_state.step = 1
        st.session_state.memory = {
            "energy": None,
            "living": None,
            "allergies": None,
            "children": None,
            "size": None
        }
        st.experimental_rerun()

    st.markdown("### 🧠 Your Preferences")
    st.info(memory_summary())

    st.markdown("---")
    render_chat_history()


# ============================================================
# MAIN FLOW — STEP-BY-STEP QUESTIONS
# ============================================================

step = st.session_state.step
mem = st.session_state.memory


# -------------------------------
# STEP 1 — INTRODUCTION
# -------------------------------
if step == 1:
    intro = (
        "👋 **Hi there! I'm Dog Lover**, your friendly dog-match chatbot.\n\n"
        "Tell me about your **energy level**, **living space**, **allergies**, "
        "**kids**, and **preferred dog size**.\n\n"
        "I’ll guide you step by step and then recommend **three dog breeds**, "
        "each with an **image** and a short **social-post-style** description.\n\n"
        "**Let's start with your energy level.**"
    )
    st.chat_message("assistant").markdown(intro)

    energy = st.selectbox(
        "Choose your energy level:",
        ["Low", "Medium", "High"],
    )

    if st.button("Next ➡️"):
        mem["energy"] = energy.lower()
        st.session_state.step = 2
        st.experimental_rerun()


# -------------------------------
# STEP 2 — LIVING SPACE
# -------------------------------
elif step == 2:
    st.chat_message("assistant").markdown(
        "🏡 Great! Now, tell me about your **living space**."
    )

    living = st.selectbox(
        "Choose your living situation:",
        ["Small apartment", "Standard apartment", "House with yard"],
    )

    if st.button("Next ➡️"):
        mem["living"] = living.lower()
        st.session_state.step = 3
        st.experimental_rerun()


# -------------------------------
# STEP 3 — ALLERGIES
# -------------------------------
elif step == 3:
    st.chat_message("assistant").markdown(
        "🌱 Thanks! What about **allergies or shedding**?"
    )

    allergies = st.selectbox(
        "Choose an option:",
        ["Hypoallergenic", "Low-shedding", "Shedding OK"],
    )

    if st.button("Next ➡️"):
        mem["allergies"] = allergies.lower()
        st.session_state.step = 4
        st.experimental_rerun()


# -------------------------------
# STEP 4 — CHILDREN
# -------------------------------
elif step == 4:
    st.chat_message("assistant").markdown(
        "👶 Do you need a dog that's good with **children**?"
    )

    kids = st.selectbox(
        "Choose an option:",
        ["Yes", "No"],
    )

    if st.button("Next ➡️"):
        mem["children"] = kids.lower()
        st.session_state.step = 5
        st.experimental_rerun()


# -------------------------------
# STEP 5 — SIZE
# -------------------------------
elif step == 5:
    st.chat_message("assistant").markdown(
        "📏 Great! What **size of dog** do you prefer?"
    )

    size = st.selectbox(
        "Choose dog size:",
        ["Small", "Medium", "Large"],
    )

    if st.button("Show My Matches 🎯"):
        mem["size"] = size.lower()
        st.session_state.step = 6
        st.experimental_rerun()


# ============================================================
# STEP 6 — RECOMMENDATIONS
# ============================================================
elif step >= 6:
    st.markdown("### 🎯 Your Top Dog Breed Matches")

    cards = recommend_breeds_with_cards(
        dog_breeds,
        mem.get("energy"),
        mem.get("living"),
        mem.get("allergies"),
        mem.get("children"),
        mem.get("size"),
        top_n=3,
    )

    if not cards:
        st.warning(
            "I couldn't find good matches with the current preferences. "
            "Try resetting the conversation and choosing slightly broader options."
        )
    else:
        st.markdown("Here are your **top 3 dog breeds**:")

        for i, card in enumerate(cards, start=1):
            st.markdown(f"#### #{i} — {card['breed']}")

            st.image(
                card["image_url"],
                caption=card["breed"],
                width=280,  # 👉 smaller image size as you requested
            )

            st.markdown(card["summary"])

    st.markdown("---")
    st.info("Want to try different answers? Use **Reset Conversation** in the sidebar.")
