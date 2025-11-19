import pandas as pd

# Path for GitHub dataset images
BASE_IMAGE_URL = "https://raw.githubusercontent.com/maartenvandenbroeck/Dog-Breeds-Dataset/main/"

def recommend_breeds(df, energy, living, allergies, children, size):
    """
    Return top 3 matching dog breeds based on exact trait matching.
    """

    candidates = df.copy()

    if energy:
        candidates = candidates[candidates["energy_level"] == energy]

    if living:
        candidates = candidates[candidates["living_space"] == living]

    if allergies:
        candidates = candidates[candidates["shedding"] == allergies]

    if children:
        candidates = candidates[candidates["good_with_children"] == children]

    if size:
        candidates = candidates[candidates["size"] == size]

    return candidates.head(3)["breed"].tolist()


def recommend_breeds_with_cards(df, energy, living, allergies, children, size):
    """
    Same as recommend_breeds(), but returns dicts with:
    - breed name
    - image URL
    - summary text
    - dataset link
    """

    recs = recommend_breeds(df, energy, living, allergies, children, size)
    cards = []

    for breed in recs:
        img filename = breed.replace(" ", "_") + ".jpg"
        url = BASE_IMAGE_URL + "images/" + img_filename

        summary = (
            f"🌟 **{breed}** is a great match for your lifestyle! "
            f"It fits your energy level, living situation, allergy needs, "
            f"child preference, and size preference. "
            f"This breed is known for being friendly, loyal, and adaptable."
        )

        cards.append({
            "breed": breed,
            "image_url": url,
            "summary": summary,
            "dataset_link": "https://github.com/maartenvandenbroeck/Dog-Breeds-Dataset"
        })

    return cards
