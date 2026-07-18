import librosa
import numpy as np

def compute_chirp(fmin: int, fmax: int, duration: int, sr: int, linear: bool) -> np.ndarray:
    """
    Constructs a “chirp” or “sine-sweep” signal. The chirp sweeps from frequency fmin to fmax (in Hz).

    Parameters:
        fmin: The minimum frequency of the chirp in Hz.
        fmax: The maximum frequency of the chirp in Hz.
        duration: The duration of the chirp in seconds.
        sr: The sampling rate of the signal in Hz.

    Returns:
        np.ndarray: The chirp signal.
    """


    return librosa.chirp(fmin=fmin, fmax=fmax, duration=duration, sr=sr)

# --- test ---

fmin = 110
fmax = 110*64
duration = 1
sr = 22050
linear = True

sol  = compute_chirp(fmin, fmax, duration, sr, linear)

test_sol = librosa.chirp(fmin=fmin, fmax=fmax, duration=duration, sr=sr)
assert np.array_equal(test_sol, sol)
