from typing import List, Optional

import pandas as pd


def _score_energy(row: pd.Series, energy: Optional[str]) -> int:
    """Score how well the breed's energy matches the user's preference."""
    if not energy:
        return 0

    breed_energy = int(row["Energy Level"])

    target_map = {
        "low": 2,
        "medium": 3,
        "high": 5,
    }
    target = target_map.get(energy.lower())
    if target is None:
        return 0

    diff = abs(breed_energy - target)
    # exact match → 3 pts, 1 away → 2 pts, 2 away → 1 pt, else 0
    return max(0, 3 - diff)


def _score_living(row: pd.Series, living: Optional[str]) -> int:
    """Score how well the breed fits the living situation."""
    if not living:
        return 0

    energy = int(row["Energy Level"])
    adapt = int(row["Adaptability Level"])
    living = living.lower()

    score = 0

    if living == "small apartment":
        # Prefer highly adaptable, not super high-energy
        score += max(0, adapt - 2)  # 3→1 pt, 4→2 pts, 5→3 pts
        if energy <= 3:
            score += 1
    elif living == "standard apartment":
        score += max(0, adapt - 1)
    elif living == "house with a yard":
        # Active breeds get a small boost
        score += max(0, energy - 2)

    return score


def _score_allergies(row: pd.Series, allergies: Optional[str]) -> int:
    """Score how well the breed fits allergy / shedding preferences."""
    if not allergies:
        return 0

    allergies = allergies.lower()
    shed = int(row["Shedding Level"])

    score = 0
    if allergies == "low-shedding":
        # Lower shedding (1–2) is strongly preferred, 3 is OK
        if shed <= 2:
            score += 3
        elif shed == 3:
            score += 1
    elif allergies == "hypoallergenic":
        # Very strict: only the lowest shedding get a big boost
        if shed == 1:
            score += 4
        elif shed == 2:
            score += 2

    return score


def _score_children(row: pd.Series, children: Optional[str]) -> int:
    """Score child-friendliness."""
    if not children:
        return 0

    children = children.lower()
    kid_score = int(row["Good With Young Children"])

    score = 0
    if children == "yes":
        # Higher kid-friendliness is better
        score += max(0, kid_score - 2)  # 3→1, 4→2, 5→3
    elif children == "no":
        # User prefers not necessarily kid-oriented
        score += max(0, 4 - kid_score)  # 1→3, 2→2, 3→1, 4–5→0

    return score


def recommend_breeds(
    breeds_df: pd.DataFrame,
    energy: Optional[str],
    living: Optional[str],
    allergies: Optional[str],
    children: Optional[str],
    size: Optional[str],  # kept for future use – not used in scoring for now
    top_n: int = 3,
) -> List[str]:
    """
    Return a simple, sorted list of breed names that best match the preferences.

    There is **no exposed match percentage** now – just internal scoring
    used to rank the breeds.
    """
    # Work on a copy so we never mutate the original DataFrame
    df = breeds_df.copy()

    scores = []
    for _, row in df.iterrows():
        score = 0
        score += _score_energy(row, energy)
        score += _score_living(row, living)
        score += _score_allergies(row, allergies)
        score += _score_children(row, children)
        scores.append(score)

    df["__score"] = scores

    # Sort by score (descending) and take top_n
    df_sorted = df.sort_values("__score", ascending=False)

    # Filter out completely zero-score rows to avoid pointless matches
    df_sorted = df_sorted[df_sorted["__score"] > 0]

    return df_sorted["Breed"].head(top_n).tolist()

