from typing import Dict


def extract_traits_from_message(message: str) -> Dict[str, str]:
    """
    Extract dog-related preference traits from a user message.
    """
    # --- SAFETY FIX ---
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
        # Minimal fix — prevent "high" inside unrelated words (like "hair") from triggering energy
        if " low " in f" {msg} ":
            traits.setdefault("energy", "low")
        if " medium " in f" {msg} ":
            traits.setdefault("energy", "medium")
        if " high " in f" {msg} " and "hair" not in msg:
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
    # Minimal Fix — ONLY trigger yes/no if user explicitly refers to children
    if "kids" in msg or "children" in msg:
        if "no kids" in msg or "no children" in msg or "not good with kids" in msg:
            traits["children"] = "no"
        elif "good with kids" in msg or "good with children" in msg:
            traits["children"] = "yes"
        elif "yes" in msg:
            traits["children"] = "yes"
        elif "no" in msg:
            traits["children"] = "no"

    return traits


def merge_traits(existing: Dict[str, str], new: Dict[str, str]) -> Dict[str, str]:
    """
    Merge new traits into existing traits.
    Only overwrite if value changes.
    """
    merged = existing.copy()
    for key, value in new.items():
        if value and merged.get(key) != value:
            merged[key] = value
    return merged


def classify_off_topic(message) -> bool:
    """
    Return True only if the message is clearly irrelevant.
    MINIMAL FIX: Allow single-trait answers like 'low', 'medium', 'yes please'.
    """
    try:
        msg = str(message).lower().strip()
    except Exception:
        return False

    # 1. Accept simple answers
    trait_answers = ["low", "medium", "high", "yes", "no", "ok", "fine", "sure"]
    if msg in trait_answers:
        return False

    # 2. Accept answers mentioning any dog trait keywords
    dog_keywords = [
        "dog", "puppy", "breed", "shedding", "hair", "fur",
        "energy", "calm", "quiet", "active",
        "apartment", "house", "yard", "garden",
        "kids", "children", "family",
        "allergy", "allergies", "hypoallergenic"
    ]
    if any(k in msg for k in dog_keywords):
        return False

    # 3. True off-topic keywords
    unrelated = [
        "bitcoin", "crypto", "stock", "stocks", "recipe",
        "politics", "election", "war", "galaxy", "universe",
        "math problem", "code this", "programming"
    ]
    if any(w in msg for w in unrelated):
        return True

    # Default: treat as on-topic to avoid false negatives
    return False
