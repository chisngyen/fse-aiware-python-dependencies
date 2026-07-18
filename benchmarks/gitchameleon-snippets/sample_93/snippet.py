import spacy
from spacy.pipeline.span_ruler import SpanRuler


def remove_pattern_by_id(ruler: SpanRuler, pattern_id: str) -> None:
    """
    Remove a pattern from the SpanRuler by its ID.
    
    Args:
        ruler (SpanRuler): The SpanRuler to remove the pattern from.
        pattern_id (str): The ID of the pattern to remove.
        
    Returns:
        None
    """
    ruler
.remove_by_id(pattern_id)

# --- test ---
nlp = spacy.blank("en")
ruler = SpanRuler(nlp)

patterns = [
    {"label": "PERSON", "pattern": [{"LOWER": "john"}], "id": "pattern1"},
    {"label": "GPE", "pattern": [{"LOWER": "london"}], "id": "pattern2"},
]
ruler.add_patterns(patterns)

assert len(ruler.patterns) == 2

pattern_id_to_remove = "pattern1"

remove_pattern_by_id(ruler, pattern_id_to_remove)
assertion_value = len(ruler.patterns) == 1 
assert assertion_value
remaining_pattern_ids = [pattern["id"] for pattern in ruler.patterns]
assertion_value = pattern_id_to_remove not in remaining_pattern_ids
assert assertion_value
