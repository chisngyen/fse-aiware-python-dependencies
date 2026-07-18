import nltk.tokenize.destructive

def tokenize_sentence(sentence: str) -> list:
    """
    Tokenize a sentence into words.
    
    Args:
        sentence (str): The sentence to tokenize.
        
    Returns:
        list: A list of tokens.
    """
    return nltk
.tokenize.destructive.NLTKWordTokenizer().tokenize(sentence)

# --- test ---
sentence = "This is a test sentence."
tokens = tokenize_sentence(sentence)
assertion_value =isinstance(tokens, list)
assert assertion_value
assertion_value = tokens == ["This", "is", "a", "test", "sentence", "."]
assert assertion_value
