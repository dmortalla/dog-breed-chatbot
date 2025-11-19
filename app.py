import streamlit as st
from trait_engine import extract_traits_from_message, merge_traits, classify_off_topic
from chatbot_utils import typing_response
from recommender_engine import recommend_breeds
import random

st.set_page_config(
    page_title="Dog Lover Chatbot",
    page_icon="🐶",
    layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "traits" not in st.session_state:
    st.session_state.traits = {}

if "awaiting" not in st.session_state:
    st.session_state.awaiting = None

if "theme" not in st.session_state:
    st.session_state.theme = "light"

if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""

if "memory_acknowledged" not in st.session_state:
    st.session_state.memory_acknowledged = False

# -----------------------------
# SIDEBAR (RESTORED)
# -----------------------------
with st.sidebar:
    st.markdown("## 🐾 Dog Lover Settings")

    theme_choice = st.radio("Theme:", ["light", "dark"], index=0 if st.session_state.theme == "light" else 1)
    st.session_state.theme = theme_choice

    st.markdown("### 🎙 Voice Input")

    try:
        import streamlit_mic_recorder
        audio = streamlit_mic_recorder.mic_recorder(
            start_prompt="Tap to record your message",
            stop_prompt="Recording...",
            use_container_width=True
        )
        if audio:
            st.session_state.voice_input = audio
    except Exception:
        st.warning("🎤 Voice input unavailable (package missing). Install `streamlit-mic-recorder` to enable it.")

    if st.button("🔄 Reset Conversation"):
        st.session_state.messages = []
        st.session_state.traits = {}
        st.session_state.awaiting = None
        st.session_state.memory_acknowledged = False
        st.experimental_rerun()

if st.session_state.theme == "dark":
    st.markdown("""
        <style>
        body, .stApp { background-color: #111 !important; color: #EEE !important; }
        .stChatMessage { background-color: #222 !important; }
        </style>
    """, unsafe_allow_html=True)

st.markdown("# 🐶 Dog Lover Chatbot — Find Your Perfect Dog Breed!")
st.markdown("Tell me about your lifestyle and preferences. I’ll match you with the perfect dog!")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

DOG_FACTS = [
    "A dog's nose print is unique—just like a human fingerprint.",
    "Dogs can learn more than 1000 words.",
    "Some dogs can smell medical conditions like seizures or diabetes.",
    "Greyhounds can reach speeds up to 45 mph.",
]

# -----------------------------
# MAIN LOGIC
# -----------------------------
def process_message(user_msg: str):

    if classify_off_topic(user_msg):
        st.session_state.messages.append({
            "role": "assistant",
            "content": "I’m sorry, but that’s a bit outside what I can help with. Let’s get back to finding you the perfect dog. 🐾"
        })
        return

    new_traits = extract_traits_from_message(user_msg)

    if new_traits:
        duplicates = [k for k in new_traits if k in st.session_state.traits]
        st.session_state.traits = merge_traits(st.session_state.traits, new_traits)

        if duplicates:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Got it — you mentioned **{', '.join(duplicates)}** earlier, and I’ve kept that in mind 👌."
            })

    t = st.session_state.traits

    if "energy" not in t:
        st.session_state.awaiting = "energy"
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Awesome! Let’s start with **energy level**.\n\nWould your ideal dog be **low**, **medium**, or **high** energy? 🐕⚡"
        })
        return

    if "living_space" not in t:
        st.session_state.awaiting = "living_space"
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Great — I’ve already noted your living situation. 🏡\n\nWhere do you live: **small apartment**, **standard apartment**, or **house with a yard**?"
        })
        return

    if "shedding" not in t:
        st.session_state.awaiting = "shedding"
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Let’s now consider **allergies**.\n\nDo you prefer **low-shedding** or **hypoallergenic** dogs? 🌿🐕"
        })
        return

    if "children" not in t:
        st.session_state.awaiting = "children"
        st.session_state.messages.append({
            "role": "assistant",
            "content": "The presence of **children** could be a factor.\n\nShould your dog be especially **good with young children**? (yes/no) 👶🐶"
        })
        return

    if not st.session_state.memory_acknowledged:
        summary = "\n".join([f"- **{k}**: {v}" for k, v in st.session_state.traits.items()])
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Here’s what I currently know about you:\n\n{summary}\n\nIf I missed anything, please tell me now. 😊"
        })
        st.session_state.memory_acknowledged = True
        return

    score_list = recommend_breeds(st.session_state.traits)

    if not score_list:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hmm… I couldn’t find any breed that fits all that. Try adjusting one preference?"
        })
        return

    st.session_state.messages.append({
        "role": "assistant",
        "content": "Awesome, I think I have enough information now. 🐶✨\n\nHere are your top matches:"
    })

    for name, score, img_url in score_list[:3]:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"### 🐕 **{name}** — Match Score: **{score:.1f}/100**\n\n![dog]({img_url})"
        })

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"**Bonus dog fact:** {random.choice(DOG_FACTS)}"
    })

# -----------------------------
# CHAT INPUT
# -----------------------------
user_msg = st.chat_input("Tell me about your lifestyle or your ideal dog...")

if st.session_state.voice_input:
    user_msg = st.session_state.voice_input
    st.session_state.voice_input = ""

if user_msg:
    st.session_state.messages.append({"role": "user", "content": user_msg})
    process_message(user_msg)
    st.experimental_rerun()
