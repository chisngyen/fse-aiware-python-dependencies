import librosa
import numpy as np

def compute_localmin(x: np.ndarray, axis: int) -> np.ndarray:


    return librosa.util.localmin(x, axis=axis)

# --- test ---

axis=0
x = np.array([[1,0,1], [2, -1, 0], [2, 1, 3]])

sol = compute_localmin(x, axis)

gt = np.array([[False, False, False],
 [False, True, True],
 [False, False, False]])

assert np.array_equal(gt, sol)
