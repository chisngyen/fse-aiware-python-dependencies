import librosa
import numpy as np

def compute_shear(E: np.ndarray, factor: int, axis: int) -> np.ndarray:


    return librosa.util.shear(E, factor=factor, axis=axis)

# --- test ---

E = np.eye(3)
factor=-1
axis=-1

sol = compute_shear(E, factor, axis)
gt = np.array([[1., 1., 1.],
 [0., 0., 0.],
 [0., 0., 0.]])
assert np.array_equal(gt, sol)
