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


    import scipy
    period = 1.0 / sr
    phi = -np.pi * 0.5

    method = "linear" if linear else "logarithmic"

    return scipy.signal.chirp(np.arange(int(duration * sr)) / sr, fmin, duration, fmax, method=method, phi=phi / np.pi * 180, )

# --- test ---

import scipy

fmin = 110
fmax = 110*64
duration = 1
sr = 22050
linear = True

sol  = compute_chirp(fmin, fmax, duration, sr, linear)
period = 1.0 / sr
phi = -np.pi * 0.5
method = "linear" if linear else "logarithmic"
test_sol = scipy.signal.chirp(
 np.arange(int(duration * sr)) / sr,
 fmin,
 duration,
 fmax,
 method=method,
 phi=phi / np.pi * 180, # scipy.signal.chirp uses degrees for phase offset
)
assert np.array_equal(test_sol, sol)
