"""
Recommendation and image helper functions for the Dog Breed Chatbot.

This module:
- Cleans numeric trait columns from the breed_traits dataset.
- Computes a match score between a user preference profile and each breed.
- Converts breed names into folder names for the GitHub image dataset.
- Builds image URLs and folder URLs for displaying photos in the app.
"""

from typing import Dict

import pandas as pd
import unicodedata
import re

# -------------------------------------------------------------------
# Numeric traits present in data/breed_traits.csv
# -------------------------------------------------------------------

NUMERIC_TRAITS = [
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


# -------------------------------------------------------------------
# Data cleaning
# -------------------------------------------------------------------

def clean_breed_traits(df: pd.DataFrame) -> pd.DataFrame:
    """Clean mixed numeric trait columns and return a new DataFrame.

    The original CSV stores many traits as strings like "5 - Very High".
    This function extracts just the leading digit and converts it to a
    numeric value (float).

    Args:
        df: Raw dog_breeds DataFrame loaded from CSV.

    Returns:
        A copy of the DataFrame with numeric trait columns converted to
        floats where possible.
    """
    df_clean = df.copy()

    for col in NUMERIC_TRAITS:
        if col in df_clean.columns:
            # Extract the first digit (e.g. "5 - Very High" -> "5")
            extracted = df_clean[col].astype(str).str.extract(r"(\d)", expand=False)
            df_clean[col] = pd.to_numeric(extracted, errors="coerce")

    return df_clean


# -------------------------------------------------------------------
# Match scoring
# -------------------------------------------------------------------

def compute_match_scores(
    numeric_df: pd.DataFrame, user_profile: Dict[str, int]
) -> pd.DataFrame:
    """Compute a similarity score (0–100) between user profile and each breed.

    The score is based on the summed absolute distance across all trait
    sliders the user controls. The smaller the distance, the higher the
    score.

    Args:
        numeric_df: Cleaned DataFrame with numeric trait columns.
        user_profile: Dictionary mapping trait name to value (1–5).

    Returns:
        DataFrame sorted by descending score, with extra columns:
        - distance: total absolute difference across all traits.
        - score: similarity score scaled 0–100.
    """
    traits = list(user_profile.keys())

    # Drop breeds that have missing values for any selected trait
    df = numeric_df.dropna(subset=traits).copy()

    max_diff = 4 * len(traits)  # max distance per trait is |5-1| = 4

    def total_diff(row) -> float:
        return sum(abs(float(row[t]) - float(user_profile[t])) for t in traits)

    df["distance"] = df.apply(total_diff, axis=1)
    df["score"] = (1.0 - df["distance"] / max_diff) * 100.0
    df["score"] = df["score"].clip(lower=0.0, upper=100.0)

    return df.sort_values(by="score", ascending=False)


# -------------------------------------------------------------------
# Folder name helpers for the GitHub dataset
# -------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    """Remove accents and keep only basic ASCII characters."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if ord(c) < 128)


def dataset_folder_for_breed(breed: str) -> str:
    """Convert a breed name into the GitHub dataset folder name.

    The dataset folders look like:
    - "akita dog"
    - "alaskan malamute dog"
    - "cirneco dell'etna dog"

    We approximate this by:
    - Stripping accents.
    - Lowercasing.
    - Removing most punctuation except spaces and hyphens.
    - Normalizing whitespace.
    - Ensuring the name ends with the word "dog".

    Args:
        breed: Breed name from the CSV (e.g., "Rhodesian Ridgebacks").

    Returns:
        Folder name used in the GitHub dataset (e.g. "rhodesian ridgeback dog").
    """
    if not breed:
        return ""

    name = _strip_accents(breed)
    name = name.lower()

    # Keep letters, digits, spaces, and hyphens; drop other punctuation.
    name = re.sub(r"[^\w\s\-]", "", name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Rough plural handling: remove trailing 's' for many breed names
    # (e.g., "ridgebacks" -> "ridgeback").
    if not name.endswith(" dog") and name.endswith("s"):
        name = name[:-1]

    # Ensure it ends with "dog"
    if not name.endswith("dog"):
        if not name.endswith(" "):
            name = name + " "
        name = name + "dog"

    return name


# -------------------------------------------------------------------
# Image + folder URLs
# -------------------------------------------------------------------

def get_breed_image_url(breed: str) -> str:
    """Return a URL to one sample image for the given breed.

    We do not know the exact image file naming convention, but most
    large image datasets contain files like "1.jpg", "2.jpg", etc.
    Here we simply point to "1.jpg" in the folder. If that file does
    not exist, the image will fail gracefully in Streamlit.

    Args:
        breed: Breed name from the CSV.

    Returns:
        Raw GitHub URL that Streamlit can use in st.image.
    """
    base = (
        "https://raw.githubusercontent.com/"
        "maartenvandenbroeck/Dog-Breeds-Dataset/master"
    )
    folder = dataset_folder_for_breed(breed)
    return f"{base}/{folder}/1.jpg"


def build_image_url(breed: str) -> str:
    """Return a GitHub folder URL for 'View more photos' links.

    Args:
        breed: Breed name from the CSV.

    Returns:
        GitHub tree URL pointing to that breed's folder.
    """
    folder = dataset_folder_for_breed(breed)
    return (
        "https://github.com/maartenvandenbroeck/"
        f"Dog-Breeds-Dataset/tree/master/{folder}"
    )


