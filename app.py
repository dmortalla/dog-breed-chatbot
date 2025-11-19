"""
Streamlit app for the Dog Breed Matchmaker.

This app lets users select their lifestyle and preferences in the sidebar
and then recommends the top 3 matching dog breeds based on trait data.
"""

from typing import Dict
import streamlit as st
import pandas as pd

from recommender_engine import (
    clean_breed_traits,
    compute_match_scores,
    build_image_url,
)
from chatbot_utils import parse_level_answer, describe_trait, load_data


def build_user_profile(
    energy: str,
    children: str,
    other_dogs: str,
    shedding_tolerance: str,
    barking: str,
    stranger: str,
) -> Dict[str, int]:
    """
    Build a simple user profile from sidebar answers.

    Args:
        energy: Text describing energy level (Low, Medium, High).
        children: "Yes" if user has young children, otherwise "No".
        other_dogs: "Yes" if user owns other dogs, otherwise "No".
        shedding_tolerance: Text on sensitivity to dog hair.
        barking: Text describing barking tolerance.
        stranger: Text describing friendliness to strangers.

    Returns:
        Dictionary mapping trait names to desired numeric levels (1–5).
    """
    profile: Dict[str, int] = {
        "Energy Level": parse_level_answer(energy),
        "Playfulness Level": parse_level_answer(energy),
        "Mental Stimulation Needs": parse_level_answer(energy),
        "Good With Young Children": 5 if children == "Yes" else 3,
        "Good With Other Dogs": 5 if other_dogs == "Yes" else 3,
        "Shedding Level": parse_level_answer(shedding_tolerance),
        "Barking Level": parse_level_answer(barking),
        "Openness To Strangers": parse_level_answer(stranger),
        # Defaults
        "Adaptability Level": 4,
        "Trainability Level": 4,
    }
    return profile


def main() -> None:
    """
    Run the Streamlit web application.

    The app:
    - Loads breed and trait description data.
    - Lets the user select preferences in a sidebar.
    - Computes match scores for all breeds.
    - Shows the top 3 matching breeds with explanations and image links.
    """
    st.set_page_config(
        page_title="Dog Breed Matchmaker",
        page_icon="🐶",
        layout="centered",
    )

    st.title("🐕 Dog Breed Matchmaker")
    st.write(
        "Answer a few quick questions and discover the dog breeds that "
        "match your lifestyle!"
    )

    # Load CSVs
    dog_breeds, trait_descriptions = load_data()
    numeric_breeds = clean_breed_traits(dog_breeds)

    # Sidebar questions
    st.sidebar.header("Your Lifestyle & Preferences")

    energy = st.sidebar.selectbox(
        "Your daily activity level",
        ["Low", "Medium", "High"],
    )
    children = st.sidebar.selectbox(
        "Do you have young children?",
        ["No", "Yes"],
    )
    other_dogs = st.sidebar.selectbox(
        "Do you own other dogs?",
        ["No", "Yes"],
    )
    shedding_tolerance = st.sidebar.selectbox(
        "How sensitive are you to dog hair around the home?",
        ["Low", "Medium", "High"],
    )
    barking = st.sidebar.selectbox(
        "How much barking can you tolerate?",
        ["Low", "Medium", "High"],
    )
    stranger = st.sidebar.selectbox(
        "How friendly should your dog be with strangers?",
        ["Low", "Medium", "High"],
    )

    st.sidebar.write("---")

    if st.sidebar.button("Find My Top 3 Breeds! 🐾"):
        user_profile = build_user_profile(
            energy=energy,
            children=children,
            other_dogs=other_dogs,
            shedding_tolerance=shedding_tolerance,
            barking=barking,
            stranger=stranger,
        )

        # Compute scores
        results = compute_match_scores(numeric_breeds, user_profile)
        top3 = results.head(3)

        st.subheader("🎯 Your Top Matches")

        traits_to_show = [
            "Energy Level",
            "Playfulness Level",
            "Good With Young Children",
            "Good With Other Dogs",
            "Shedding Level",
            "Barking Level",
        ]

        for _, row in top3.iterrows():
            breed = row["Breed"]
            score = round(row["score"], 1)
            img_url = build_image_url(breed)

            st.markdown(f"### **{breed}** — Match Score: **{score}/100**")
            st.markdown(f"[See {breed} photos here]({img_url})")

            descriptions = [
                describe_trait(trait_descriptions, trait, row[trait])
                for trait in traits_to_show
                if trait in row.index
            ]

            st.write("**Why this breed could fit you:**")
            if descriptions:
                st.write("• " + "\n• ".join(descriptions[:4]))
            else:
                st.write("Trait information not available.")

            st.write("---")
    else:
        st.info("Use the sidebar to enter your preferences, then click **Find My Top 3 Breeds! 🐾**")


if __name__ == "__main__":
    main()
