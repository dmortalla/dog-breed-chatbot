"""
Recommender engine for Dog Lover Chatbot.

This module:
- Cleans and normalizes breed names from the CSV.
- Maps them to the Dog-Breeds-Dataset folders.
- Scores breeds based on user preferences.
- Returns top-N breeds with image URLs and summaries.
"""

from typing import List, Dict, Optional, Tuple
import re

import pandas as pd


# ============================================================
# DATASET IMAGE FOLDERS (Dog-Breeds-Dataset repo)
# ============================================================

DOG_FOLDER_NAMES: List[str] = [
    "affenpinscher dog",
    "afghan hound dog",
    "airedale terrier dog",
    "akita dog",
    "alaskan malamute dog",
    "alpine dachsbracke dog",
    "american akita dog",
    "american cocker spaniel dog",
    "american foxhound dog",
    "american staffordshire terrier dog",
    "american water spaniel dog",
    "appenzell cattle dog",
    "ariege pointing dog",
    "ariegeois dog",
    "artois hound dog",
    "atlas mountain dog (aidi)",
    "australian cattle dog",
    "australian kelpie dog",
    "australian shepherd dog",
    "australian silky terrier dog",
    "australian stumpy tail cattle dog",
    "australian terrier dog",
    "austrian pinscher dog",
    "austrian black and tan hound dog",
    "auvergne pointer dog",
    "azawakh dog",
    "basenji dog",
    "basset fauve de bretagne dog",
    "basset hound dog",
    "bavarian mountain scent hound dog",
    "beagle dog",
    "beagle harrier dog",
    "bearded collie dog",
    "bedlington terrier dog",
    "belgian shepherd dog",
    "bergamasco shepherd dog",
    "berger de beauce dog",
    "bernese mountain dog",
    "bichon frise dog",
    "billy dog",
    "black and tan coonhound dog",
    "bloodhound dog",
    "blue gascony basset dog",
    "blue gascony griffon dog",
    "blue picardy spaniel dog",
    "bohemian shepherd dog",
    "bohemian wire-haired pointing griffon dog",
    "bolognese dog",
    "border collie dog",
    "border terrier dog",
    "borzoi - russian hunting sighthound dog",
    "bosnian and herzegovinian - croatian shepherd dog",
    "bosnian broken-haired hound - called barak dog",
    "boston terrier dog",
    "bourbonnais pointing dog",
    "bouvier des ardennes dog",
    "bouvier des flandres dog",
    "boxer dog",
    "brazilian terrier dog",
    "brazilian tracker dog",
    "briard dog",
    "briquet griffon vendeen dog",
    "brittany spaniel dog",
    "broholmer dog",
    "bull terrier dog",
    "bulldog",
    "bullmastiff dog",
    "burgos pointing dog",
    "cairn terrier dog",
    "canaan dog",
    "canadian eskimo dog",
    "canarian warren hound dog",
    "castro laboreiro dog",
    "catalan sheepdog",
    "caucasian shepherd dog",
    "cavalier king charles spaniel dog",
    "central asia shepherd dog",
    "cesky terrier dog",
    "chesapeake bay retriever dog",
    "chihuahua dog",
    "chinese crested dog",
    "chow chow dog",
    "cimarrón uruguayo dog",
    "cirneco dell'etna dog",
    "clumber spaniel dog",
    "coarse-haired styrian hound dog",
    "collie rough dog",
    "collie smooth dog",
    "continental bulldog",
    "continental toy spaniel dog",
    "coton de tulear dog",
    "croatian shepherd dog",
    "curly coated retriever dog",
    "czechoslovakian wolfdog",
    "dachshund dog",
    "dalmatian dog",
    "dandie dinmont terrier dog",
    "danish-swedish farmdog",
    "deerhound dog",
    "deutsch langhaar dog",
    "deutsch stichelhaar dog",
    "dobermann dog",
    "dogo argentino",
    "dogue de bordeaux",
    "drentsche partridge dog",
    "drever dog",
    "dutch schapendoes dog",
    "dutch shepherd dog",
    "dutch smoushond dog",
    "east siberian laika dog",
    "english cocker spaniel dog",
    "english foxhound dog",
    "english pointer dog",
    "english setter dog",
    "english springer spaniel dog",
    "english toy terrier (black &tan) dog",
    "entlebuch cattle dog",
    "estonian hound dog",
    "estrela mountain dog",
    "eurasian dog",
    "fawn brittany griffon dog",
    "field spaniel dog",
    "fila brasileiro dog",
    "finnish hound dog",
    "finnish lapponian dog",
    "finnish spitz dog",
    "flat coated retriever dog",
    "fox terrier (smooth) dog",
    "fox terrier (wire) dog",
    "french bulldog",
    "french pointing dog - pyrenean type",
    "french spaniel dog",
    "french tricolour hound dog",
    "french water dog",
    "french white & black hound dog",
    "french white and orange hound dog",
    "frisian water dog",
    "gascon saintongeois dog",
    "german hound dog",
    "german hunting terrier dog",
    "german pinscher dog",
    "german shepherd dog",
    "german short- haired pointing dog",
    "german spaniel dog",
    "german spitz dog",
    "german wire- haired pointing dog",
    "giant schnauzer dog",
    "golden retriever dog",
    "gordon setter dog",
    "grand basset griffon vendeen dog",
    "grand griffon vendeen dog",
    "great anglo-french tricolour hound dog",
    "great anglo-french white & orange hound dog",
    "great anglo-french white and black hound dog",
    "great dane dog",
    "great gascony blue dog",
    "great swiss mountain dog",
    "greenland dog",
    "greyhound dog",
    "griffon belge dog",
    "griffon bruxellois dog",
    "griffon nivernais dog",
    "halden hound dog",
    "hamiltonstövare dog",
    "hanoverian scent hound dog",
    "harrier dog",
    "havanese dog",
    "hellenic hound dog",
    "hokkaido dog",
    "hovawart dog",
    "hungarian greyhound dog",
    "hungarian hound - transylvanian scent hound dog",
    "hungarian short-haired pointer (vizsla) dog",
    "hungarian wire-haired pointer dog",
    "hygen hound dog",
    "ibizan podenco dog",
    "icelandic sheepdog",
    "irish glen of imaal terrier dog",
    "irish red and white setter dog",
    "irish red setter dog",
    "irish soft coated wheaten terrier dog",
    "irish terrier dog",
    "irish water spaniel dog",
    "irish wolfhound dog",
    "istrian short-haired hound dog",
    "istrian wire-haired hound dog",
    "italian cane corso dog",
    "italian pointing dog",
    "italian rough-haired segugio dog",
    "italian short-haired segugio dog",
    "italian sighthound dog",
    "italian spinone dog",
    "italian volpino dog",
    "jack russell terrier dog",
    "japanese chin dog",
    "japanese spitz dog",
    "japanese terrier dog",
    "jämthund dog",
    "kai dog",
    "kangal shepherd dog",
    "karelian bear dog",
    "karst shepherd dog",
    "kerry blue terrier dog",
    "king charles spaniel dog",
    "kintamani-bali dog",
    "kishu dog",
    "kleiner münsterländer dog",
    "komondor dog",
    "korea jindo dog",
    "kromfohrländer dog",
    "kuvasz dog",
    "labrador retriever dog",
    "lakeland terrier dog",
    "lancashire heeler dog",
    "landseer (european continental type) dog",
    "lapponian herder dog",
    "large munsterlander dog",
    "leonberger dog",
    "lhasa apso dog",
    "little lion dog",
    "long-haired pyrenean sheepdog",
    "majorca mastiff dog",
    "majorca shepherd dog",
    "maltese dog",
    "manchester terrier dog",
    "maremma and the abruzzes sheepdog",
    "mastiff dog",
    "medium-sized anglo-french hound dog",
    "miniature american shepherd dog",
    "miniature bull terrier dog",
    "miniature pinscher dog",
    "miniature schnauzer dog",
    "montenegrin mountain hound dog",
    "mudi dog",
    "neapolitan mastiff dog",
    "nederlandse kooikerhondje dog",
    "newfoundland dog",
    "norfolk terrier dog",
    "norman artesien basset dog",
    "norrbottenspitz dog",
    "norwegian buhund dog",
    "norwegian elkhound black dog",
    "norwegian elkhound grey dog",
    "norwegian hound dog",
    "norwegian lundehund dog",
    "norwich terrier dog",
    "nova scotia duck tolling retriever dog",
    "old danish pointing dog",
    "old english sheepdog",
    "otterhound dog",
    "parson russell terrier dog",
    "pekingese dog",
    "peruvian hairless dog",
    "petit basset griffon vendeen dog",
    "petit brabançon dog",
    "pharaoh hound dog",
    "picardy sheepdog",
    "picardy spaniel dog",
    "poitevin dog",
    "polish greyhound dog",
    "polish hound dog",
    "polish hunting dog",
    "polish lowland sheepdog",
    "pont-audemer spaniel dog",
    "poodle dog",
    "porcelaine dog",
    "portuguese pointing dog",
    "portuguese sheepdog",
    "portuguese warren hound-portuguese podengo dog",
    "portuguese water dog",
    "posavatz hound dog",
    "prague ratter dog",
    "presa canario dog",
    "pudelpointer dog",
    "pug dog",
    "puli dog",
    "pumi dog",
    "pyrenean mastiff dog",
    "pyrenean mountain dog",
    "pyrenean sheepdog - smooth faced",
    "rafeiro of alentejo dog",
    "rhodesian ridgeback dog",
    "romagna water dog",
    "romanian bucovina shepherd dog",
    "romanian carpathian shepherd dog",
    "romanian mioritic shepherd dog",
    "rottweiler dog",
    "russian black terrier dog",
    "russian toy dog",
    "russian-european laika dog",
    "saarloos wolfhond dog",
    "saint germain pointer dog",
    "saint miguel cattle dog",
    "saluki dog",
    "samoyed dog",
    "schillerstövare dog",
    "schipperke dog",
    "schnauzer dog",
    "scottish terrier dog",
    "sealyham terrier dog",
    "segugio maremmano dog",
    "serbian hound dog",
    "serbian tricolour hound dog",
    "shar pei dog",
    "shetland sheepdog",
    "shiba dog",
    "shih tzu dog",
    "shikoku dog",
    "siberian husky dog",
    "skye terrier dog",
    "sloughi dog",
    "slovakian chuvach dog",
    "slovakian hound dog",
    "small blue gascony dog",
    "small swiss hound dog",
    "smålandsstövare dog",
    "south russian shepherd dog",
    "spanish greyhound dog",
    "spanish hound dog",
    "spanish mastiff dog",
    "spanish water dog",
    "st. bernard dog",
    "stabijhoun dog",
    "staffordshire bull terrier dog",
    "sussex spaniel dog",
    "swedish lapphund dog",
    "swedish vallhund dog",
    "swiss hound dog",
    "taiwan dog",
    "tatra shepherd dog",
    "thai bangkaew dog",
    "thai ridgeback dog",
    "tibetan mastiff dog",
    "tibetan spaniel dog",
    "tibetan terrier dog",
    "tosa dog",
    "transmontano mastiff dog",
    "tyrolean hound dog",
    "valencian terrier dog",
    "weimaraner dog",
    "welsh corgi (cardigan) dog",
    "welsh corgi (pembroke) dog",
    "welsh springer spaniel dog",
    "welsh terrier dog",
    "west highland white terrier dog",
    "west siberian laika dog",
    "westphalian dachsbracke dog",
    "whippet dog",
    "white swiss shepherd dog",
    "wire-haired pointing griffon korthals dog",
    "wirehaired slovakian pointer dog",
    "xoloitzcuintle dog",
    "yakutian laika dog",
    "yorkshire terrier dog",
    "yugoslavian shepherd dog - sharplanina",
]

BASE_IMAGE_URL = (
    "https://raw.githubusercontent.com/maartenvandenbroeck/"
    "Dog-Breeds-Dataset/main"
)


# ============================================================
# TEXT NORMALIZATION HELPERS
# ============================================================

def _clean_text(text: str) -> str:
    """Basic cleanup: remove encoding junk, normalize spaces, lowercase."""
    if not isinstance(text, str):
        return ""
    # Fix common encoding artifacts
    text = text.replace("Â", " ").replace("â€™", "'")
    # Collapse whitespace
    text = " ".join(text.split())
    return text.strip()


def _words(text: str) -> List[str]:
    """
    Split text into normalized, roughly singular words.

    Example:
        'Retrievers (Labrador)' -> ['retriever', 'labrador']
    """
    text = _clean_text(text).lower()
    # Only letters
    tokens = re.findall(r"[a-z]+", text)
    cleaned: List[str] = []
    for t in tokens:
        # Rough singularization: remove trailing 's' for longer words
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        cleaned.append(t)
    return cleaned


def _folder_word_index() -> List[Tuple[str, set]]:
    """Precompute (folder, word_set) for all known dataset folders."""
    result: List[Tuple[str, set]] = []
    for folder in DOG_FOLDER_NAMES:
        w = set(_words(folder.replace("dog", "")))
        result.append((folder, w))
    return result


_FOLDER_INDEX = _folder_word_index()


def map_breed_to_folder(breed_name: str) -> Optional[str]:
    """
    Map a CSV breed name to the most likely Dog-Breeds-Dataset folder.

    Uses word overlap between cleaned breed name and folder names.
    Returns None if no reasonable overlap is found.
    """
    breed_words = set(_words(breed_name))
    if not breed_words:
        return None

    best_folder: Optional[str] = None
    best_overlap = 0

    for folder, folder_words in _FOLDER_INDEX:
        overlap = len(breed_words & folder_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_folder = folder

    # Require at least one overlapping word to accept a match
    if best_overlap == 0:
        return None

    return best_folder


# ============================================================
# SCORING
# ============================================================

def _to_int(value) -> Optional[int]:
    """Convert trait value to int 1–5, or None if not possible."""
    try:
        val = int(value)
        if 1 <= val <= 5:
            return val
    except Exception:
        return None
    return None


def score_breed_row(
    row: pd.Series,
    energy_pref: Optional[str],
    living_pref: Optional[str],
    allergy_pref: Optional[str],
    children_pref: Optional[str],
) -> float:
    """
    Compute a match score in [0.0, 1.0] for a single breed row.
    Higher is better.
    """
    scores: List[float] = []

    # Energy Level
    if energy_pref:
        target_map = {"low": 1.5, "medium": 3.0, "high": 4.5}
        target = target_map.get(energy_pref)
        val = _to_int(row.get("Energy Level"))
        if target is not None and val is not None:
            scores.append(max(0.0, 1.0 - abs(val - target) / 4.0))

    # Shedding / allergies
    if allergy_pref in ("low-shedding", "hypoallergenic"):
        val = _to_int(row.get("Shedding Level"))
        if val is not None:
            # 1 = lowest shedding, 5 = highest
            scores.append(max(0.0, 1.0 - (val - 1) / 4.0))

    # Children
    if children_pref in ("yes", "no"):
        val = _to_int(row.get("Good With Young Children"))
        if val is not None:
            target = 5.0 if children_pref == "yes" else 1.0
            scores.append(max(0.0, 1.0 - abs(val - target) / 4.0))

    # Living situation (apartment -> care about adaptability & barking)
    living = (living_pref or "").lower()
    if living in ("small apartment", "standard apartment"):
        adapt = _to_int(row.get("Adaptability Level"))
        bark = _to_int(row.get("Barking Level"))
        if adapt is not None:
            scores.append(max(0.0, (adapt - 1) / 4.0))  # higher better
        if bark is not None:
            scores.append(max(0.0, 1.0 - (bark - 1) / 4.0))  # lower better

    if not scores:
        return 0.0

    return float(sum(scores) / len(scores))


# ============================================================
# PUBLIC API
# ============================================================

def recommend_breeds_with_cards(
    dog_breeds: pd.DataFrame,
    energy_pref: Optional[str],
    living_pref: Optional[str],
    allergy_pref: Optional[str],
    children_pref: Optional[str],
    size_pref: Optional[str],  # currently not used in scoring, just in summary
    top_n: int = 3,
) -> List[Dict[str, str]]:
    """
    Recommend top-N dog breeds as rich cards.

    Args:
        dog_breeds: DataFrame of breed traits.
        energy_pref: 'low' | 'medium' | 'high' or None.
        living_pref: 'small apartment' | 'standard apartment' | 'house with a yard' or None.
        allergy_pref: 'low-shedding' | 'hypoallergenic' | None.
        children_pref: 'yes' | 'no' | None.
        size_pref: 'small' | 'medium' | 'large' | None.
        top_n: Number of breeds to return.

    Returns:
        A list of dicts with:
            - 'breed': display name
            - 'image_url': GitHub raw image URL
            - 'match_pct': integer percent match
            - 'summary': markdown summary string
    """
    if dog_breeds is None or dog_breeds.empty:
        return []

    df = dog_breeds.copy()

    # Clean breed names
    df["Breed_clean"] = df["Breed"].apply(_clean_text)

    # Map to folders
    df["folder"] = df["Breed_clean"].apply(map_breed_to_folder)

    # Drop rows without a folder match
    df = df.dropna(subset=["folder"])
    if df.empty:
        return []

    # Compute scores
    df["score"] = df.apply(
        lambda row: score_breed_row(
            row,
            energy_pref=energy_pref,
            living_pref=living_pref,
            allergy_pref=allergy_pref,
            children_pref=children_pref,
        ),
        axis=1,
    )

    # Keep only positive scores
    df = df[df["score"] > 0.0]
    if df.empty:
        return []

    # Sort by descending score
    df = df.sort_values("score", ascending=False)

    cards: List[Dict[str, str]] = []

    for _, row in df.head(top_n).iterrows():
        breed_name = row["Breed_clean"]
        folder = row["folder"]
        score = float(row["score"])
        match_pct = int(round(score * 100))

        image_url = f"{BASE_IMAGE_URL}/{folder}/Image_1.jpg"

        # Build a simple summary using preferences and trait values
        energy_val = row.get("Energy Level", "")
        shed_val = row.get("Shedding Level", "")
        child_val = row.get("Good With Young Children", "")
        adapt_val = row.get("Adaptability Level", "")
        bark_val = row.get("Barking Level", "")

        summary = (
            f"**Match score:** {match_pct}%\n\n"
            f"**Why {breed_name} fits you:**\n"
            f"- Energy level trait: **{energy_val} / 5**\n"
            f"- Shedding level trait: **{shed_val} / 5**\n"
            f"- Good with young children: **{child_val} / 5**\n"
            f"- Adaptability: **{adapt_val} / 5**\n"
            f"- Barking level: **{bark_val} / 5**\n\n"
            f"Based on your preferences for energy, living space, allergies, and children, "
            f"the **{breed_name}** is a strong candidate for your lifestyle. 🐾"
        )

        cards.append(
            {
                "breed": breed_name,
                "image_url": image_url,
                "match_pct": match_pct,
                "summary": summary,
            }
        )

    return cards


