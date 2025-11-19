from typing import List, Dict, Optional
import pandas as pd
from urllib.parse import quote


# Base URL for the public GitHub image dataset
BASE_IMAGE_URL = (
    "https://raw.githubusercontent.com/maartenvandenbroeck/"
    "Dog-Breeds-Dataset/master/"
)


def _clean_breed_label(raw: str) -> str:
    """Convert raw AKC-style breed label into a clean, human-readable name."""
    if not isinstance(raw, str):
        return ""

    # Replace non-breaking spaces and trim
    txt = raw.replace("\xa0", " ").strip()

    # Drop bracketed group info like "Retrievers (Labrador)"
    if "(" in txt and ")" in txt:
        txt = txt.split("(")[0].strip()

    # Simple plural handling
    if txt.endswith("Dogs"):
        txt = txt[:-1]  # "Dogs" -> "Dog"
    elif txt.endswith("dogs"):
        txt = txt[:-1]
    elif txt.endswith("s") and not txt.endswith("ss"):
        txt = txt[:-1]

    return txt


def _folder_name_for_breed(clean_breed: str) -> str:
    """
    Map a clean breed name to the folder name used in the image repo.

    Pattern (Option B):
    - lower-case
    - strip apostrophes
    - append ' dog' if not present
    """
    folder = clean_breed.lower()
    folder = folder.replace("'", "")  # remove apostrophes
    while "  " in folder:
        folder = folder.replace("  ", " ")
    folder = folder.strip()

    if not folder.endswith(" dog"):
        folder = f"{folder} dog"

    return folder


def _image_url_for_breed(clean_breed: str) -> str:
    """Build a URL for Image_1.jpg of the given breed from the GitHub dataset."""
    folder = _folder_name_for_breed(clean_breed)
    folder_enc = quote(folder)  # URL-encode spaces, etc.
    return f"{BASE_IMAGE_URL}{folder_enc}/Image_1.jpg"


def _score_row(
    row: pd.Series,
    energy: Optional[str],
    living: Optional[str],
    allergies: Optional[str],
    children: Optional[str],
    size: Optional[str],
) -> float:
    """
    Compute a numeric score for one breed row based on user preferences.

    Higher score = better match.
    """
    score = 0.0

    # -------- Energy Level (1–5 in dataset) --------
    if energy:
        target = {"low": 1, "medium": 3, "high": 5}.get(energy, 3)
        val = row.get("Energy Level", 3)
        if pd.notna(val):
            score -= abs(val - target) * 1.5

    # -------- Shedding / Allergies --------
    shed = row.get("Shedding Level", 3)
    if pd.notna(shed) and allergies:
        if allergies == "hypoallergenic":
            # Punish shedding strongly
            score -= shed * 1.5
        elif allergies == "low-shedding":
            score -= max(0, shed - 2) * 1.0

    # -------- Children friendliness --------
    kids_val = row.get("Good With Young Children", 3)
    if pd.notna(kids_val):
        if children == "yes":
            score += kids_val * 1.5
        elif children == "no":
            score += (6 - kids_val) * 1.0  # lower friendless = better for "no kids"

    # -------- Living situation (small apt vs house) --------
    bark = row.get("Barking Level", 3)
    energy_val = row.get("Energy Level", 3)
    if living and pd.notna(bark) and pd.notna(energy_val):
        if living.startswith("small"):
            # small apartments prefer calmer, quieter dogs
            score -= max(0, energy_val - 3) * 1.0
            score -= max(0, bark - 3) * 0.8
        elif "apartment" in living:
            score -= max(0, energy_val - 4) * 0.7
        elif "house" in living:
            # house with yard: higher energy is okay / slightly rewarded
            score += max(0, energy_val - 3) * 0.7

    # -------- Size preference --------
    # Dataset has no explicit size column; we keep this neutral for now.
    # The parameter is kept so you can extend it later.

    return float(score)


def recommend_breeds(
    df: pd.DataFrame,
    energy: Optional[str],
    living: Optional[str],
    allergies: Optional[str],
    children: Optional[str],
    size: Optional[str],
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Return a DataFrame of the top N matching breeds with an added 'Score' column.

    Args:
        df: DataFrame loaded from breed_traits.csv.
        energy, living, allergies, children, size: User preferences.
        top_n: Number of breeds to return.

    Returns:
        DataFrame of top-N breeds sorted by descending score.
    """
    if df.empty:
        return df

    df = df.copy()
    df["Clean_Breed"] = df["Breed"].apply(_clean_breed_label)

    scores = []
    for _, row in df.iterrows():
        s = _score_row(row, energy, living, allergies, children, size)
        scores.append(s)

    df["Score"] = scores
    df_sorted = df.sort_values("Score", ascending=False)
    return df_sorted.head(top_n)


def recommend_breeds_with_cards(
    df: pd.DataFrame,
    energy: Optional[str],
    living: Optional[str],
    allergies: Optional[str],
    children: Optional[str],
    size: Optional[str],
    top_n: int = 3,
) -> List[Dict[str, str]]:
    """
    Return a list of "cards" with cleaned breed name, image URL, and a short summary.

    Each card is a dict:
        {
            "breed": "<clean name>",
            "image_url": "<GitHub image URL>",
            "summary": "<short explanation>",
            "dataset_link": "<link to dataset repo>",
        }
    """
    top_df = recommend_breeds(df, energy, living, allergies, children, size, top_n=top_n)
    cards: List[Dict[str, str]] = []

    for _, row in top_df.iterrows():
        clean_name = row["Clean_Breed"]
        image_url = _image_url_for_breed(clean_name)
        summary = (
            f"🌟 **{clean_name}** looks like a strong match for your lifestyle. "
            f"It balances energy, shedding, kid-friendliness, and other traits "
            f"based on the preferences you selected."
        )
        cards.append(
            {
                "breed": clean_name,
                "image_url": image_url,
                "summary": summary,
                "dataset_link": "https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset",
            }
        )

    return cards

