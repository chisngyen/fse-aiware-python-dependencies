import librosa
import numpy as np
from librosa import istft, stft
from typing import Union, Optional

DTypeLike = Union[np.dtype, type]

def compute_griffinlim(y: np.ndarray, sr: int, S: np.ndarray, random_state: int, n_iter: int, hop_length: Optional[int], win_length: Optional[int], window: str, center: bool, dtype: DTypeLike, length: Optional[int], pad_mode: str, n_fft: int) -> np.ndarray:
    """
    Compute waveform from a linear scale magnitude spectrogram using the Griffin-Lim transformation.

    Parameters:
        y: Audio timeseries.
        sr: Sampling rate.
        S: short-time Fourier transform magnitude matrix.
        random_state: Random state for the random number generator.
        n_iter: Number of iterations.
        hop_length: Hop length.
        win_length: Window length.
        window: Window function.
        center: If True, the signal y is padded so that frame t is centered at y[t * hop_length]. If False, then frame t begins at y[t * hop_length].
        dtype: Data type of the output.
        length: Length of the output signal.
        pad_mode: Padding mode.
        n_fft: FFT size.

    Returns:
        The Griffin-Lim waveform.        
    """    
    rng = np.random.RandomState(seed=random_state)


    return librosa.griffinlim(S, n_iter, hop_length, win_length, window, center, dtype, length, pad_mode, momentum, random_state)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
momentum = 0.99
S = np.abs(librosa.stft(y))
random_state = 0
rng = np.random.RandomState(seed=random_state)
n_iter=32
hop_length=None
win_length=None
window='hann'
center=True
dtype=np.float32
length=None
pad_mode='reflect'
n_fft = 2 * (S.shape[0] - 1)

sol = compute_griffinlim(y, sr, S, random_state, n_iter, hop_length, win_length, window, center, dtype, length, pad_mode, n_fft)

rng = np.random.RandomState(seed=random_state)
test_sol = librosa.griffinlim(S, n_iter, hop_length, win_length, window, center, dtype, length, pad_mode, momentum, random_state)
assert np.allclose(test_sol, sol)
