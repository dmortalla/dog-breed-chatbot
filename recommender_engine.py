import pandas as pd

def score_breed(row, prefs):
    """Return a match score between a single breed row and user preferences."""
    score = 0

    # ENERGY
    if "energy" in prefs:
        try:
            breed_energy = int(row["Energy Level"])
            score += 5 - abs(breed_energy - prefs["energy"])
        except:
            pass

    # HOME → Adaptability Level
    if "home" in prefs:
        try:
            adaptability = int(row["Adaptability Level"])
            score += 5 - abs(adaptability - prefs["home"])
        except:
            pass

    # ALLERGIES / SHEDDING
    if "allergies" in prefs:
        try:
            shedding = int(row["Shedding Level"])
            if prefs["allergies"] == 1:        # hypoallergenic (prefer very low shedding)
                score += max(0, 5 - shedding)
            elif prefs["allergies"] == 2:      # low shedding
                score += max(0, 5 - shedding)
            elif prefs["allergies"] == 4:      # shedding ok
                score += 1
        except:
            pass

    # KIDS
    if "kids" in prefs:
        try:
            kids_score = int(row["Good With Young Children"])
            score += kids_score
        except:
            pass

    return score


def recommend_breeds(dog_breeds, prefs, top_n=3):
    """Return the top matching breeds."""
    dog_breeds = dog_breeds.copy()

    dog_breeds["match_score"] = dog_breeds.apply(
        lambda row: score_breed(row, prefs),
        axis=1
    )

    ranked = dog_breeds.sort_values(
        by="match_score",
        ascending=False
    )

    top_breeds = ranked.head(top_n)["Breed"].tolist()
    return top_breeds
