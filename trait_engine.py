from __future__ import annotations

from typing import Dict, Optional


# ============================================================
# Low-level trait extractors
# ============================================================

def _extract_energy(text: str) -> Optional[int]:
    """Return 1 (low), 3 (medium), or 5 (high) based on natural language."""
    t = text.lower()

    # Low energy
    low_words = ["low energy", "very low", "calm", "chill", "relaxed", "couch", "quiet dog"]
    if any(w in t for w in low_words):
        return 1
    if "low" in t and "low shedding" not in t:
        # avoid confusion with low-shedding
        return 1

    # Medium energy
    med_words = ["medium", "moderate", "in the middle", "not too active", "balanced energy"]
    if any(w in t for w in med_words):
        return 3

    # High energy
    high_words = ["high energy", "very active", "hyper", "energetic", "sporty", "runner"]
    if any(w in t for w in high_words):
        return 5
    if "high" in t:
        return 5

    return None


def _extract_home(text: str) -> Optional[int]:
    """
    Return 1–2 for smaller spaces (apartments), 5 for larger spaces (house/yard).
    """
    t = text.lower()

    small_words = ["studio", "small apartment", "tiny apartment", "condo"]
    if any(w in t for w in small_words):
        return 1

    if "apartment" in t or "flat" in t:
        return 2

    big_words = ["yard", "garden", "big house", "house with a yard", "suburbs"]
    if any(w in t for w in big_words):
        return 5
    if "house" in t or "home" in t:
        return 4

    return None


def _extract_allergies(text: str) -> Optional[int]:
    """
    Lower values mean stronger allergy concern.
    1 = hypoallergenic, 2 = low shedding, higher values = less concern.
    """
    t = text.lower()

    if "hypoallergenic" in t:
        return 1

    low_shed_words = ["low-shedding", "low shedding", "doesn't shed much", "minimal shedding"]
    if any(w in t for w in low_shed_words):
        return 2

    if "allergies" in t or "allergy" in t or "asthma" in t:
        # concerned but not specific
        return 2

    if "i don't mind shedding" in t or "shedding is fine" in t:
        return 4

    return None


def _extract_kids(text: str) -> Optional[int]:
    """
    Return 5 if good-with-kids is important, 1 if not important, None if not mentioned.
    """
    t = text.lower()
    if not any(w in t for w in ["kid", "kids", "child", "children", "baby", "toddler", "family"]):
        return None

    # Positive
    yes_words = ["yes", "important", "must", "should", "need", "absolutely", "be good with"]
    if any(w in t for w in yes_words):
        return 5

    no_words = ["no", "not important", "doesn't matter", "don't care"]
    if any(w in t for w in no_words):
        return 1

    # If kids mentioned but no polarity, assume important
    return 5


# ============================================================
# Public API: preference parsing
# ============================================================

def parse_preferences(text: str) -> Dict[str, int]:
    """
    Parse user text into structured preferences.

    Returns:
        Dict with possible keys: "energy", "home", "allergies", "kids".
        Values are ints compatible with the recommender.
    """
    prefs: Dict[str, int] = {}

    energy = _extract_energy(text)
    if energy is not None:
        prefs["energy"] = energy

    home = _extract_home(text)
    if home is not None:
        prefs["home"] = home

    allergies = _extract_allergies(text)
    if allergies is not None:
        prefs["allergies"] = allergies

    kids = _extract_kids(text)
    if kids is not None:
        prefs["kids"] = kids

    return prefs


# ============================================================
# Off-topic classifier
# ============================================================

GENERAL_DOG_WORDS = [
    "dog", "dogs", "breed", "breeds", "puppy", "puppies", "pet", "pets", "canine",
    "walk", "leash", "bark", "coat", "fur",
]


def classify_off_topic(
    text: str,
    step: int,
    new_prefs: Dict[str, int],
) -> bool:
    """
    Decide whether a user message is off-topic for the dog-matching use case.

    Args:
        text: Raw user message.
        step: Conversation step (0 = intro, 1 = energy, 2 = home, 3 = allergies, 4 = kids, >=5 = recommend).
        new_prefs: Preferences parsed from this single message.

    Returns:
        True if the message is clearly off-topic, False otherwise.
    """
    t = text.lower()

    # Intro step: accept almost anything
    if step == 0:
        return False

    # If we detected any new preference, it's definitely on-topic
    if new_prefs:
        return False

    # Step-specific hints even if parse missed it
    if step == 1 and any(w in t for w in ["low", "medium", "high", "moderate", "energetic", "calm"]):
        return False

    if step == 2 and any(w in t for w in ["apartment", "flat", "house", "home", "yard", "garden", "space"]):
        return False

    if step == 3 and any(w in t for w in ["allergy", "allergies", "hypoallergenic", "shedding", "shed", "dander"]):
        return False

    if step == 4 and any(w in t for w in ["kid", "kids", "child", "children", "baby", "toddler", "family"]):
        return False

    # Generic dog-related words mean it's still somewhat on-topic
    if any(w in t for w in GENERAL_DOG_WORDS):
        return False

    # Otherwise, likely off-topic (e.g., "tell me a joke", "what's the weather?")
    return True


# ============================================================
# Memory summary helper
# ============================================================

def summarize_preferences(prefs: Dict[str, int]) -> str:
    """
    Human-readable memory summary used in the sidebar.
    """
    if not prefs:
        return (
            "I don’t know much yet. Tell me about your activity level, "
            "living situation, allergies, or whether you have kids."
        )

    parts: list[str] = []

    energy = prefs.get("energy")
    if energy is not None:
        if energy <= 2:
            parts.append("You prefer a calmer, lower-energy dog.")
        elif energy == 3:
            parts.append("You’re okay with a medium-energy dog.")
        else:
            parts.append("You’d like a high-energy, active dog.")

    home = prefs.get("home")
    if home is not None:
        if home <= 2:
            parts.append("You mentioned living in an apartment or smaller space.")
        else:
            parts.append("You seem to have more space, like a house or yard.")

    allergies = prefs.get("allergies")
    if allergies is not None:
        if allergies <= 2:
            parts.append("Low shedding or hypoallergenic coats are important for you.")
        else:
            parts.append("You’re flexible about shedding and allergies.")

    kids = prefs.get("kids")
    if kids is not None:
        if kids >= 4:
            parts.append("Being good with young children is important.")
        else:
            parts.append("Kid-friendliness is less critical for you.")

    return " ".join(parts)
