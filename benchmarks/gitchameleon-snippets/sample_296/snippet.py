import librosa
import numpy as np

def compute_samples_like(y: np.ndarray, sr: int, D: np.ndarray, hop_length: int) -> np.ndarray:
    """
    Compute the samples vector of a spectrogram.

    Parameters:
        y: The audio signal.
        sr: The sampling rate of the audio signal in Hertz.
        D: The spectrogram.
    
    Returns:
        The computed samples vector.
    """


    return librosa.samples_like(D)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
D = librosa.stft(y)
hop_length = 512 

sol = compute_samples_like(y, sr, D, hop_length)

if np.isscalar(D):
    frames = np.arange(D) # type: ignore
else:
    frames = np.arange(D.shape[-1]) # type: ignore
offset = 0
test_sol = (np.asanyarray(frames) * hop_length + offset).astype(int)

assert np.array_equal(test_sol, sol)
