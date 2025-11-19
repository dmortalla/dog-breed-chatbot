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
    classify_off_topic,
)
from recommender_engine import recommend_breeds_with_cards


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

if "memory" not in st.session_state:
    init_memory()

dog_breeds, trait_descriptions = load_data()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🔄 Reset conversation"):
        st.session_state.messages = []
        init_memory()
        st.rerun()

    st.markdown("### 🧠 Current preferences")
    st.info(memory_summary())

    st.markdown("---")
    st.markdown("### 📜 Chat history")
    render_chat_history()

    st.markdown("---")
    st.caption(
        "This demo chatbot uses dog breed traits and your lifestyle "
        "to recommend real-world breeds, with images from the "
        "[Dog-Breeds-Dataset](https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset)."
    )


# ============================================================
# INITIAL GREETING
# ============================================================

if len(st.session_state.messages) == 0:
    intro = (
        "👋 **Hi there! I'm Dog Lover**, your friendly dog-match chatbot.\n\n"
        "Tell me about your **energy level**, **living space** (apartment / house with yard), "
        "**allergies or shedding concerns**, whether you have **kids**, and what **size of dog** "
        "you’d like.\n\n"
        "I’ll ask follow-up questions if needed and then recommend **three dog breeds**, "
        "each with an image and a short ‘social-post-style’ description."
    )
    add_assistant_msg(intro)
    st.chat_message("assistant").markdown(intro)


# ============================================================
# MAIN MESSAGE HANDLER
# ============================================================

def process_message(user_msg: str):
    """Handle a single user message: classify, parse, update memory, maybe recommend breeds."""
    # 1. Off-topic guard
    if classify_off_topic(user_msg):
        reply = (
            "😅 I’m sorry, but that’s beyond what I can do.\n\n"
            "Let’s get back to how I can help you pick the **best dog** for you — "
            "tell me more about your lifestyle, home, allergies, or family."
        )
        add_assistant_msg(reply)
        st.chat_message("assistant").markdown(reply)
        return

    # 2. Extract traits from natural language
    new_traits = extract_traits(user_msg)

    # 3. Update memory only with traits actually present in this message
    for key, value in new_traits.items():
        update_memory(key, value)

    # 4. If we didn’t learn anything, ask for more specific info
    if not new_traits:
        reply = (
            "Thanks! Could you tell me a bit more about your **lifestyle and preferences**?\n\n"
            "For example, you can mention:\n"
            "• your energy level (low / medium / high)\n"
            "• your living space (small apartment / apartment / house with yard)\n"
            "• allergies or shedding (“low shedding” / “hypoallergenic”)\n"
            "• whether you have kids\n"
            "• whether you want a small / medium / large dog"
        )
        add_assistant_msg(reply)
        st.chat_message("assistant").markdown(reply)
        return

    # 5. Check if we have enough info to recommend breeds
    mem = st.session_state.memory
    ready = all([
        mem.get("energy"),
        mem.get("living"),
        mem.get("allergies"),
        mem.get("children"),
        mem.get("size"),
    ])

    if not ready:
        reply = (
            "Great, thanks for that! 😊\n\n"
            "Tell me a bit more — maybe about your **home**, **allergies**, "
            "**kids**, or **preferred dog size**, and I’ll keep refining my match."
        )
        add_assistant_msg(reply)
        st.chat_message("assistant").markdown(reply)
        return

    # 6. We have enough info → show summary + recommendations
    summary = (
        "✨ **Here’s what I currently know about you:**\n\n"
        f"{memory_summary()}\n\n"
        "If I missed something or you’d like to adjust, just tell me — "
        "otherwise, here are your matches!"
    )
    add_assistant_msg(summary)
    st.chat_message("assistant").markdown(summary)

    # 7. Compute top-3 breeds + cards (with images + social-style text)
    cards = recommend_breeds_with_cards(
        dog_breeds,
        energy=mem.get("energy"),
        living=mem.get("living"),
        allergies=mem.get("allergies"),
        children=mem.get("children"),
        size=mem.get("size"),
    )

    if not cards:
        msg = (
            "Hmm… I couldn’t find strong matches with what I know so far.\n\n"
            "Try giving me a bit more detail about your lifestyle, allergies, "
            "and what you want in a dog."
        )
        add_assistant_msg(msg)
        st.chat_message("assistant").markdown(msg)
        return

    intro_msg = "🐾 **Here are the top dog breeds that match your preferences:**"
    add_assistant_msg(intro_msg)
    st.chat_message("assistant").markdown(intro_msg)

    # 8. Render each recommendation as a card with image + explanation
    for card in cards:
        breed = card["breed"]
        img_url = card["image_url"]
        summary_text = card["summary"]
        dataset_link = card["dataset_link"]

        msg_block = st.chat_message("assistant")
        msg_block.markdown(f"### 🐕 {breed}")

        if img_url:
            msg_block.image(
                img_url,
                caption=f"{breed} — example image from the dataset",
                use_column_width=True,
            )
        else:
            msg_block.caption(
                "Image unavailable for this breed from the external dataset."
            )

        msg_block.markdown(summary_text)
        msg_block.markdown(
            f"[View more **{breed}** photos on the dataset]({dataset_link})"
        )


# ============================================================
# CHAT INPUT
# ============================================================

user_msg = st.chat_input("Tell me about your lifestyle, home, and ideal dog...")

if user_msg:
    add_user_msg(user_msg)
    st.chat_message("user").markdown(user_msg)
    process_message(user_msg)
