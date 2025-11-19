import streamlit as st
import pandas as pd
import time


# ============================================================
# MESSAGE HANDLING
# ============================================================

def add_user_msg(text: str):
    """Store a user message in session memory."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("user", text))


def add_assistant_msg(text: str):
    """Store an assistant message in session memory."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("assistant", text))


# ============================================================
# LOAD DATASETS (cached)
# ============================================================

@st.cache_data
def load_data():
    """Load trait and breed datasets."""
    dog_breeds = pd.read_csv("data/breed_traits.csv")
    trait_descriptions = pd.read_csv("data/trait_description.csv")
    return dog_breeds, trait_descriptions


# ============================================================
# CHAT HISTORY
# ============================================================

def render_chat_history():
    """Show collapsible chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.expander("📜 Chat History", expanded=False):
        for role, content in st.session_state.messages:
            st.chat_message(role).write(content)


# ============================================================
# MEMORY UTILITIES
# ============================================================

def init_memory():
    """Ensure memory dictionary exists."""
    if "memory" not in st.session_state:
        st.session_state.memory = {
            "energy": None,
            "living": None,
            "allergies": None,
            "children": None,
            "size": None,
            "notes": [],
        }


def update_memory(key: str, value):
    """Update one memory field if user answers."""
    init_memory()
    if value:
        st.session_state.memory[key] = value


def memory_summary():
    """Return readable natural-language memory summary."""
    m = st.session_state.memory

    summary_parts = []

    if m.get("energy"):
        summary_parts.append(f"Energy level: {m['energy']}")
    if m.get("living"):
        summary_parts.append(f"Living situation: {m['living']}")
    if m.get("allergies"):
        summary_parts.append(f"Allergies preference: {m['allergies']}")
    if m.get("children"):
        summary_parts.append(f"Good with children: {m['children']}")
    if m.get("size"):
        summary_parts.append(f"Preferred dog size: {m['size']}")

    if m.get("notes"):
        summary_parts.extend(m["notes"])

    if not summary_parts:
        return "I haven't collected any preferences yet."

    return " • " + "\n • ".join(summary_parts)


# ============================================================
# PARSING HELPERS (simple keyword-based parser)
# ============================================================

def parse_energy(message: str):
    msg = message.lower()
    if "low" in msg:
        return "low"
    if "medium" in msg:
        return "medium"
    if "high" in msg:
        return "high"
    return None


def parse_living(message: str):
    msg = message.lower()
    if "small" in msg:
        return "small apartment"
    if "apartment" in msg:
        return "standard apartment"
    if "yard" in msg:
        return "house with yard"
    return None


def parse_allergies(message: str):
    msg = message.lower()
    if "hypo" in msg:
        return "hypoallergenic"
    if "shed" in msg or "low-shed" in msg or "low shed" in msg:
        return "low-shedding"
    return None


def parse_children(message: str):
    msg = message.lower()
    if "yes" in msg or "yep" in msg or "sure" in msg:
        return "yes"
    if "no" in msg:
        return "no"
    return None


def parse_size(message: str):
    msg = message.lower()
    if "small dog" in msg or "small" in msg:
        return "small"
    if "medium dog" in msg or "medium" in msg:
        return "medium"
    if "large dog" in msg or "big dog" in msg or "large" in msg:
        return "large"
    return None


def extract_traits(message: str):
    """Return a dict of parsed traits detected from the message."""
    return {
        "energy": parse_energy(message),
        "living": parse_living(message),
        "allergies": parse_allergies(message),
        "children": parse_children(message),
        "size": parse_size(message),
    }


def typing_response(text: str, delay: float = 0.02):
    """
    Simulate a typing animation for assistant messages.

    Args:
        text (str): The message to display.
        delay (float): Delay between characters.
    """
    placeholder = st.empty()
    typed = ""

    for char in text:
        typed += char
        placeholder.markdown(typed)
        time.sleep(delay)

    return typed


# ============================================================
# OFF-TOPIC DETECTION
# ============================================================

NON_DOG_KEYWORDS = [
    "bitcoin", "crypto", "stocks", "cooking", "recipe", "weather",
    "politics", "election", "war", "galaxy", "math", "code", "programming"
]

def classify_off_topic(message: str):
    """Return True if message is unrelated to dogs or lifestyle."""
    msg = message.lower()

    # If message contains dog traits — it's IN topic
    if any(word in msg for word in ["dog", "pup", "breed", "shedding", "children", "yard", "apartment", "energy"]):
        return False

    # Hard exclusion — clearly off-topic
    if any(word in msg for word in NON_DOG_KEYWORDS):
        return True

    # A short yes/no or phrase responding to a question is considered ON TOPIC
    if msg.strip() in ["yes", "no", "sure", "ok", "okay", "yep", "yeah", "fine"]:
        return False

    # Default: consider it ON topic (safe)
    return False
