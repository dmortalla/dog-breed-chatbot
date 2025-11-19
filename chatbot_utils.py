import streamlit as st
import pandas as pd
import time


# ============================================================
# MESSAGE HANDLING
# ============================================================

def add_user_msg(text: str):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("user", text))


def add_assistant_msg(text: str):
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("assistant", text))


# ============================================================
# LOAD DATASETS (cached)
# ============================================================

@st.cache_data
def load_data():
    dog_breeds = pd.read_csv("data/breed_traits.csv")
    trait_descriptions = pd.read_csv("data/trait_description.csv")
    return dog_breeds, trait_descriptions


# ============================================================
# CHAT HISTORY
# ============================================================

def render_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.expander("📜 Chat History", expanded=False):
        for role, content in st.session_state.messages:
            st.chat_message(role).write(content)


# ============================================================
# MEMORY UTILITIES
# ============================================================

def init_memory():
    if "memory" not in st.session_state:
        st.session_state.memory = {
            "energy": None,
            "living": None,
            "allergies": None,
            "children": None,
            "size": None,
        }


def update_memory(key: str, value):
    if value:
        st.session_state.memory[key] = value


def memory_summary():
    m = st.session_state.memory
    parts = []

    if m.get("energy"):
        parts.append(f"Energy: {m['energy']}")
    if m.get("living"):
        parts.append(f"Living: {m['living']}")
    if m.get("allergies"):
        parts.append(f"Allergies: {m['allergies']}")
    if m.get("children"):
        parts.append(f"Children: {m['children']}")
    if m.get("size"):
        parts.append(f"Size: {m['size']}")

    if not parts:
        return "No preferences collected yet."

    return " • " + "\n • ".join(parts)


# ============================================================
# TYPING EFFECT
# ============================================================

def typing_response(text: str, delay: float = 0.02):
    placeholder = st.empty()
    typed = ""
    for c in text:
        typed += c
        placeholder.markdown(typed)
        time.sleep(delay)
    return typed


# ============================================================
# OFF-TOPIC FILTER
# ============================================================

NON_DOG_KEYWORDS = [
    "bitcoin", "crypto", "stocks", "recipe", "cooking",
    "politics", "election", "war", "galaxy", "math", "code",
    "programming"
]

def classify_off_topic(message: str):
    msg = message.lower().strip()

    if msg in ["yes", "no", "sure", "ok", "okay", "yep", "yeah"]:
        return False

    dog_terms = [
        "dog", "puppy", "breed", "shedding", "children",
        "apartment", "yard", "energy", "allerg"
    ]

    if any(t in msg for t in dog_terms):
        return False

    if any(k in msg for k in NON_DOG_KEYWORDS):
        return True

    return True
