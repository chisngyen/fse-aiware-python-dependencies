import librosa
import numpy as np

def compute_fill_diagonal(mut_x: np.ndarray, radius: float) -> np.ndarray:


    return librosa.util.fill_off_diagonal(mut_x,  radius)

# --- test ---

mut_x = np.ones((8, 12))
radius = 0.25
assertion_value = np.array_equal(librosa.util.fill_off_diagonal(mut_x,  radius), compute_fill_diagonal(mut_x, radius))
assert assertion_value
