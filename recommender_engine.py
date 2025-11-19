import pandas as pd


def score_match(breed_row, energy, living, allergies, children, size):
    """
    Compute a simple matching score for one breed row.
    Higher score = better match.
    """

    score = 0

    # energy (1–5 scale vs. low/medium/high)
    if energy:
        if energy == "low" and breed_row["Energy Level"] <= 2:
            score += 1
        elif energy == "medium" and breed_row["Energy Level"] == 3:
            score += 1
        elif energy == "high" and breed_row["Energy Level"] >= 4:
            score += 1

    # living environment
    if living:
        if living == "small apartment" and breed_row["Adaptability Level"] >= 4:
            score += 1
        if living == "standard apartment" and breed_row["Adaptability Level"] >= 3:
            score += 1
        if living == "house with a yard" and breed_row["Energy Level"] >= 3:
            score += 1

    # allergies
    if allergies:
        if allergies == "hypoallergenic" and "hypoallergenic" in str(breed_row["Coat Type"]).lower():
            score += 1
        if allergies == "low-shedding" and breed_row["Shedding Level"] <= 2:
            score += 1

    # children
    if children:
        if children == "yes" and breed_row["Good With Young Children"] >= 4:
            score += 1
        if children == "no" and breed_row["Good With Young Children"] <= 2:
            score += 1

    # dog size from dataset's Coat Length + maybe other traits
    if size:
        # This is approximate — dataset doesn't have direct size measure
        if size == "small" and breed_row["Coat Grooming Frequency"] <= 2:
            score += 1
        if size == "medium" and breed_row["Coat Grooming Frequency"] == 3:
            score += 1
        if size == "large" and breed_row["Coat Grooming Frequency"] >= 4:
            score += 1

    return score


def recommend_breeds(df, energy, living, allergies, children, size):
    """
    Return top matching dog breeds based on memory.
    """
    if df is None or df.empty:
        return []

    df = df.copy()
    df["score"] = df.apply(
        lambda row: score_match(
            row, energy, living, allergies, children, size
        ),
        axis=1
    )

    # Sort by best score, return top 3
    df_sorted = df.sort_values(by="score", ascending=False)
    top = df_sorted.head(3)

    return list(top["Breed"])
