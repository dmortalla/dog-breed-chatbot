"""Utility functions for the Dog Breed Matchmaker chatbot.

This module contains:
- Data loading helpers.
- Simple natural language parsers for levels (low/medium/high).
- Trait description helpers using the trait_description dataset.
"""

from typing import Tuple

import pandas as pd
import streamlit as st


@st.cache_data
def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load dog breed and trait description data from CSV files.

    Returns:
        A tuple of:
        - dog_breeds: main breed traits DataFrame.
        - trait_descriptions: DataFrame with long-form trait explanations.
    """
    dog_breeds = pd.read_csv("data/breed_traits.csv")
    trait_descriptions = pd.read_csv("data/trait_description.csv")
    return dog_breeds, trait_descriptions


def parse_level_answer(text: str) -> int:
    """Convert a simple text answer into a level from 1 to 5.

    Examples:
    - "Low"  -> 1
    - "Medium" -> 3
    - "High" -> 5
    - "4" -> 4

    This keeps the logic easy to understand for new learners.

    Args:
        text: User's text description of a level.

    Returns:
        An integer between 1 and 5.
    """
    text = text.strip().lower()
    if not text:
        return 3

    if text[0].isdigit():
        # Use the first digit directly if present.
        try:
            val = int(text[0])
            return max(1, min(5, val))
        except ValueError:
            return 3

    if "low" in text:
        return 1
    if "high" in text:
        return 5
    if "medium" in text:
        return 3

    return 3


def describe_trait(
    trait_descriptions: pd.DataFrame,
    trait_name: str,
    level: float,
) -> str:
    """Create a short human-readable description for a trait.

    The app uses this to explain *why* a particular breed matches the user.

    Args:
        trait_descriptions: DataFrame of trait explanations.
        trait_name: Name of the trait to describe.
        level: Numeric level of the trait for a given breed.

    Returns:
        A short description string.
    """
    row = trait_descriptions[trait_descriptions["Trait"] == trait_name]

    if row.empty:
        return f"{trait_name}: level {int(level)}."

    base = row["Description"].iloc[0]
    return f"{base} (level {int(level)})"
