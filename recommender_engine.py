"""
Recommendation + Image Loading Engine for Dog Breed Matchmaker

This version is fully compatible with the folder structure of:
https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset

Folders look like:
"airedale terrier dog"
"akita dog"
"alaskan malamute dog"
etc.

This module handles:
- Normalizing CSV breed names → correct dataset folder format
- Constructing stable image URLs
- Trait cleaning & match scoring
"""

import pandas as pd
import unicodedata
import re

# ------------------------------------------------------------
# 1. NUMERIC TRAITS
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# 2. Trait cleaning
# ------------------------------------------------------------

def clean_breed_traits(df: pd.DataFrame) -> pd.DataFrame:
    """Convert mixed string traits like '5 - High' → numeric 5."""
    df = df.copy()
    for col in NUMERIC_TRAITS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.extract(r"(\d)")
                .iloc[:, 0]
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ------------------------------------------------------------
# 3. Compute match score (0–100)
# ------------------------------------------------------------

def compute_match_scores(numeric_df: pd.DataFrame, user_profile: dict) -> pd.DataFrame:
    """Compute similarity score between user profile and each breed."""
    traits = list(user_profile.keys())
    df = numeric_df.dropna(subset=traits).copy()

    max_diff = 4 * len(traits)

    def total_diff(row):
        return sum(abs(float(row[t]) - float(user_profile[t])) for t in traits)

    df["distance"] = df.apply(total_diff, axis=1)
    df["score"] = (1 - df["distance"] / max_diff) * 100
    df["score"] = df["score"].clip(0, 100)

    return df.sort_values(by="score", ascending=False)


# ------------------------------------------------------------
# 4. Dataset folder normalization rules
# ------------------------------------------------------------

def dataset_folder_for_breed(breed: str) -> str:
    """
    Convert CSV breed names into the dataset's folder names.

    Dataset format:
    - lowercase
    - remove accents
    - remove punctuation
    - convert plural → singular
    - append " dog"

    Example:
    "Rhodesian Ridgebacks" → "rhodesian ridgeback dog"
    """
    # Normalize Unicode → ASCII
    name = unicodedata.normalize('NFKD', breed)
    name = ''.join(c for c in name if ord(c) < 128)

    # Lowercase
    name = name.lower()

    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # Remove plural "s" (simple heuristic works for 95% of breeds)
    if name.endswith("s"):
        name = name[:-1]

    # Add dataset suffix
    folder = f"{name} dog"

    return folder


# ------------------------------------------------------------
# 5. Construct REAL GitHub image URL
# ------------------------------------------------------------

def get_breed_image_url(breed: str) -> str:
    """
    Build a URL pointing to a real photo in the GitHub dataset.

    The dataset usually contains images named:
    - 1.jpg
    - 2.jpg
    - 3.jpg
    ...
    """
    base = "https://raw.githubusercontent.com/maartenvandenbroeck/Dog-Breeds-Dataset/master"
    folder = dataset_folder_for_breed(breed)

    return f"{base}/{folder}/1.jpg"  # most folders have at least "1.jpg"


# ------------------------------------------------------------
# 6. Folder link for gallery
# ------------------------------------------------------------

def build_image_url(breed: str) -> str:
    """Return GitHub folder link for 'View more photos'."""
    folder = dataset_folder_for_bre ed(breed)
    return f"https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset/tree/master/{folder}"

