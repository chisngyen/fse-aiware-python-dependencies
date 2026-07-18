import librosa
import numpy as np

def compute_lpc_coef(y: np.ndarray, sr: int, order: int) -> np.ndarray:
    """
    Compute the Linear Prediction Coefficients of an audio signal.

    Parameters:
        y: The audio signal.
        sr: The sampling rate of the audio signal in Hertz.
        order: Order of the linear filter.

    Returns:
        LP prediction error coefficients, i.e. filter denominator polynomial.
    """


    return librosa.lpc(y, order)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
order=2

sol = compute_lpc_coef(y, sr, order)
test_sol = librosa.lpc(y, order)
assert np.array_equal(test_sol, sol)
