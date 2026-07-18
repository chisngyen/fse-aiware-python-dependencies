import librosa
import numpy as np
from librosa.core.spectrum import stft

def compute_fourier_tempogram(oenv: np.ndarray, sr: int, hop_length: int) -> np.ndarray:
    """
    Compute the Fourier tempogram: the short-time Fourier transform of the onset strength envelope.

    Parameters:
       oenv: The onset strength envelope.
       sr: The sampling rate of the audio signal in Hertz.
       hop_length: The number of samples between successive frames.

    Returns:
       The computed Fourier tempogram.
    """


    return stft(oenv, n_fft=384, hop_length=1, center=True, window="hann")

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
hop_length = 512
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

sol = compute_fourier_tempogram(oenv, sr, hop_length)
test_sol = stft(oenv, n_fft=384, hop_length=1, center=True, window="hann")
assert np.array_equal(test_sol, sol)
