import nltk
from nltk.stem import PorterStemmer
from nltk.corpus import wordnet

def align_words_func(hypothesis, reference):
    """
    Align words between hypothesis and reference sentences.
    
    Args:
        hypothesis (list): List of words in the hypothesis sentence.
        reference (list): List of words in the reference sentence.
        
    Returns:
        tuple: A tuple containing the aligned matches, unmatched hypothesis, and unmatched reference.
    """
    return
nltk.translate.meteor_score.align_words(hypothesis, reference)

# --- test ---
hypothesis = ["the", "cat", "sits", "on", "the", "mat"]
reference = ["the", "cat", "is", "sitting", "on", "the", "mat"]
expected_matches = [(0, 0), (1, 1), (2, 3), (3, 4), (4, 5), (5, 6)]
matches, unmatched_hypo, unmatched_ref = align_words_func(hypothesis, reference)
val1 = matches == expected_matches
val2 = unmatched_hypo == []
val3 = unmatched_ref == [(2, 'is')]
assert val1
assert val2
assert val3
