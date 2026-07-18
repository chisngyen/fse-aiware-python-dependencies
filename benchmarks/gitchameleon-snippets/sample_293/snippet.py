import librosa
import numpy as np

def compute_times_like(y: np.ndarray, sr: int, hop_length: int, D: np.ndarray) -> np.ndarray:
    """
    Compute the times vector of a spectrogram.

    Parameters:
        y: The audio signal.
        sr: The sampling rate of the audio signal in Hertz.
        hop_length: The number of samples between successive frames.
        D: The spectrogram.

    Returns:
        The computed times vector.
    """


    if np.isscalar(D):
        frames = np.arange(D) # type: ignore
    else:
        frames = np.arange(D.shape[-1]) # type: ignore
    offset = 0
    samples = (np.asanyarray(frames) * hop_length + offset).astype(int)

    return np.asanyarray(samples) / float(sr)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
D = librosa.stft(y)
hop_length = 512 

sol = compute_times_like(y, sr, hop_length, D)
    
if np.isscalar(D):
    frames = np.arange(D) # type: ignore
else:
    frames = np.arange(D.shape[-1]) # type: ignore
offset = 0
samples = (np.asanyarray(frames) * hop_length + offset).astype(int)

test_sol = np.asanyarray(samples) / float(sr)
assert np.array_equal(test_sol, sol)
