import librosa
import numpy as np

def compute_shear(E: np.ndarray, factor: int, axis: int) -> np.ndarray:


    E_shear = np.empty_like(E)
    for i in range(E.shape[1]):
        E_shear[:, i] = np.roll(E[:, i], factor * i)
    return E_shear

# --- test ---

E = np.eye(3)
factor=-1
axis=-1

sol = compute_shear(E, factor, axis)
gt = np.array([[1., 1., 1.],
 [0., 0., 0.],
 [0., 0., 0.]])
assert np.array_equal(gt, sol)
