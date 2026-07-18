import librosa
import numpy as np

def compute_tone(frequency: int, sr: int, length: int) -> np.ndarray:
    """
    Constructs a pure tone (cosine) signal at a given frequency.

    Parameters:
        frequency: The frequency of the tone in Hz.
        sr: The sampling rate of the signal in Hz.
        length: The length of the signal in samples.

    Returns:
        np.ndarray: The pure tone signal.
    """


    return librosa.tone(frequency, sr=sr, length=length)

# --- test ---

frequency = 440
sr = 22050
length = sr

sol = compute_tone(frequency, sr, length)
test_sol = librosa.tone(frequency, sr=sr, length=length)
assert np.array_equal(test_sol, sol)
