"""Streamlit app for the Dog Breed Chatbot / Recommender.

This app:
- Loads dog breed traits from CSV.
- Lets the user set lifestyle preferences in the sidebar.
- Computes similarity scores for all breeds.
- Shows the top 3 matches with photos and dataset links.
"""

from typing import Dict

import pandas as pd
import streamlit as st

from recommender_engine import (
    clean_breed_traits,
    compute_match_scores,
    get_breed_image_url,
    build_image_url,
)


# -------------------------------------------------------------------
# Data loading
# -------------------------------------------------------------------

@st.cache_data
def load_breed_data() -> pd.DataFrame:
    """Load the dog breed trait data from CSV."""
    return pd.read_csv("data/breed_traits.csv")


# -------------------------------------------------------------------
# User profile construction
# -------------------------------------------------------------------

def build_user_profile() -> Dict[str, int]:
    """Collect user preferences from sidebar sliders.

    Returns:
        Dictionary mapping trait names to a 1–5 integer score.
    """
    st.sidebar.header("🐾 Your Lifestyle & Preferences")

    user_profile = {
        "Energy Level": st.sidebar.slider(
            "Your energy level", min_value=1, max_value=5, value=3
        ),
        "Good With Young Children": st.sidebar.slider(
            "How important is being good with children?",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Good With Other Dogs": st.sidebar.slider(
            "How important is being friendly with other dogs?",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Shedding Level": st.sidebar.slider(
            "Shedding tolerance (1 = very low, 5 = don't mind fur everywhere)",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Barking Level": st.sidebar.slider(
            "Barking tolerance (1 = very quiet, 5 = lots of barking)",
            min_value=1,
            max_value=5,
            value=3,
        ),
        "Openness To Strangers": st.sidebar.slider(
            "Do you prefer friendly or more reserved dogs?",
            min_value=1,
            max_value=5,
            value=3,
        ),
    }

    st.sidebar.markdown(
        "_Tip: 1 means “very low / not important”, 5 means “very high / very important”._"
    )

    return user_profile


# -------------------------------------------------------------------
# Display helpers
# -------------------------------------------------------------------

def display_breed_card(
    rank: int,
    breed: str,
    score: float,
    row: pd.Series,
) -> None:
    """Render a single result card for a breed.

    Args:
        rank: Rank (1, 2, 3) in the recommendation list.
        breed: Name of the breed.
        score: Match score (0–100).
        row: The full row from the cleaned DataFrame for that breed.
    """
    st.subheader(f"#{rank} — {breed}  (Match Score: {score:.1f} / 100)")

    # Image and link to more photos
    image_url = get_breed_image_url(breed)
    folder_url = build_image_url(breed)
    st.image(image_url, width=320, caption=breed)
    st.markdown(
        f"[View more **{breed}** photos in the dataset]({folder_url})",
        unsafe_allow_html=False,
    )

    # Simple explanation using a few key traits
    st.markdown("**Why this breed might fit you:**")
    bullet_points = []

    def trait_sentence(col_name: str, friendly_name: str) -> None:
        if col_name in row and pd.notna(row[col_name]):
            bullet_points.append(
                f"- {friendly_name}: {int(row[col_name])} / 5"
            )

    trait_sentence("Energy Level", "Energy level")
    trait_sentence("Good With Young Children", "Good with children")
    trait_sentence("Good With Other Dogs", "Good with other dogs")
    trait_sentence("Shedding Level", "Shedding level")
    trait_sentence("Barking Level", "Barking level")

    if bullet_points:
        st.markdown("\n".join(bullet_points))

    st.markdown("---")


# -------------------------------------------------------------------
# Main app
# -------------------------------------------------------------------

def main() -> None:
    """Main entry point for the Streamlit app."""
    st.set_page_config(
        page_title="Choose My Dog Breed",
        page_icon="🐕",
        layout="centered",
    )

    st.title("🐕 Choose My Dog Breed")
    st.write(
        "Describe your lifestyle and preferences on the left, "
        "then click the button to see your top dog breed matches."
    )

    # Load and clean data
    raw_df = load_breed_data()
    clean_df = clean_breed_traits(raw_df)

    # Build user profile from sidebar
    user_profile = build_user_profile()

    st.markdown("---")
    st.header("🔍 Find Your Best Matches")

    if st.button("✨ Show My Top 3 Breeds"):
        # Compute scores
        scored = compute_match_scores(clean_df, user_profile)
        top3 = scored.head(3)

        st.markdown("## 🎯 Your Top Matches (with photos)")

        for rank, (_, row) in enumerate(top3.iterrows(), start=1):
            breed = row["Breed"]
            score = row["score"]
            display_breed_card(rank, breed, score, row)

    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit")


# -------------------------------------------------------------------
# Script entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    main()

