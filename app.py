import streamlit as st
import pandas as pd

from recommender_engine import (
    clean_breed_traits,
    compute_match_scores,
    get_breed_image_url,
    build_image_url,
)


# -------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    """Load the dog breed trait CSV files."""
    dog_breeds = pd.read_csv("data/breed_traits.csv")
    trait_desc = pd.read_csv("data/trait_description.csv")
    return dog_breeds, trait_desc


# -------------------------------------------------------------------
# Build user profile from sidebar sliders
# -------------------------------------------------------------------
def build_user_profile():
    """
    Collect user lifestyle preferences from Streamlit sidebar
    and convert them into a numeric trait dictionary.
    """

    st.sidebar.header("Your Lifestyle & Preferences")

    user_profile = {
        "Energy Level": st.sidebar.slider(
            "Your Energy Level", 1, 5, 3
        ),
        "Good With Young Children": st.sidebar.slider(
            "Good with Young Children", 1, 5, 3
        ),
        "Good With Other Dogs": st.sidebar.slider(
            "Good with Other Dogs", 1, 5, 3
        ),
        "Shedding Level": st.sidebar.slider(
            "Shedding Tolerance", 1, 5, 3
        ),
        "Barking Level": st.sidebar.slider(
            "Tolerance for Barking", 1, 5, 3
        ),
        "Openness To Strangers": st.sidebar.slider(
            "Likes Friendly or Reserved Dogs?", 1, 5, 3
        ),
    }

    return user_profile


# -------------------------------------------------------------------
# Display breed recommendation card
# -------------------------------------------------------------------
def display_breed_result(rank, breed, score, image_url, long_desc, folder_link):
    """
    Render a single breed recommendation card with image, score,
    and descriptive text.
    """
    st.subheader(f"#{rank} — {breed}  (Score: {score:.1f}/100)")
    st.image(image_url, width=300, caption=breed)

    st.markdown(f"[View more **{breed}** photos on dataset]({folder_link})")

    if long_desc:
        st.write("### Why this breed might suit you:")
        st.write(long_desc)


# -------------------------------------------------------------------
# Main App
# -------------------------------------------------------------------
def main():
    st.title("🐕 Choose My Dog Breed — Smart Recommender")
    st.write(
        "Use the sidebar to describe your lifestyle. "
        "Then click the button to discover your top dog breed matches!"
    )

    # Load data
    dog_breeds, trait_desc = load_data()
    clean_df = clean_breed_traits(dog_breeds)

    # Get user inputs
    user_profile = build_user_profile()

    st.markdown("---")
    st.header("🔎 Find Your Perfect Pup")

    if st.button("✨ Show My Top 3 Breeds"):
        results = compute_match_scores(clean_df, user_profile)
        top3 = results.head(3)

        st.markdown("## 🎯 Your Top Matches (with photos)")

        for idx, row in enumerate(top3.itertuples(), start=1):
            breed = getattr(row, "Breed")
            score = getattr(row, "score")

            # Image + folder links
            image_url = get_breed_image_url(breed)
            folder_url = build_image_url(breed)

            # Trait description (optional)
            long_desc = ""
            if breed in trait_desc["Trait"].values:
                long_desc = trait_desc.loc[
                    trait_desc["Trait"] == breed, "Description"
                ].values[0]

            display_breed_result(
                idx,
                breed,
                score,
                image_url,
                long_desc,
                folder_url,
            )

    st.markdown("---")
    st.write("Built with ❤️ using Streamlit")


# -------------------------------------------------------------------
# Run app
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
