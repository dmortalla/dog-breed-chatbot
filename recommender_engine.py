import pandas as pd
import urllib.request
from urllib.parse import quote
from typing import Dict, Tuple, List, Optional

# -------------------------------------------------------------------
# Load CSV data
# -------------------------------------------------------------------

dog_breeds = pd.read_csv("data/breed_traits.csv")
trait_descriptions = pd.read_csv("data/trait_description.csv")

# -------------------------------------------------------------------
# Image Loader Settings
# -------------------------------------------------------------------

RAW_BASE = (
    "https://raw.githubusercontent.com/maartenvandenbroeck/"
    "Dog-Breeds-Dataset/master"
)

# filename patterns used in the dataset
IMAGE_PATTERNS = [
    "Image_1.jpg",
    "Image_1.JPG",
    "image_1.jpg",
    "image_1.JPG",
]

# -------------------------------------------------------------------
# Breed Folder Name Normalization
# -------------------------------------------------------------------

def folder_for_breed(breed: str) -> str:
    """
    Convert breed name to folder format used in the GitHub dataset.
    Example:
        "Havanese" -> "havanese dog"
        "German Shepherd" -> "german shepherd dog"
    """
    b = breed.lower().strip()
    folder = f"{b} dog"
    return folder


# -------------------------------------------------------------------
# Image URL Builder
# -------------------------------------------------------------------

def image_url_for_breed(breed: str) -> Optional[str]:
    """
    Returns a raw GitHub URL for the 1st available image in the breed folder.
    Tries multiple filename variants because the dataset is inconsistent.
    """
    folder = folder_for_breed(breed)
    encoded = quote(folder, safe="")

    for fname in IMAGE_PATTERNS:
        url = f"{RAW_BASE}/{encoded}/{fname}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=5)
            return url
        except Exception:
            continue

    return None


# -------------------------------------------------------------------
# Preference Extraction
# -------------------------------------------------------------------

def extract_preferences(text: str) -> Dict[str, Optional[int]]:
    """
    Extracts user preferences from free text.
    Returns a dictionary of key dog traits.

    Keys include:
    - energy
    - kids
    - allergies
    - home

    Matches the conversational flow used in app.py.
    """
    t = text.lower()
    prefs = {}

    # Energy level
    if "low energy" in t or "calm" in t:
        prefs["energy"] = 1
    elif "medium energy" in t or "moderate" in t:
        prefs["energy"] = 3
    elif "high energy" in t or "active" in t:
        prefs["energy"] = 5

    # Allergies / shedding
    if "hypoallergenic" in t:
        prefs["allergies"] = 1
    elif "low-shedding" in t or "low shedding" in t:
        prefs["allergies"] = 2

    # Good with kids
    if "yes" in t and "child" in t:
        prefs["kids"] = 5
    elif "no" in t and "child" in t:
        prefs["kids"] = 1

    # Home size
    if "small apartment" in t:
        prefs["home"] = 1
    elif "apartment" in t:
        prefs["home"] = 2
    elif "yard" in t or "house" in t:
        prefs["home"] = 5

    return prefs


# -------------------------------------------------------------------
# Scoring Engine
# -------------------------------------------------------------------

def score_breeds(preferences: Dict[str, int]) -> Dict[str, float]:
    """
    Score each dog breed based on user preferences.
    Uses weighted distance between user prefs and breed traits.
    """
    scores = {}

    for _, row in dog_breeds.iterrows():
        breed = row["Breed"]
        total = 0
        count = 0

        # Energy
        if "energy" in preferences:
            trait = int(row["Energy Level"])
            diff = abs(preferences["energy"] - trait)
            total += (5 - diff)
            count += 1

        # Allergies (barking / shedding)
        if "allergies" in preferences:
            trait = int(row["Shedding Level"])
            diff = abs(preferences["allergies"] - trait)
            total += (5 - diff)
            count += 1

        # Kids
        if "kids" in preferences:
            trait = int(row["Good With Young Children"])
            diff = abs(preferences["kids"] - trait)
            total += (5 - diff)
            count += 1

        # Home size
        if "home" in preferences:
            trait = int(row["Openness To Strangers"])
            diff = abs(preferences["home"] - trait)
            total += (5 - diff)
            count += 1

        # Avoid division by zero
        if count == 0:
            continue

        score = (total / (count * 5)) * 100
        scores[breed] = score

    return scores


# -------------------------------------------------------------------
# Top N Breeds
# -------------------------------------------------------------------

def top_n_breeds(scores: Dict[str, float], n=3) -> List[Tuple[str, float]]:
    """
    Return the top-N scoring breeds in descending order.
    """
    sorted_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_list[:n]
