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


def _safe_rerun() -> None:
    """Handle different Streamlit versions safely."""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            # In the worst case, just continue without rerunning.
            pass


# ============================================================
# IMAGE HELPERS — map AKC names -> Maarten repo folders
# ============================================================

RAW_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "maartenvandenbroeck/Dog-Breeds-Dataset/master"
)


_SPECIAL_NAME_MAP = {
    # Common AKC "group-style" names → FCI-style base names
    "retrievers (labrador)": "labrador retriever",
    "retrievers (golden)": "golden retriever",
    "retrievers (chesapeake bay)": "chesapeake bay retriever",
    "retrievers (flat-coated)": "flat coated retriever",
    "retrievers (curly-coated)": "curly coated retriever",
    "spaniels (english springer)": "english springer spaniel",
    "spaniels (cocker)": "cocker spaniel",
    "spaniels (english cocker)": "english cocker spaniel",
    "spaniels (boykin)": "boykin spaniel",
    "spaniels (welsh springer)": "welsh springer spaniel",
    "spaniels (american water)": "american water spaniel",
    "spaniels (field)": "field spaniel",
    "spaniels (sussex)": "sussex spaniel",
    "pointers (german shorthaired)": "german short- haired pointing",
    "pointers (german wirehaired)": "german wire- haired pointing",
    # A few very common breeds where Maarten's folder name is known
    "french bulldogs": "french bulldog",
    "bulldogs": "bulldog",
    "poodles": "poodle",
    "beagles": "beagle",
    "rottweilers": "rottweiler",
    "dachshunds": "dachshund",
    "chihuahuas": "chihuahua",
    "shih tzu": "shih tzu",
    "standard schnauzers": "standard schnauzer",
    "yorkshire terriers": "yorkshire terrier",
}


def _breed_to_folder(breed_name: str) -> str:
    """
    Convert an AKC-style breed name into a folder name
    for the Dog-Breeds-Dataset repository.

    This:
    - Normalizes accents / weird spacing (e.g. 'ShihÂ Tzu' → 'shih tzu')
    - Applies a few hand-tuned mappings where AKC naming differs
    - Singularizes the last word ('Schnauzers' → 'Schnauzer')
    - Returns something like 'shih tzu dog' or 'french bulldog'
    """
    # Normalize odd unicode like Â, non-breaking spaces, accents
    text = unicodedata.normalize("NFKD", str(breed_name))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = text.replace("’", "").replace("'", "")
    text = re.sub(r"\s+", " ", text)

    # Apply explicit special mappings first
    if text in _SPECIAL_NAME_MAP:
        base = _SPECIAL_NAME_MAP[text]
    else:
        base = text
        # Singularize only the LAST word very simply
        parts = base.split()
        if parts:
            last = parts[-1]
            if last.endswith("ies"):
                last = last[:-3] + "y"
            elif last.endswith("s") and not last.endswith("ss"):
                last = last[:-1]
            parts[-1] = last
            base = " ".join(parts)

    # Many Maarten folders end with "dog", but some (e.g. french bulldog)
    # already include "bulldog" etc. We add " dog" only if it does not
    # already end with "dog".
    if not base.endswith(" dog"):
        folder = f"{base} dog"
    else:
        folder = base

    return folder


def _make_image_url(breed_name: str) -> str:
    """
    Build the raw.githubusercontent.com URL for Image_1.jpg of a breed.

    We percent-encode spaces as %20 for the URL.
    """
    folder = _breed_to_folder(breed_name)
    folder_for_url = folder.replace(" ", "%20")
    return f"{RAW_BASE_URL}/{folder_for_url}/Image_1.jpg"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        init_memory()
        st.session_state.wizard_step = 1
        # Also reset the intro flag so the greeting shows again
        st.session_state["intro_shown"] = False
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
        "**Let's start with your energy level.** Select one from the options shown in the "
        "drop-down menu below."
    )
    add_assistant_msg(intro)
    st.session_state.intro_shown = True  # only mark; rendering happens in the loop below

# Render existing messages once
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
        mem.get("size"),
    )

    if not recs:
        st.warning(
            "I couldn't find good matches with the current preferences. "
            "Try resetting the conversation and choosing slightly broader options."
        )
    else:
        st.markdown("Here are your **top 3 dog breeds** based on your choices:")

        for breed in recs:
            image_url = _make_image_url(breed)

            col1, col2 = st.columns([1, 2])

            with col1:
                # Even if the URL 404s, Streamlit will just show a broken image,
                # which is OK for the contest. No app crash.
                st.image(image_url, width=220, caption=breed)

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

