from typing import List, Dict, Any

import pandas as pd


GITHUB_BASE = "https://raw.githubusercontent.com/maartenvandenbroeck/Dog-Breeds-Dataset/master"


def _prepare_breed_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure numerical trait columns are numeric for scoring.
    """
    work = df.copy()

    numeric_cols = [
        "Affectionate With Family",
        "Good With Young Children",
        "Good With Other Dogs",
        "Shedding Level",
        "Coat Grooming Frequency",
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
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")

    return work


def _score_breed(
    row: pd.Series,
    energy: str,
    living: str,
    allergies: str,
    children: str,
    size: str,
) -> int:
    """
    Compute a simple matching score for one breed.
    Higher score → better match.
    """
    score = 0

    # ENERGY
    energy_level = row.get("Energy Level", None)
    if energy and pd.notna(energy_level):
        if energy == "low" and energy_level <= 2:
            score += 2
        elif energy == "medium" and energy_level == 3:
            score += 2
        elif energy == "high" and energy_level >= 4:
            score += 2

    # LIVING
    adaptability = row.get("Adaptability Level", None)
    if living and pd.notna(adaptability):
        if living == "small apartment" and adaptability >= 4:
            score += 2
        elif living == "apartment" and adaptability >= 3:
            score += 1
        elif living == "house with yard" and energy_level is not None and energy_level >= 3:
            score += 1

    # ALLERGIES / SHEDDING
    shedding = row.get("Shedding Level", None)
    coat_type = str(row.get("Coat Type", "")).lower()
    if allergies:
        if allergies == "hypoallergenic":
            if "hypoallergenic" in coat_type:
                score += 2
        elif allergies == "low-shedding":
            if pd.notna(shedding) and shedding <= 2:
                score += 2

    # CHILDREN
    kids_trait = row.get("Good With Young Children", None)
    if children and pd.notna(kids_trait):
        if children == "yes" and kids_trait >= 4:
            score += 2
        elif children == "no" and kids_trait <= 2:
            score += 1

    # SIZE (approximation using grooming frequency as a weak proxy)
    grooming = row.get("Coat Grooming Frequency", None)
    if size and pd.notna(grooming):
        if size == "small" and grooming <= 2:
            score += 1
        elif size == "medium" and grooming == 3:
            score += 1
        elif size == "large" and grooming >= 4:
            score += 1

    return score


def _build_image_url_and_link(breed_name: str) -> Dict[str, str]:
    """
    Build a best-guess image URL and dataset folder link
    from the external GitHub dataset.

    We assume folder names like 'beagle dog' and a file 'Image_1.jpg'.
    """
    folder_slug = breed_name.strip().lower().replace("/", " ")
    if not folder_slug.endswith("dog"):
        folder_slug = f"{folder_slug} dog"

    folder_encoded = folder_slug.replace(" ", "%20")
    image_url = f"{GITHUB_BASE}/{folder_encoded}/Image_1.jpg"
    dataset_link = f"https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset/tree/master/{folder_slug.replace(' ', '%20')}"

    return {"image_url": image_url, "dataset_link": dataset_link}


def _build_summary_text(
    breed_name: str,
    row: pd.Series,
    energy: str,
    living: str,
    allergies: str,
    children: str,
    size: str,
) -> str:
    """
    Create a short, social-media-style description for the breed.
    """
    energy_level = row.get("Energy Level", None)
    shedding = row.get("Shedding Level", None)
    kids_trait = row.get("Good With Young Children", None)

    # Energy description
    if pd.notna(energy_level):
        if energy_level <= 2:
            energy_desc = "low-energy and relaxed"
        elif energy_level == 3:
            energy_desc = "moderately active"
        else:
            energy_desc = "high-energy and playful"
    else:
        energy_desc = "easy-going"

    # Shedding description
    if pd.notna(shedding):
        if shedding <= 2:
            shed_desc = "low shedding"
        elif shedding == 3:
            shed_desc = "moderate shedding"
        else:
            shed_desc = "higher shedding"
    else:
        shed_desc = "unknown shedding"

    # Kids description
    if pd.notna(kids_trait):
        if kids_trait >= 4:
            kids_desc = "great with children"
        elif kids_trait == 3:
            kids_desc = "okay with children"
        else:
            kids_desc = "less suited to young children"
    else:
        kids_desc = "temperament with kids varies"

    living_phrase = ""
    if living == "small apartment":
        living_phrase = "in smaller apartments"
    elif living == "apartment":
        living_phrase = "in most apartments"
    elif living == "house with yard":
        living_phrase = "in homes with a yard"

    allergy_phrase = ""
    if allergies == "hypoallergenic":
        allergy_phrase = "and may suit people with allergies"
    elif allergies == "low-shedding":
        allergy_phrase = "and is a good choice if you prefer less fur around"

    size_phrase = ""
    if size == "small":
        size_phrase = "small-sized companion"
    elif size == "medium":
        size_phrase = "medium-sized companion"
    elif size == "large":
        size_phrase = "large, impressive companion"

    parts = [
        f"Meet **{breed_name}** — a {energy_desc} dog",
    ]
    if size_phrase:
        parts.append(f"and a {size_phrase}")
    parts.append(f"with {shed_desc}.")

    sentence1 = " ".join(parts)

    sentence2_parts = []
    if living_phrase:
        sentence2_parts.append(f"It tends to do well {living_phrase}")
    if kids_desc:
        sentence2_parts.append(f"and is {kids_desc}")
    if allergy_phrase:
        sentence2_parts.append(allergy_phrase)

    sentence2 = ""
    if sentence2_parts:
        sentence2 = " ".join(sentence2_parts) + "."

    return f"{sentence1} {sentence2}".strip()


def recommend_breeds_with_cards(
    dog_breeds: pd.DataFrame,
    energy: str,
    living: str,
    allergies: str,
    children: str,
    size: str,
) -> List[Dict[str, Any]]:
    """
    Recommend the top 3 dog breeds as rich 'cards' including
    breed name, a best-guess image URL, a dataset link, and a
    short explanation text.

    Returns:
        List[dict]: Up to three recommendation cards.
    """
    if dog_breeds is None or dog_breeds.empty:
        return []

    df = _prepare_breed_dataframe(dog_breeds)

    # Compute scores
    df["match_score"] = df.apply(
        lambda row: _score_breed(row, energy, living, allergies, children, size),
        axis=1,
    )

    # Filter weak matches (score 0)
    df = df[df["match_score"] > 0]

    if df.empty:
        return []

    df_sorted = df.sort_values(by="match_score", ascending=False).head(3)

    cards: List[Dict[str, Any]] = []

    for _, row in df_sorted.iterrows():
        breed_name = str(row.get("Breed", "Unknown breed"))
        img_info = _build_image_url_and_link(breed_name)

        summary_text = _build_summary_text(
            breed_name=breed_name,
            row=row,
            energy=energy,
            living=living,
            allergies=allergies,
            children=children,
            size=size,
        )

        card = {
            "breed": breed_name,
            "image_url": img_info["image_url"],
            "dataset_link": img_info["dataset_link"],
            "summary": summary_text,
            "score": row["match_score"],
        }
        cards.append(card)

    return cards

