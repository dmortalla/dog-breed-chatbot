"""Core recommendation logic for the Dog Breed Matchmaker.

This module contains simple helper functions to:
- Clean numeric trait columns.
- Compute match scores for each breed.
- Build URLs to image searches or sample image URLs for each breed.
"""

from typing import Dict, List

import pandas as pd

NUMERIC_TRAIT_COLUMNS: List[str] = [
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

GITHUB_DATASET_URL: str = "https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset"


def clean_breed_traits(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 1–5 trait columns to numeric values.

    The raw CSV often stores traits as strings like:
    - "5"
    - "5 - Very High"
    - "3 out of 5"

    This function extracts the first digit and converts it to an integer.

    Args:
        df: Original dog breed traits DataFrame.

    Returns:
        A copy of the DataFrame with numeric trait columns.
    """
    df_clean = df.copy()
    for col in NUMERIC_TRAIT_COLUMNS:
        if col in df_clean.columns:
            extracted = df_clean[col].astype(str).str.extract(r"(\d)").iloc[:, 0]
            df_clean[col] = pd.to_numeric(extracted, errors="coerce")
    return df_clean


def compute_match_scores(
    numeric_df: pd.DataFrame,
    user_profile: Dict[str, int],
) -> pd.DataFrame:
    """Compute match scores for all breeds given a user profile.

    For each trait:
    - We compute the absolute difference between the breed value and
      the user's desired value (1–5).
    - We sum these differences to get a distance.
    - We convert that distance to a score between 0 and 100.

    Args:
        numeric_df: DataFrame with numeric trait values for all breeds.
        user_profile: Dictionary mapping trait names to desired levels.

    Returns:
        A DataFrame sorted by best match (smallest distance).
    """
    traits = list(user_profile.keys())
    df = numeric_df.dropna(subset=traits).copy()

    # Each trait gets an equal weight of 1.0 to keep it simple.
    weights = [1.0] * len(traits)
    max_distance = 4.0 * sum(weights)  # max |1-5| per trait is 4

    def distance(row: pd.Series) -> float:
        dist = 0.0
        for t, w in zip(traits, weights):
            desired = float(user_profile[t])
            dist += w * abs(float(row[t]) - desired)
        return dist

    df["distance"] = df.apply(distance, axis=1)

    # Convert distance to score: closer means higher score.
    df["score"] = (1.0 - df["distance"] / max_distance).clip(0.0, 1.0) * 100.0

    df = df.sort_values(by=["distance", "score"], ascending=[True, False])
    return df


def build_image_url(breed: str) -> str:
    """Build a GitHub search URL for images of a given breed.

    Args:
        breed: Dog breed name as stored in the dataset.

    Returns:
        A URL string pointing to a GitHub search for this breed.
    """
    query = breed.replace(" ", "+")
    return f"{GITHUB_DATASET_URL}/search?q={query}"


def get_breed_image_url(breed: str) -> str:
    """Get a sample image URL for a breed.

    This version uses the Unsplash "featured" endpoint to return an image
    tagged with both "dog" and the breed name. In a production setting,
    you could instead map each breed to a specific image from the GitHub
    dataset.

    Args:
        breed: Dog breed name.

    Returns:
        A URL string pointing to an image that Streamlit can display.
    """
    # Replace spaces with "+" so the breed name can be used in a query.
    query = breed.replace(" ", "+")
    # This URL returns a random but relevant image on each load.
    return f"https://source.unsplash.com/featured/?dog,{query}"
