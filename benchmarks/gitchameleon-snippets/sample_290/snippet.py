import librosa
import numpy as np

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


    return librosa.feature.fourier_tempogram(onset_envelope=oenv, sr=sr, hop_length=hop_length)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
hop_length = 512
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

sol = compute_fourier_tempogram(oenv, sr, hop_length)
test_sol = librosa.feature.fourier_tempogram(onset_envelope=oenv, sr=sr, hop_length=hop_length)
assert np.array_equal(test_sol, sol)
