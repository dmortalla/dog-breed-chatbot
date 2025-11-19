"""
Recommender engine for the Dog Breed Chatbot (serverless version).

This module:

- Fetches the list of breed folders from the GitHub Dog-Breeds-Dataset
  repository using the GitHub REST API.
- Loads the dog breed traits table from data/breed_traits.csv.
- Ensures that only breeds with image folders are ever recommended.
- Scores breeds against a user preference profile (1–5 scale traits).
- Builds image URLs (using 1.jpg) and folder URLs for each breed.
"""

from __future__ import annotations

import json
import urllib.request
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# GitHub config
# -------------------------------------------------------------------
GITHUB_USER = "maartenvandenbroeck"
GITHUB_REPO = "Dog-Breeds-Dataset"
BRANCH = "master"

RAW_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
)
WEB_BASE = (
    f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/tree/{BRANCH}"
)

GITHUB_CONTENTS_API = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents?ref={BRANCH}"
)


# -------------------------------------------------------------------
# Fetch breed folders directly from GitHub (serverless)
# -------------------------------------------------------------------
@lru_cache(maxsize=1)
def fetch_breed_folders_from_github() -> List[str]:
    """Fetch folder names from the Dog-Breeds-Dataset repo using GitHub API.

    This uses the public API and is cached in memory using lru_cache so it
    is called at most once per process.

    Returns:
        List of folder names like:
        ["affenpinscher dog", "afghan hound dog", "cirneco dell'etna dog", ...]
    """
    try:
        with urllib.request.urlopen(GITHUB_CONTENTS_API, timeout=30) as resp:
            data = resp.read().decode("utf-8")
        items = json.loads(data)
    except Exception as exc:  # noqa: BLE001
        # If something goes wrong, return an empty list.
        print(f"Warning: could not fetch breed folders from GitHub: {exc}")
        return []

    folders: List[str] = [
        item["name"]
        for item in items
        if isinstance(item, dict) and item.get("type") == "dir"
    ]
    return folders


# Cached list of supported folders
SUPPORTED_FOLDERS: List[str] = fetch_breed_folders_from_github()


# -------------------------------------------------------------------
# Load traits
# -------------------------------------------------------------------
def load_breed_traits(path: str = "data/breed_traits.csv") -> pd.DataFrame:
    """Load breed traits and ensure numeric columns are numeric.

    Args:
        path: Path to the breed traits CSV file.

    Returns:
        DataFrame with a 'Breed' column and trait columns on 1–5 scales.
    """
    df = pd.read_csv(path)

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
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# -------------------------------------------------------------------
# Folder mapping helpers
# -------------------------------------------------------------------
def folder_for_breed(breed: str) -> Optional[str]:
    """Map a breed name from CSV to an image folder name.

    Example:
        "Anatolian Shepherd Dogs" -> "anatolian shepherd dog"

    This function also checks that the folder is present in SUPPORTED_FOLDERS.
    If not, it returns None.

    Args:
        breed: Breed name from the traits table.

    Returns:
        Matching folder name or None.
    """
    if not isinstance(breed, str):
        return None

    name = breed.strip().lower()

    # Normalize plurals:
    #   "... dogs" -> "... dog"
    #   "... dog"  -> "... dog"
    if name.endswith(" dogs"):
        name = name[:-1]
    elif name.endswith(" dog"):
        pass
    else:
        # Many folders use the "dog" suffix, so we try that.
        name = name + " dog"

    if name in SUPPORTED_FOLDERS:
        return name

    # Fallback: sometimes the CSV may already match folder naming
    if breed.strip().lower() in SUPPORTED_FOLDERS:
        return breed.strip().lower()

    return None


def image_url_for_breed(breed: str) -> Optional[str]:
    """Return a raw GitHub URL for Image_1.jpg in this breed's folder."""
    folder = folder_for_breed(breed)
    if folder is None:
        return None

    from urllib.parse import quote

    encoded_folder = quote(folder, safe="")

    # Try common filename variants used in the dataset
    possible_files = [
        "Image_1.jpg",
        "Image_1.JPG",
        "image_1.jpg",
        "image_1.JPG",
    ]

    for fname in possible_files:
        url = f"{RAW_BASE}/{encoded_folder}/{fname}"
        # Do a HEAD request to check existence
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=5):
                return url
        except Exception:
            continue

    return None


def folder_url_for_breed(breed: str) -> Optional[str]:
    """Return the GitHub web URL for this breed's image folder."""
    folder = folder_for_breed(breed)
    if folder is None:
        return None

    from urllib.parse import quote

    encoded_folder = quote(folder, safe="")
    return f"{WEB_BASE}/{encoded_folder}"


# -------------------------------------------------------------------
# Scoring logic
# -------------------------------------------------------------------
PREFERENCE_TRAITS = {
    "Energy Level": "Energy Level",
    "Good With Young Children": "Good With Young Children",
    "Shedding Level": "Shedding Level",
    "Barking Level": "Barking Level",
    "Trainability Level": "Trainability Level",
    "Affectionate With Family": "Affectionate With Family",
}


def score_breeds(
    dog_breeds: pd.DataFrame,
    prefs: Dict[str, int],
    weights: Dict[str, float],
) -> pd.DataFrame:
    """Score only breeds that have image folders.

    Args:
        dog_breeds: Full traits DataFrame.
        prefs: Mapping trait -> desired level (1–5).
        weights: Mapping trait -> importance weight.

    Returns:
        DataFrame sorted by score (descending), with columns:
        ['Breed', 'score', 'details'] where 'details' is a dict of per-trait info.
    """
    # Keep only breeds with a folder in the GitHub dataset
    mask = dog_breeds["Breed"].apply(lambda b: folder_for_breed(b) is not None)
    df = dog_breeds[mask].copy().reset_index(drop=True)

    total_weight = sum(weights.values()) or 1.0

    scores: List[float] = []
    details_list: List[Dict[str, Dict[str, float]]] = []

    for _, row in df.iterrows():
        breed_score = 0.0
        details: Dict[str, Dict[str, float]] = {}

        for trait_label, col_name in PREFERENCE_TRAITS.items():
            desired = prefs.get(trait_label)
            weight = weights.get(trait_label, 0.0)
            actual = row.get(col_name, np.nan)

            if desired is None or np.isnan(actual):
                diff = 2.0  # neutral gap
            else:
                diff = abs(float(actual) - float(desired))

            # Max difference on a 1–5 scale is 4 → convert to 0–1 match.
            match = max(0.0, 1.0 - diff / 4.0)
            weighted = match * weight
            breed_score += weighted

            details[trait_label] = {
                "desired": desired,
                "actual": float(actual) if not np.isnan(actual) else None,
                "match": match,
                "weight": weight,
            }

        score_pct = (breed_score / total_weight) * 100.0
        scores.append(score_pct)
        details_list.append(details)

    df["score"] = scores
    df["details"] = details_list

    return df[["Breed", "score", "details"]].sort_values(
        by="score", ascending=False
    ).reset_index(drop=True)


def explain_match(details: Dict[str, Dict[str, float]]) -> List[str]:
    """Create human-readable bullet points from per-trait details."""
    lines: List[str] = []

    for trait, info in details.items():
        desired = info["desired"]
        actual = info["actual"]
        match = info["match"]

        if actual is None:
            lines.append(f"- No data available for **{trait}**.")
            continue

        if match > 0.8:
            lines.append(
                f"- Excellent match on **{trait.lower()}** "
                f"(you prefer {desired}, this breed is about {int(round(actual))})."
            )
        elif match > 0.6:
            lines.append(
                f"- Good match on **{trait.lower()}** "
                f"(you prefer {desired}, this breed is about {int(round(actual))})."
            )
        elif match > 0.4:
            lines.append(
                f"- Moderate match on **{trait.lower()}** "
                f"(you prefer {desired}, this breed is {int(round(actual))})."
            )
        else:
            lines.append(
                f"- Weaker match on **{trait.lower()}** "
                f"(you prefer {desired}, this breed is {int(round(actual))})."
            )

    return lines
