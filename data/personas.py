"""
Rich persona descriptions and baseline definitions for Terra Health Intelligence.
"""

from config import PERSONAS

def get_all_personas():
    """Return list of available personas."""
    return list(PERSONAS.values())

def get_persona_by_id(persona_id: str):
    """Retrieve persona config by ID or default to alex_longevity."""
    return PERSONAS.get(persona_id, PERSONAS["alex_longevity"])
