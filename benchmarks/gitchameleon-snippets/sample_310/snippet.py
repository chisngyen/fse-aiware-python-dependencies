import librosa
import numpy as np
import scipy
from typing import Union, Optional

DTypeLike = Union[np.dtype, type]


def compute_vqt(y: np.ndarray, sr: int) -> np.ndarray:


    return librosa.vqt(y, sr=sr)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)

sol = compute_vqt(y, sr)
test_sol = librosa.vqt(y, sr=sr)
assert np.allclose(test_sol, sol)
