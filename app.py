import streamlit as st
from streamlit_mic_recorder import mic_recorder
import time
import random
import requests
from io import BytesIO
from PIL import Image

from trait_engine import parse_preferences
from recommender_engine import recommend_breeds
from chatbot_utils import (
    add_user_msg,
    add_assistant_msg,
    load_data,
)

# -------------------------------
# THEME
# -------------------------------

def apply_theme(theme: str) -> None:
    if theme == "dark":
        css = """
        <style>
        body {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            color: #f8fafc !important;
        }
        [data-testid="stChatMessage"] {
            margin-bottom: 0.3rem;
        }
        [data-testid="stChatMessage"] > div {
            border-radius: 16px;
            padding: 10px 14px;
        }
        [data-testid="stChatMessage-user"] > div {
            background: #334155 !important;
            color: #f1f5f9 !important;
        }
        [data-testid="stChatMessage-assistant"] > div {
            background: #0f172a !important;
            color: #f1f5f9 !important;
        }
        .stTextInput input, .stChatInput textarea {
            background: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #475569 !important;
        }
        </style>
        """
    else:
        css = """
        <style>
        body { background-color: #ffffff !important; color: #111827 !important; }
        [data-testid="stSidebar"] { background-color: #f9fafb !important; }
        [data-testid="stChatMessage"] { margin-bottom: 0.3rem; }
        [data-testid="stChatMessage"] > div {
            border-radius: 16px; padding: 10px 14px;
        }
        [data-testid="stChatMessage-user"] > div { background: #e5f3ff !important; }
        [data-testid="stChatMessage-assistant"] > div { background: #f3f4f6 !important; }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


# -------------------------------
# SAMPLE DOG FACTS
# -------------------------------
DOG_FACTS = [
    "Dogs can learn over 100 words 🐶🧠",
    "Some dogs can smell medical conditions 👃✨",
    "Greyhounds can reach speeds of 45 mph! ⚡",
    "A dog's nose print is as unique as a fingerprint.",
]


# -------------------------------
# REPEAT TRAIT ACKNOWLEDGEMENT
# -------------------------------

def detect_repeated_traits(user_text: str, prefs: dict, new_prefs: dict) -> str:
    replies = {
        "energy": "I remember your preferred energy level — thanks for confirming! ⚡👌",
        "home": "I've already noted your living situation — all good! 🏡",
        "allergies": "Got it — you mentioned shedding earlier, and I’ve kept that in mind 👌",
        "kids": "You already told me about children — thanks for confirming! 🧒🐶",
    }
    msgs = []
    for trait in new_prefs:
        if trait in prefs and replies.get(trait):
            msgs.append(replies[trait])
    return "\n".join(msgs)


# -------------------------------
# OFF TOPIC CLASSIFIER (ENHANCED)
# -------------------------------

def classify_off_topic(text: str, extracted: dict) -> bool:
    t = text.lower().strip()

    if extracted:
        return False

    confirmations = [
        "yes", "yep", "yeah", "sure", "ok", "okay",
        "sounds good", "correct", "right", "fine"
    ]
    if any(t.startswith(c) for c in confirmations):
        return False

    dog_keywords = [
        "dog", "puppy", "breed", "shedding", "hair", "fur",
        "energy", "calm", "quiet", "active", "yard",
        "apartment", "house", "kids", "children",
        "family", "allergy", "hypoallergenic",
    ]
    if any(k in t for k in dog_keywords):
        return False

    return True


# -------------------------------
# MEMORY SUMMARY (ENHANCED)
# -------------------------------

def render_memory_summary(prefs: dict) -> str:
    text = ["Here’s what I currently know about you so far: 👇\n"]

    if "energy" in prefs:
        em = {1: "low", 3: "medium", 5: "high"}
        text.append(f"• Preferred energy level: **{em[prefs['energy']]}**")

    if "home" in prefs:
        hm = {1: "small apartment", 2: "apartment", 3: "house with a yard"}
        text.append(f"• Living situation: **{hm[prefs['home']]}**")

    if "allergies" in prefs:
        am = {1: "hypoallergenic", 2: "low-shedding", 4: "shedding ok"}
        text.append(f"• Allergy/shedding preference: **{am[prefs['allergies']]}**")

    if "kids" in prefs:
        km = {1: "yes", 0: "no"}
        text.append(f"• Needs to be good with kids: **{km[prefs['kids']]}**")

    text.append("\nIf I missed something, please tell me now. 🐶✨")

    return "\n".join(text)


# -------------------------------
# IMAGE LOADER
# -------------------------------

def load_breed_image(breed: str) -> Image.Image:
    folder = breed.replace(" ", "_")
    url = f"https://raw.githubusercontent.com/maartenvandenbroeck/Dog-Breeds-Dataset/main/{folder}/Image_1.jpg"
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content))
        return img
    except:
        return None


# -------------------------------
# SIDEBAR
# -------------------------------

def render_sidebar():
    st.sidebar.title("🐾 Dog Lover Settings")

    theme_choice = st.sidebar.radio(
        "Theme:", ["light", "dark"], index=0
    )
    apply_theme(theme_choice)

    st.sidebar.markdown("### 🎙 Voice Input")
    st.sidebar.info("Tap to record your message")
    voice = mic_recorder(start_prompt="Start recording", stop_prompt="Stop", just_once=False)
    return voice


# -------------------------------
# TYPING SIMULATION
# -------------------------------

def typing(msg: str):
    add_assistant_msg("…")
    time.sleep(0.15)
    st.session_state.messages.pop()  # remove dots
    add_assistant_msg(msg)


# -------------------------------
# APP MAIN
# -------------------------------

def main():
    st.title("🐶 Dog Lover — Your Personalized Dog Matchmaker")

    voice_text = render_sidebar()

    # Init states
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.preferences = {}
        st.session_state.awaiting_final_confirmation = False

        intro = (
            "Hi there! I'm **Dog Lover**, your friendly canine matchmaker. 🐾\n\n"
            "Tell me about your lifestyle and what you're hoping for in a dog. "
            "I'll ask questions only if needed."
        )
        add_assistant_msg(intro)

    # Display history
    for role, content in st.session_state.messages:
        if role == "user":
            st.chat_message("user").write(content)
        else:
            st.chat_message("assistant").write(content)

    # Process voice
    if voice_text:
        user_msg = voice_text["text"]
    else:
        user_msg = st.chat_input("Type something about your dream dog…")

    if not user_msg:
        return

    add_user_msg(user_msg)

    # Handle confirmation stage
    if st.session_state.awaiting_final_confirmation:
        if any(x in user_msg.lower() for x in ["yes", "correct", "go ahead", "proceed"]):
            st.session_state.awaiting_final_confirmation = False
        else:
            added = parse_preferences(user_msg)
            if added:
                st.session_state.preferences.update(added)
                typing("Thanks! Updated your preferences. 👍")
            else:
                typing("No worries — I’ll proceed.")
            st.session_state.awaiting_final_confirmation = False

    # Extract new traits
    new_prefs = parse_preferences(user_msg)

    # Off-topic
    if classify_off_topic(user_msg, new_prefs):
        typing("I’m sorry, but that’s beyond what I can help with. Let’s get back to finding your perfect dog! 🐶")
        return

    # Repeated traits
    repeat_msg = detect_repeated_traits(user_msg, st.session_state.preferences, new_prefs)
    if repeat_msg:
        typing(repeat_msg)

    # Update traits
    st.session_state.preferences.update(new_prefs)

    prefs = st.session_state.preferences

    # Required traits to recommend
    REQUIRED = ["energy", "home", "allergies", "kids"]
    if all(k in prefs for k in REQUIRED):

        summary = render_memory_summary(prefs)
        typing(summary)

        st.session_state.awaiting_final_confirmation = True
        return

    # Ask next missing trait
    if "home" not in prefs:
        typing("Let's talk about your living situation. Do you live in a small apartment, apartment, or a house with a yard?")
        return

    if "energy" not in prefs:
        typing("How active would you like your dog to be? Low energy, medium, or high-energy companion?")
        return

    if "allergies" not in prefs:
        typing("Let’s now consider allergies. Do you prefer a hypoallergenic or low-shedding dog?")
        return

    if "kids" not in prefs:
        typing("Do you need your dog to be especially good with young children?")
        return

    # Recommendations
    if not st.session_state.awaiting_final_confirmation:
        matches = recommend_breeds(
            st.session_state.data_breeds,
            prefs
        )

        if not matches:
            typing("I couldn’t find a perfect match, but I can try again if you adjust your preferences.")
            return

        typing("Great! Based on everything you shared, here are your top dog matches 🐾✨")

        for breed in matches:
            st.subheader(breed)
            img = load_breed_image(breed)
            if img:
                st.image(img, use_column_width=True)
            else:
                st.info("(Image unavailable)")

            st.markdown(f"**{random.choice(DOG_FACTS)}**")

        # Reset for next conversation
        st.session_state.preferences = {}
        st.session_state.awaiting_final_confirmation = False


# -------------------------------
# Load Data Once
# -------------------------------

if "data_breeds" not in st.session_state:
    dog_breeds, trait_descriptions = load_data()
    st.session_state.data_breeds = dog_breeds

# -------------------------------
main()

