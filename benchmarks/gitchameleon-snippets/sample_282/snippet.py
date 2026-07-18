import librosa
import numpy as np
from typing import Tuple

def compute_extraction(y: np.ndarray, sr: int) -> Tuple[np.ndarray, bool]:


    M_from_y = librosa.feature.melspectrogram(y=y, sr=sr) 
    return M_from_y, M_from_y.dtype == np.float32

# --- test ---

duration = 2.0 
frequency = 440 
sr = 22050 
t = np.linspace(0, duration, int(sr * duration), endpoint=False)

y = 0.5 * np.sin(2 * np.pi * frequency * t)
y = y.astype(np.float32)

sol=librosa.feature.melspectrogram(y=y, sr=sr) 
M_from_y, float32_bool = compute_extraction(y, sr)
assert np.array_equal(sol, M_from_y)
assert float32_bool
