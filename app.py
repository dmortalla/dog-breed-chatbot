import re
import unicodedata

import streamlit as st

from chatbot_utils import (
    add_user_msg,
    add_assistant_msg,
    render_chat_history,
    load_data,
    init_memory,
    update_memory,
    memory_summary,
)
from recommender_engine import recommend_breeds


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="wide",
)


# ============================================================
# INITIALIZATION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

init_memory()

if "wizard_step" not in st.session_state:
    st.session_state.wizard_step = 1

dog_breeds, trait_descriptions = load_data()


def _safe_rerun():
    """Handle different Streamlit versions safely."""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _breed_to_folder(breed_name: str) -> str:
    """
    Convert a breed name from the CSV into a folder-friendly slug.

    Handles odd characters like 'Â', accents, brackets, etc., so that
    'ShihÂ Tzu' -> 'shih_tzu', 'AmericanÂ HairlessÂ Terriers' -> 'american_hairless_terriers'.
    """
    text = unicodedata.normalize("NFKD", str(breed_name))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("(", " ").replace(")", " ")
    text = text.replace("'", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        init_memory()
        st.session_state.wizard_step = 1
        _safe_rerun()

    st.markdown("### 🧠 Your Preferences So Far")
    st.info(memory_summary())

    st.markdown("---")
    render_chat_history()


# ============================================================
# MAIN CHAT AREA
# ============================================================

st.title("🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")

# ============================================================
# FIXED INTRO — shown only once & NOT doubled
# ============================================================

if not st.session_state.get("intro_shown", False):
    intro = (
        "Hi there! I'm **Dog Lover**, your friendly dog-match chatbot.\n\n"
        "Tell me about your energy level, living space (apartment / house with yard), "
        "allergies or shedding concerns, whether you have kids, and what size of dog you’d like.\n\n"
        "I’ll guide you step by step and then recommend three dog breeds, each with an image "
        "and a short ‘social-post-style’ description.\n\n"
        "**Let's start with your energy level.** Select one from the options shown in the drop-down menu below."
    )
    # Only show visually — DO NOT store in chat history
    st.chat_message("assistant").markdown(intro)

    # Mark it shown so it never appears again
    st.session_state.intro_shown = True

# Render existing messages normally
for role, content in st.session_state.messages:
    st.chat_message(role).markdown(content)

step = st.session_state.wizard_step
mem = st.session_state.memory


# ============================================================
# STEP 1 — ENERGY LEVEL
# ============================================================

if step == 1:
    st.markdown("### Step 1: Energy Level")
    choice = st.selectbox(
        "Would your ideal dog be low, medium, or high energy?",
        ["(Select one)", "low", "medium", "high"],
        key="energy_select",
    )
    if choice != "(Select one)" and mem.get("energy") is None:
        update_memory("energy", choice)
        add_user_msg(f"My ideal dog's energy level is **{choice}**.")
        add_assistant_msg(
            "Great — now let’s consider your **living situation**. "
            "Next, choose your home type from the drop-down menu."
        )
        st.session_state.wizard_step = 2
        _safe_rerun()


# ============================================================
# STEP 2 — LIVING SPACE
# ============================================================

elif step == 2:
    st.markdown("### Step 2: Living Space")
    choice = st.selectbox(
        "Which best describes where you live?",
        [
            "(Select one)",
            "small apartment",
            "standard apartment",
            "house with a yard",
        ],
        key="living_select",
    )
    if choice != "(Select one)" and mem.get("living") is None:
        update_memory("living", choice)
        add_user_msg(f"I live in a **{choice}**.")
        add_assistant_msg(
            "Thanks! Now let’s think about **allergies and shedding**. "
            "Some people prefer low-shedding or hypoallergenic dogs."
        )
        st.session_state.wizard_step = 3
        _safe_rerun()


# ============================================================
# STEP 3 — ALLERGIES / SHEDDING
# ============================================================

elif step == 3:
    st.markdown("### Step 3: Allergies & Shedding")
    choice = st.selectbox(
        "Which option fits you best?",
        [
            "(Select one)",
            "no strong preference",
            "low-shedding",
            "hypoallergenic",
        ],
        key="allergy_select",
    )
    if choice != "(Select one)" and mem.get("allergies") is None:
        value = None if choice == "no strong preference" else choice
        update_memory("allergies", value)
        add_user_msg(f"My shedding/allergy preference is: **{choice}**.")
        add_assistant_msg(
            "Good to know. The presence of **children** can also be important. "
            "Next, tell me if your dog should be especially good with young children."
        )
        st.session_state.wizard_step = 4
        _safe_rerun()


# ============================================================
# STEP 4 — CHILDREN
# ============================================================

elif step == 4:
    st.markdown("### Step 4: Children")
    choice = st.selectbox(
        "Should your dog be especially good with young children?",
        [
            "(Select one)",
            "yes",
            "no",
            "not important",
        ],
        key="children_select",
    )
    if choice != "(Select one)" and mem.get("children") is None:
        value = None if choice == "not important" else choice
        update_memory("children", value)
        add_user_msg(f"Good with young children: **{choice}**.")
        add_assistant_msg(
            "Got it. Finally, let’s talk about **dog size**. "
            "Choose the size you prefer, or pick 'no preference'."
        )
        st.session_state.wizard_step = 5
        _safe_rerun()


# ============================================================
# STEP 5 — SIZE
# ============================================================

elif step == 5:
    st.markdown("### Step 5: Dog Size")
    choice = st.selectbox(
        "What size of dog do you prefer?",
        [
            "(Select one)",
            "small",
            "medium",
            "large",
            "no preference",
        ],
        key="size_select",
    )
    if choice != "(Select one)" and mem.get("size") is None:
        value = None if choice == "no preference" else choice
        update_memory("size", value)
        add_user_msg(f"My preferred dog size is: **{choice}**.")
        add_assistant_msg(
            "Awesome! I think I have enough information now. "
            "Let me compute your best matches…"
        )
        st.session_state.wizard_step = 6
        _safe_rerun()


# ============================================================
# STEP 6 — RECOMMENDATIONS
# ============================================================

elif step >= 6:
    st.markdown("### 🎯 Your Top Dog Breed Matches")

    recs = recommend_breeds(
        dog_breeds,
        mem.get("energy"),
        mem.get("living"),
        mem.get("allergies"),
        mem.get("children"),
        mem.get("size")
    )

    if not recs:
        st.warning(
            "I couldn't find good matches with the current preferences. "
            "Try resetting the conversation and choosing slightly broader options."
        )
    else:
        st.markdown("Here are your **top 3 dog breeds** based on your choices:")

        for breed in recs:
            # folder name: lowercase, spaces -> underscores, no special chars
            folder = breed.lower().replace(" ", "_").replace("’", "").replace("'", "")
            image_path = f"data/dog_images/{folder}/Image_1.jpg"

            col1, col2 = st.columns([1, 2])

            with col1:
                try:
                    st.image(image_path, width=220, caption=breed)
                except:
                    st.warning(f"No image found for {breed}")

            with col2:
                st.markdown(
                    f"""
                    ### 🐾 {breed}

                    **Why this breed may be a good fit:**
                    - Energy level preference: **{mem.get('energy')}**
                    - Home type: **{mem.get('living')}**
                    - Allergies/shedding: **{mem.get('allergies')}**
                    - Good with kids: **{mem.get('children')}**
                    - Preferred size: **{mem.get('size')}**

                    _The {breed} could be a great match based on your lifestyle and preferences!_
                    """
                )

            st.markdown("---")

    st.info("Want to try different answers? Use **Reset Conversation** in the sidebar.")
