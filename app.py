"""
Streamlit app: "Choose My Dog Breed"

This app:
- Loads dog breed traits and trait descriptions from local CSV files.
- Lets users set preferences via sidebar dropdowns (Quick Match).
- Provides a simple natural-language chatbot interface.
- Recommends the top 3 matching breeds.
- Shows a sample image for each breed from the GitHub Dog-Breeds-Dataset fork.
- Links to the full folder of images for each breed on GitHub.
"""

from __future__ import annotations

import random
import textwrap
import urllib.parse
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

# GitHub repo where the images live (your fork)
GITHUB_USER = "maartenvandenbroeck"
GITHUB_REPO = "Dog-Breeds-Dataset"
GITHUB_BRANCH = "master"  # this repo uses "master", not "main"

# Base URLs for folders (web view) and raw image files
GITHUB_DATASET_BASE = (
    f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/tree/{GITHUB_BRANCH}"
)
GITHUB_RAW_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
)


# ---------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------


@st.cache_data
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load breed traits and trait description tables.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (dog_breeds, trait_descriptions)
    """
    dog_breeds = pd.read_csv("data/breed_traits.csv")
    trait_descriptions = pd.read_csv("data/trait_description.csv")

    # Convert numeric traits stored as text to floats (1–5 scale)
    numeric_cols = [
        "Affectionate With Family",
        "Good With Young Children",
        "Good With Other Dogs",
        "Shedding Level",
        "Coat Grooming Frequency",
        "Drooling Level",
        "Openness To Strangers",
        "Playfulness Level",
        "Watchdog/Protective Nature",
        "Adaptability Level",
        "Trainability Level",
        "Energy Level",
        "Barking Level",
        "Mental Stimulation Needs",
    ]
    for col in numeric_cols:
        if col in dog_breeds.columns:
            dog_breeds[col] = pd.to_numeric(dog_breeds[col], errors="coerce")

    return dog_breeds, trait_descriptions


# ---------------------------------------------------------------------
# IMAGE HELPERS (PATCHED)
# ---------------------------------------------------------------------


def _breed_folder_name(breed_name: str) -> str:
    """Convert a human breed name into the folder name used in the repo.

    The repo folders follow a pattern like:
    - "Rhodesian Ridgebacks"  -> "rhodesian ridgeback dog"
    - "Anatolian Shepherd Dogs" -> "anatolian shepherd dog"

    Args:
        breed_name: Breed name from the CSV.

    Returns:
        Folder name string (still with spaces; will be URL-encoded later).
    """
    name = breed_name.strip().lower()

    # Remove trailing "dogs" or "dog" then append " dog"
    if name.endswith("dogs"):
        name = name[:-1]  # drop the final "s"
    elif name.endswith("dog"):
        pass
    else:
        name = f"{name} dog"

    return name


def build_dataset_folder_url(breed_name: str) -> str:
    """Build the GitHub web URL for the folder containing this breed's images.

    Args:
        breed_name: Breed name from the trait table.

    Returns:
        A URL string pointing to the correct folder on GitHub.
    """
    folder = _breed_folder_name(breed_name)
    # Encode spaces and special characters for a safe URL path segment
    encoded_folder = urllib.parse.quote(folder, safe="")
    return f"{GITHUB_DATASET_BASE}/{encoded_folder}"


def get_breed_image_url(breed_name: str, index: int | None = None) -> str:
    """Build the raw image URL for Streamlit to display.

    The dataset stores about 35 images per breed, typically named "1.jpg",
    "2.jpg", ..., "35.jpg". We pick one index (or a random one) and build
    a raw.githubusercontent.com URL.

    Args:
        breed_name: Breed name from the trait table.
        index: Optional image index (1–35). If None, choose randomly.

    Returns:
        A URL string for a JPG image. If the image does not exist, the
        browser may show a broken image, but the app will still run.
    """
    if index is None:
        index = random.randint(1, 35)

    folder = _breed_folder_name(breed_name)
    encoded_folder = urllib.parse.quote(folder, safe="")
    filename = f"{index}.jpg"

    return f"{GITHUB_RAW_BASE}/{encoded_folder}/{filename}"


# ---------------------------------------------------------------------
# MATCHING LOGIC
# ---------------------------------------------------------------------


PREFERENCE_TRAITS = {
    "Energy Level": "Energy Level",
    "Good With Young Children": "Good With Young Children",
    "Shedding Level": "Shedding Level",
    "Barking Level": "Barking Level",
    "Trainability Level": "Trainability Level",
    "Affectionate With Family": "Affectionate With Family",
}


def score_breeds(
    dog_breeds: pd.DataFrame, prefs: Dict[str, int], weights: Dict[str, float]
) -> pd.DataFrame:
    """Score each breed against user preferences on a 0–100 scale.

    Args:
        dog_breeds: Full trait table.
        prefs: Mapping trait name -> desired level (1–5).
        weights: Mapping trait name -> importance weight (0–1).

    Returns:
        DataFrame sorted by descending score with columns:
        ['Breed', 'score', 'details'] where details is a dict of per-trait info.
    """
    df = dog_breeds.copy()
    total_weight = sum(weights.values()) or 1.0

    scores = []
    details_list: List[Dict[str, Dict[str, float]]] = []

    for _, row in df.iterrows():
        breed_score = 0.0
        details: Dict[str, Dict[str, float]] = {}

        for pretty_name, col_name in PREFERENCE_TRAITS.items():
            if pretty_name not in prefs:
                continue
            desired = prefs[pretty_name]
            weight = weights.get(pretty_name, 0.0)
            trait_value = row.get(col_name, np.nan)

            if np.isnan(trait_value):
                diff = 2.5  # neutral penalty if data missing
            else:
                diff = abs(trait_value - desired)

            # Max diff on a 1–5 scale is 4. Convert to a 0–1 match.
            match = max(0.0, 1.0 - diff / 4.0)
            weighted = match * weight

            breed_score += weighted
            details[pretty_name] = {
                "desired": desired,
                "actual": float(trait_value) if not np.isnan(trait_value) else np.nan,
                "match": match,
                "weight": weight,
            }

        # Convert total weighted match into 0–100
        score_pct = (breed_score / total_weight) * 100.0
        scores.append(score_pct)
        details_list.append(details)

    df["score"] = scores
    df["details"] = details_list

    return df[["Breed", "score", "details"]].sort_values("score", ascending=False)


def explain_match(details: Dict[str, Dict[str, float]]) -> List[str]:
    """Create simple bullet-point explanations from trait match details."""
    lines: List[str] = []

    for trait, info in details.items():
        match = info["match"]
        actual = info["actual"]
        desired = info["desired"]

        if np.isnan(actual):
            lines.append(f"- No data available for **{trait}**.")
            continue

        if match > 0.8:
            lines.append(
                f"- Excellent **{trait.lower()}** match (you wanted {desired}, "
                f"this breed is around {int(round(actual))})."
            )
        elif match > 0.6:
            lines.append(
                f"- Good **{trait.lower()}** match (you wanted {desired}, "
                f"this breed is about {int(round(actual))})."
            )
        elif match > 0.4:
            lines.append(
                f"- Moderate match on **{trait.lower()}** "
                f"(your preference {desired} vs. breed {int(round(actual))})."
            )
        else:
            lines.append(
                f"- This breed differs on **{trait.lower()}** "
                f"(you prefer {desired}, this breed is {int(round(actual))})."
            )

    return lines


# ---------------------------------------------------------------------
# SIMPLE CHATBOT INTENT PARSER
# ---------------------------------------------------------------------


def parse_chat_message_to_preferences(message: str) -> Dict[str, int]:
    """Very simple keyword-based parser to update preferences from chat text.

    This is *not* a real NLP model, just a friendly rules-based helper.

    Args:
        message: User message.

    Returns:
        Dict of trait -> preferred level (1–5) inferred from text.
    """
    text = message.lower()
    prefs: Dict[str, int] = {}

    # Energy
    if any(k in text for k in ["high energy", "very active", "run", "jogging"]):
        prefs["Energy Level"] = 5
    elif any(k in text for k in ["medium energy", "moderate energy"]):
        prefs["Energy Level"] = 3
    elif any(k in text for k in ["low energy", "couch", "chill", "apartment"]):
        prefs["Energy Level"] = 2

    # Kids
    if any(k in text for k in ["kids", "children", "family"]):
        prefs["Good With Young Children"] = 5
    if "no kids" in text or "no children" in text:
        prefs["Good With Young Children"] = 2

    # Shedding
    if "hypoallergenic" in text or "allergy" in text:
        prefs["Shedding Level"] = 1
    elif "okay with shedding" in text or "don't mind fur" in text:
        prefs["Shedding Level"] = 4

    # Barking
    if any(k in text for k in ["quiet", "noise sensitive", "noisy neighbors"]):
        prefs["Barking Level"] = 2
    if "guard dog" in text or "watchdog" in text:
        prefs["Watchdog/Protective Nature"] = 5

    # Trainability
    if any(k in text for k in ["first dog", "easy to train", "beginner"]):
        prefs["Trainability Level"] = 5

    return prefs


# ---------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------


def render_breed_card(
    breed_row: pd.Series,
    rank: int,
) -> None:
    """Render a single breed result card with image, score, and explanation."""
    breed_name = breed_row["Breed"]
    score = breed_row["score"]
    details = breed_row["details"]

    image_url = get_breed_image_url(breed_name)
    folder_url = build_dataset_folder_url(breed_name)

    st.subheader(f"#{rank} — {breed_name} (Match Score: {score:.1f}/100)")

    cols = st.columns([1.2, 2.8])
    with cols[0]:
        st.image(
            image_url,
            caption=breed_name,
            use_column_width=True,
        )

    with cols[1]:
        st.markdown(
            f"[View more **{breed_name}** photos in dataset]({folder_url})"
        )
        st.write("**Why this breed might fit you:**")
        for line in explain_match(details):
            st.markdown(line)

        # Short social-media-style blurb
        blurb = textwrap.fill(
            f"{breed_name} could be your next adventure buddy! 🐶 "
            f"It balances energy, trainability, and family-friendliness "
            f"based on the preferences you shared.",
            width=80,
        )
        st.write("")
        st.markdown(f"> {blurb}")


def sidebar_preference_controls() -> Tuple[Dict[str, int], Dict[str, float]]:
    """Render sidebar dropdowns and return (preferences, weights)."""
    st.sidebar.header("⚡ Quick Match Controls")

    st.sidebar.write("Choose the vibe you want, then click **Find my breeds!**")

    levels = ["No preference", "1 (Very low)", "2 (Low)", "3 (Medium)", "4 (High)", "5 (Very high)"]

    def choose_level(label: str, default: str = "No preference") -> int | None:
        choice = st.sidebar.selectbox(label, levels, index=levels.index(default))
        if choice == "No preference":
            return None
        return int(choice[0])

    prefs: Dict[str, int] = {}
    weights: Dict[str, float] = {}

    # User controls
    energy = choose_level("Energy level")
    kids = choose_level("Good with young children")
    shedding = choose_level("Shedding / allergies")
    barking = choose_level("Barking level")
    train = choose_level("Trainability / ease of training")
    affection = choose_level("Affectionate with family")

    # Assign preferences + weights (importance)
    if energy is not None:
        prefs["Energy Level"] = energy
        weights["Energy Level"] = 1.0
    if kids is not None:
        prefs["Good With Young Children"] = kids
        weights["Good With Young Children"] = 1.0
    if shedding is not None:
        prefs["Shedding Level"] = shedding
        weights["Shedding Level"] = 0.9
    if barking is not None:
        prefs["Barking Level"] = barking
        weights["Barking Level"] = 0.7
    if train is not None:
        prefs["Trainability Level"] = train
        weights["Trainability Level"] = 0.9
    if affection is not None:
        prefs["Affectionate With Family"] = affection
        weights["Affectionate With Family"] = 0.8

    if not prefs:
        # Default gentle preferences if user leaves everything as "No preference"
        prefs = {"Energy Level": 3, "Affectionate With Family": 4}
        weights = {"Energy Level": 1.0, "Affectionate With Family": 0.8}

    return prefs, weights


# ---------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------


def main() -> None:
    """Run the Streamlit app."""
    st.set_page_config(
        page_title="Choose My Dog Breed",
        page_icon="🐕",
        layout="wide",
    )

    dog_breeds, trait_descriptions = load_data()  # noqa: F841 (trait_descriptions unused for now)

    st.title("🐕 Choose My Dog Breed")
    st.markdown(
        """
Welcome to your personal **AI dog matchmaker**!

This app:
- Asks about your lifestyle and preferences,
- Matches them to real dog breed traits,
- Suggests your **top 3 breeds** with photos and explanations,
- And includes a simple **chatbot** to refine your choices.
"""
    )

    # Sidebar controls
    prefs_sidebar, weights_sidebar = sidebar_preference_controls()

    tab_quick, tab_chat = st.tabs(["⚡ Quick Match", "💬 Chatbot Mode"])

    # ------------- QUICK MATCH TAB -------------
    with tab_quick:
        st.header("⚡ Quick Match (Sidebar Controls)")
        st.write(
            "Use the controls in the **left sidebar** to describe your ideal pup, "
            "then click the button below."
        )

        if st.button("🎯 Find my top 3 breeds", type="primary"):
            results = score_breeds(dog_breeds, prefs_sidebar, weights_sidebar)
            top3 = results.head(3).reset_index(drop=True)

            st.subheader("🎉 Your Top Matches (with photos)")
            for idx, row in top3.iterrows():
                render_breed_card(row, rank=idx + 1)

    # ------------- CHATBOT TAB -------------
    with tab_chat:
        st.header("💬 Chatbot: Talk about your lifestyle")

        st.write(
            """
Tell the bot about your lifestyle and what you're looking for in a dog.
For example:

> *\"I live in an apartment, want a low-shedding, medium-energy dog that's good with kids.\"*
"""
        )

        # Keep a simple chat history in session_state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for speaker, text in st.session_state.chat_history:
            if speaker == "user":
                st.chat_message("user").markdown(text)
            else:
                st.chat_message("assistant").markdown(text)

        user_msg = st.chat_input("Tell me about yourself and your ideal dog...")
        if user_msg:
            # Show user message
            st.chat_message("user").markdown(user_msg)
            st.session_state.chat_history.append(("user", user_msg))

            # Infer preferences from this message
            inferred_prefs = parse_chat_message_to_preferences(user_msg)

            # Merge with sidebar prefs (chat overrides where it has info)
            combined_prefs = dict(prefs_sidebar)
            combined_prefs.update(inferred_prefs)

            combined_weights = dict(weights_sidebar)

            # Boost weights for any traits mentioned explicitly in chat
            for trait in inferred_prefs:
                combined_weights[trait] = max(combined_weights.get(trait, 0.6), 1.0)

            # Compute recommendations
            results = score_breeds(dog_breeds, combined_prefs, combined_weights)
            top3 = results.head(3).reset_index(drop=True)

            # Compose a short assistant reply
            first_breed = top3.loc[0, "Breed"]
            reply = (
                f"Based on what you described, **{first_breed}** looks like a strong match! "
                "Here are the top 3 breeds for you below. You can tweak the sidebar "
                "controls and send more messages to refine your results. 🐾"
            )

            st.chat_message("assistant").markdown(reply)
            st.session_state.chat_history.append(("assistant", reply))

            st.divider()
            st.subheader("🎉 Recommended breeds based on our chat")

            for idx, row in top3.iterrows():
                render_breed_card(row, rank=idx + 1)


if __name__ == "__main__":
    main()

