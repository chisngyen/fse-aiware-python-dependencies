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


    logmel = scipy.fftpack.idct(mfcc, axis=0, type=dct_type, norm=norm, n=n_mels)
    return librosa.db_to_power(logmel, ref=ref)

# --- test ---
filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)
mfcc = librosa.feature.mfcc(y=y, sr=sr)

sol =  compute_mfcc_to_mel(mfcc)
def mfcc_to_mel(mfcc, n_mels=128, dct_type=2, norm='ortho', ref=1.0):
    logmel = scipy.fftpack.idct(mfcc, axis=0, type=dct_type, norm=norm, n=n_mels)
    return librosa.db_to_power(logmel, ref=ref)

np.random.seed(seed=0)
test_sol = mfcc_to_mel(mfcc)
assert np.allclose(test_sol, sol)
