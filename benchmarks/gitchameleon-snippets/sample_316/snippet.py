import librosa
import numpy as np
import scipy

def compute_mfcc_to_mel(mfcc: np.ndarray, n_mels: int=128, dct_type: int=2, norm: str='ortho', ref: float=1.0) -> np.ndarray:
    """
    Invert Mel-frequency cepstral coefficients to approximate a Mel power spectrogram.

    Parameters:
        mfcc (np.ndarray): Mel-frequency cepstral coefficients.
        n_mels (int): Number of Mel bands to generate.
        dct_type (int): Type of DCT to use.
        norm (str): Normalization to use.
        ref: Reference power for (inverse) decibel calculation

    Returns:
        An approximate Mel power spectrum recovered from mfcc.        
    """    
    np.random.seed(seed=0)


    return librosa.feature.inverse.mfcc_to_mel(mfcc)

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
mfcc = librosa.feature.mfcc(y=y, sr=sr)

sol = compute_mfcc_to_mel(mfcc)

np.random.seed(seed=0)
test_sol = librosa.feature.inverse.mfcc_to_mel(mfcc)
assert np.allclose(test_sol, sol)
