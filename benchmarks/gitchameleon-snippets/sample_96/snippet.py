import nltk
nltk.download('sinica_treebank')
from nltk.tree import Tree
from nltk.corpus import sinica_treebank

def parse_sinica_treebank_sentence(sentence: str) -> Tree:
    """
    Parse a sentence from the Sinica Treebank.
    
    Args:
        sentence (str): The sentence to parse.
        
    Returns:
        Tree: The parsed tree.
    """
    return
Tree.fromstring(sentence)

# --- test ---
sinica_sentence = sinica_treebank.parsed_sents()[0]
tree_string = sinica_sentence.pformat()

parsed_tree = parse_sinica_treebank_sentence(tree_string)
assertion_value =isinstance(parsed_tree, Tree)
assert assertion_value
assertion_value = parsed_tree.label() == "NP"
assert assertion_value
