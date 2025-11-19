from typing import Dict


def extract_traits_from_message(message: str) -> Dict[str, str]:
    """
    Extract dog-related preference traits from a user message.
    """
    # --- SAFETY FIX: force message into a lowercase string ---
    msg = str(message).lower().strip()

    traits: Dict[str, str] = {}

    # -------- ENERGY --------
    if any(p in msg for p in ["low energy", "very calm", "calm dog", "not very active", "couch potato"]):
        traits["energy"] = "low"
    elif any(p in msg for p in ["medium energy", "moderate energy", "in the middle"]):
        traits["energy"] = "medium"
    elif any(p in msg for p in ["high energy", "very active", "energetic", "hyper"]):
        traits["energy"] = "high"
    else:
        if "low energy" in msg or ("low" in msg and "shed" not in msg):
            traits.setdefault("energy", "low")
        if "medium energy" in msg or "medium" in msg:
            traits.setdefault("energy", "medium")
        if "high energy" in msg or "high" in msg:
            traits.setdefault("energy", "high")

    # -------- LIVING SPACE --------
    if "small apartment" in msg or "tiny apartment" in msg or "studio" in msg:
        traits["living_space"] = "small apartment"
    elif "apartment" in msg:
        traits["living_space"] = "standard apartment"
    elif any(p in msg for p in ["house with a yard", "yard", "garden", "big house", "house and yard"]):
        traits["living_space"] = "house with a yard"

    # -------- SHEDDING / ALLERGIES --------
    if "hypoallergenic" in msg:
        traits["shedding"] = "hypoallergenic"
    else:
        low_shed_patterns = [
            "low-shedding", "low shedding", "doesn't shed much", "doesnt shed much",
            "doesn't shed too much", "doesnt shed too much", "doesn't shed much hair",
            "doesnt shed much hair", "doesn't shed too much hair", "doesnt shed too much hair",
            "not shed much hair", "not shed too much hair", "don't shed much hair",
            "dont shed much hair", "don't shed too much hair", "dont shed too much hair",
            "little shedding", "minimal shedding", "hardly sheds", "barely sheds",
        ]
        if any(p in msg for p in low_shed_patterns):
            traits["shedding"] = "low-shedding"
        elif "i don't mind shedding" in msg or "shedding is fine" in msg:
            traits["shedding"] = "shedding ok"

    # -------- CHILDREN --------
    if any(p in msg for p in ["yes", "yep", "yeah", "sure"]) and "no " not in msg:
        traits.setdefault("children", "yes")
    if any(p in msg for p in ["no", "nope", "not really"]) and "yes" not in msg:
        traits.setdefault("children", "no")

    if "kids" in msg or "children" in msg:
        if "no kids" in msg or "no children" in msg:
            traits["children"] = "no"
        elif "good with kids" in msg or "good with children" in msg:
            traits["children"] = "yes"

    return traits


def merge_traits(existing: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """
    Merge new traits into existing traits.

    If a trait already exists and the new value is non-empty, overwrite with the new value.
    """
    merged = existing.copy()
    for key, value in new.items():
        if value is not None and value != "":
            merged[key] = value
    return merged


def classify_off_topic(message) -> bool:
    """
    Return True only if the message is genuinely off-topic.

    A message is considered ON-TOPIC if:
      - It mentions dogs, breeds, lifestyle, or traits we care about, or
      - It is a simple confirmation like 'yes', 'no', 'sure', etc.
    """
    # Be robust to non-string inputs (e.g., mic recorder objects)
    try:
        msg = str(message).lower().strip()
    except Exception:
        return False  # treat as on-topic rather than crashing

    confirmations = [
        "yes", "yep", "yeah", "sure", "ok", "okay",
        "sounds good", "fine", "correct", "that's right"
    ]
    if msg in confirmations:
        return False

    dog_keywords = [
        "dog", "puppy", "breed", "shedding", "hair", "fur",
        "energy", "calm", "quiet", "active",
        "apartment", "house", "yard", "garden",
        "kids", "children", "family",
        "allergy", "allergies", "hypoallergenic"
    ]
    if any(k in msg for k in dog_keywords):
        return False

    unrelated = [
        "bitcoin", "crypto", "stock", "stocks", "recipe",
        "politics", "election", "war", "galaxy", "universe",
        "math problem", "code this", "programming"
    ]
    if any(w in msg for w in unrelated):
        return True

    return False
