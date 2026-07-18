import spacy
from spacy.pipeline.span_ruler import SpanRuler

def get_labels(ruler: SpanRuler) -> tuple:
    """
    Get the labels of the SpanRuler.
    
    Args:
        ruler (SpanRuler): The SpanRuler to get the labels from.
        
    Returns:
        tuple: The labels of the SpanRuler.
    """
    return ruler
.labels

# --- test ---
nlp = spacy.blank("en")
ruler = SpanRuler(nlp)

patterns = [
    {"label": "PERSON", "pattern": [{"LOWER": "john"}]},
    {"label": "GPE", "pattern": [{"LOWER": "london"}]},
]
ruler.add_patterns(patterns)
labels = get_labels(ruler)
assert isinstance(labels, tuple)
expected = ('GPE', 'PERSON')
assert labels == expected
