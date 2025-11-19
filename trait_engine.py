from __future__ import annotations
from typing import Dict, Optional


# ============================================================
# LOW-LEVEL TRAIT EXTRACTORS
# ============================================================

def _extract_energy(text: str) -> Optional[int]:
    """Return 1 (low), 3 (medium), or 5 (high) based on natural language."""
    t = text.lower()

    low_words = [
        "low energy",
        "very low",
        "calm",
        "chill",
        "relaxed",
        "quiet dog",
        "quiet and calm",
        "not very active",
        "doesn't make too much noise",
        "doesnt make too much noise",
        "not make too much noise",
        "couch potato",
    ]
    if any(w in t for w in low_words):
        return 1
    # Simple "low" but not in "low shedding"
    if "low" in t and "low shedding" not in t and "low-shedding" not in t:
        return 1

    med_words = [
        "medium energy",
        "moderate energy",
        "in the middle",
        "not too active",
        "balanced energy",
    ]
    if any(w in t for w in med_words):
        return 3

    high_words = [
        "high energy",
        "very active",
        "hyper",
        "energetic",
        "sporty",
        "runner",
    ]
    if any(w in t for w in high_words):
        return 5
    if "high" in t:
        return 5

    return None


def _extract_home(text: str) -> Optional[int]:
    """Return 1–2 = apartment, 4–5 = house/yard."""
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
    """Return 1 = hypoallergenic, 2 = low shedding, 4 = shedding ok."""
    t = text.lower()

    # Hypoallergenic / allergy-focused
    if "hypoallergenic" in t:
        return 1

    if "allergy" in t or "allergies" in t or "asthma" in t:
        # If allergies are mentioned at all, assume they care about shedding
        return 2

    # Broad set of "low shedding" phrases
    low_shed_patterns = [
        "low-shedding",
        "low shedding",
        "little shedding",
        "minimal shedding",
        "hardly sheds",
        "barely sheds",
        "doesn't shed much",
        "doesnt shed much",
        "doesn't shed too much",
        "doesnt shed too much",
        "doesn't shed much hair",
        "doesnt shed much hair",
        "doesn't shed too much hair",
        "doesnt shed too much hair",
        "not shed much hair",
        "not shed too much hair",
        "don't shed much hair",
        "dont shed much hair",
        "don't shed too much hair",
        "dont shed too much hair",
        "shed much hair",          # often used with a negation in the sentence
        "shed too much hair",
        "shed much fur",
        "shed too much fur",
    ]
    if any(p in t for p in low_shed_patterns):
        return 2

    # Explicitly relaxed about shedding
    if "i don't mind shedding" in t or "shedding is fine" in t:
        return 4

    return None


def _extract_kids(text: str) -> Optional[int]:
    """Return 5 if kid-friendly desired; 1 if explicitly not; None if not mentioned."""
    t = text.lower()

    if not any(w in t for w in ["kid", "kids", "child", "children", "baby", "toddler", "family"]):
        return None

    yes_words = ["yes", "important", "must", "should", "need", "absolutely", "be good with"]
    if any(w in t for w in yes_words):
        return 5

    no_words = ["no", "not important", "doesn't matter", "don't care"]
    if any(w in t for w in no_words):
        return 1

    return 5


# ============================================================
# PUBLIC API — PARSE USER PREFERENCES
# ============================================================

def parse_preferences(text: str) -> Dict[str, int]:
    """Parse user text and return a dictionary of extracted traits."""
    prefs = {}

    e = _extract_energy(text)
    if e is not None:
        prefs["energy"] = e

    h = _extract_home(text)
    if h is not None:
        prefs["home"] = h

    a = _extract_allergies(text)
    if a is not None:
        prefs["allergies"] = a

    k = _extract_kids(text)
    if k is not None:
        prefs["kids"] = k

    return prefs


# ============================================================
# OFF-TOPIC CLASSIFICATION
# ============================================================

GENERAL_DOG_WORDS = [
    "dog", "dogs", "breed", "breeds", "puppy", "puppies", "pet",
    "canine", "walk", "leash", "bark", "coat", "fur"
]

YES_NO = {
    "yes", "yes.", "yes!", "yes please", "yes please.",
    "yep", "yeah", "sure", "of course", "okay", "ok", "ok!",
    "no", "no.", "no!", "no thanks", "no thank you",
    "nope", "not really"
}


def classify_off_topic(text: str, extracted: dict) -> bool:
    """
    Return True only if the message is genuinely off-topic.

    A message is OFF TOPIC only if:
    - No new traits were extracted
    - AND it does not match any dog/lifestyle keywords
    - AND it is not a simple confirmation (yes/no/ok/etc.)
    """

    t = text.lower().strip()

    # If any trait was extracted → topic is valid
    if extracted:
        return False

    # Accept simple confirmations as valid
    confirmations = ["yes", "yep", "yeah", "sure", "ok", "okay", "that's fine",
                     "sounds good", "fine", "alright", "go ahead"]
    if any(t.startswith(c) for c in confirmations):
        return False

    # Dog-related keywords that still count as on-topic
    dog_keywords = [
        "dog", "puppy", "breed", "shedding", "hair", "fur",
        "energy", "calm", "quiet", "active", "yard",
        "apartment", "house", "kids", "children",
        "family", "allergy", "allergies", "hypoallergenic"
    ]
    if any(k in t for k in dog_keywords):
        return False

    # Otherwise off-topic
    return True


# ============================================================
# HUMAN-FRIENDLY MEMORY SUMMARY
# ============================================================

def summarize_preferences(prefs: Dict[str, int]) -> str:
    if not prefs:
        return ("Tell me about your activity level, home size, allergies, "
                "or whether you have kids — I’ll learn as we chat!")

    parts = []

    if (e := prefs.get("energy")) is not None:
        parts.append(
            "You prefer a calmer dog." if e <= 2 else
            "You’re okay with medium energy." if e == 3 else
            "You want a high-energy, active dog."
        )

    if (h := prefs.get("home")) is not None:
        parts.append(
            "You live in an apartment or smaller space." if h <= 2 else
            "You have more space, like a house or yard."
        )

    if (a := prefs.get("allergies")) is not None:
        parts.append(
            "Low-shedding or hypoallergenic coats matter to you." if a <= 2 else
            "You’re flexible about shedding."
        )

    if (k := prefs.get("kids")) is not None:
        parts.append(
            "Good with young children is important." if k >= 4 else
            "Kid-friendliness is less critical."
        )

    return " ".join(parts)
