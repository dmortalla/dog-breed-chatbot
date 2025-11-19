import streamlit as st
import pandas as pd
import time


# ============================================================
# MESSAGE HANDLING
# ============================================================

def add_user_msg(text: str) -> None:
    """Store a user message in session memory."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("user", text))


def add_assistant_msg(text: str) -> None:
    """Store an assistant message in session memory."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append(("assistant", text))


# ============================================================
# DATA LOADING
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

def render_chat_history() -> None:
    """Show collapsible chat history."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.expander("📜 Expand full chat history", expanded=False):
        for role, content in st.session_state.messages:
            st.chat_message(role).write(content)


# ============================================================
# MEMORY UTILITIES
# ============================================================

def init_memory() -> None:
    """Ensure preference memory exists in session state."""
    if "memory" not in st.session_state:
        st.session_state.memory = {
            "energy": None,     # low / medium / high
            "living": None,     # small apartment / apartment / house with yard
            "allergies": None,  # hypoallergenic / low-shedding
            "children": None,   # yes / no
            "size": None,       # small / medium / large
        }


def update_memory(key: str, value: str) -> None:
    """Update a memory field only when we have a non-empty value."""
    init_memory()
    if value:
        st.session_state.memory[key] = value


def memory_summary() -> str:
    """Return a readable summary of what we know so far."""
    m = st.session_state.memory

    parts = []

    if m.get("energy"):
        parts.append(f"Energy level: **{m['energy']}**")
    if m.get("living"):
        parts.append(f"Living situation: **{m['living']}**")
    if m.get("allergies"):
        parts.append(f"Allergy / shedding preference: **{m['allergies']}**")
    if m.get("children"):
        parts.append(f"Good with children: **{m['children']}**")
    if m.get("size"):
        parts.append(f"Preferred dog size: **{m['size']}**")

    if not parts:
        return "I haven’t collected any preferences yet."

    return "\n".join(f"• {p}" for p in parts)


# ============================================================
# PARSING HELPERS
# ============================================================

def parse_energy(msg: str):
    if "low energy" in msg or "very calm" in msg or "calm dog" in msg:
        return "low"
    if "medium energy" in msg or "moderate energy" in msg:
        return "medium"
    if "high energy" in msg or "very active" in msg or "energetic" in msg:
        return "high"

    if " low " in f" {msg} ":
        return "low"
    if " medium " in f" {msg} ":
        return "medium"
    if " high " in f" {msg} ":
        return "high"
    return None


def parse_living(msg: str):
    if "small apartment" in msg or "tiny apartment" in msg or "studio" in msg:
        return "small apartment"
    if "apartment" in msg:
        return "apartment"
    if "yard" in msg or "garden" in msg or "house with yard" in msg:
        return "house with yard"
    return None


def parse_allergies(msg: str):
    if "hypoallergenic" in msg:
        return "hypoallergenic"

    low_shed_patterns = [
        "low-shedding",
        "low shedding",
        "doesn't shed much",
        "doesnt shed much",
        "little shedding",
        "minimal shedding",
        "hardly sheds",
        "barely sheds",
    ]
    if any(p in msg for p in low_shed_patterns):
        return "low-shedding"

    if "shedding is fine" in msg or "i don't mind shedding" in msg:
        return "no special requirement"

    return None


def parse_children(msg: str):
    # Only interpret yes/no for children if kids/children are mentioned
    if "kids" in msg or "children" in msg:
        if "no kids" in msg or "no children" in msg or "not good with kids" in msg:
            return "no"
        if "good with kids" in msg or "good with children" in msg:
            return "yes"
        if "yes" in msg:
            return "yes"
        if "no" in msg:
            return "no"
    return None


def parse_size(msg: str):
    if "small dog" in msg or "small breed" in msg:
        return "small"
    if "medium dog" in msg or "medium breed" in msg:
        return "medium"
    if "large dog" in msg or "big dog" in msg or "large breed" in msg:
        return "large"

    # fallback: single word hints
    if " small " in f" {msg} ":
        return "small"
    if " medium " in f" {msg} ":
        return "medium"
    if " large " in f" {msg} " or " big " in f" {msg} ":
        return "large"

    return None


def extract_traits(message: str):
    """
    Extract only the traits mentioned in the user message.

    Returns:
        dict: Only keys with detected values (no None values).
    """
    msg = str(message).lower().strip()

    traits = {}
    energy = parse_energy(msg)
    living = parse_living(msg)
    allergies = parse_allergies(msg)
    children = parse_children(msg)
    size = parse_size(msg)

    if energy:
        traits["energy"] = energy
    if living:
        traits["living"] = living
    if allergies:
        traits["allergies"] = allergies
    if children:
        traits["children"] = children
    if size:
        traits["size"] = size

    return traits


# ============================================================
# OFF-TOPIC DETECTION
# ============================================================

NON_DOG_KEYWORDS = [
    "bitcoin", "crypto", "stocks", "stock market",
    "recipe", "cooking", "bake", "weather",
    "politics", "election", "war",
    "galaxy", "universe",
    "math problem", "equation", "code this", "programming",
]


def classify_off_topic(message: str) -> bool:
    """
    Return True only if the message is clearly unrelated to dogs / lifestyle.

    Simple confirmations, short answers, or trait-related replies are treated as on-topic.
    """
    msg = str(message).lower().strip()

    # Obvious dog / lifestyle keywords → on-topic
    dog_keywords = [
        "dog", "pup", "puppy", "breed",
        "shedding", "shed", "fur", "hair",
        "energy", "calm", "active",
        "apartment", "yard", "garden", "house",
        "kids", "children", "family",
        "allergy", "allergies", "hypoallergenic",
        "small dog", "large dog", "medium dog",
    ]
    if any(k in msg for k in dog_keywords):
        return False

    # Confirmation-style replies → on-topic
    confirmations = ["yes", "no", "sure", "ok", "okay", "yep", "yeah", "fine"]
    if msg in confirmations:
        return False

    # Obvious unrelated topics → off-topic
    if any(word in msg for word in NON_DOG_KEYWORDS):
        return True

    # Default: treat as on-topic to avoid being too strict
    return False


# ============================================================
# OPTIONAL TYPING EFFECT (currently unused by app)
# ============================================================

def typing_response(text: str, delay: float = 0.02) -> str:
    """Simulate a typing animation for assistant messages."""
    placeholder = st.empty()
    typed = ""

    for char in text:
        typed += char
        placeholder.markdown(typed)
        time.sleep(delay)

    return typed
