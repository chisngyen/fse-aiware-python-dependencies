import torch
def stft(audio_signal: torch.Tensor, n_fft: int) -> torch.Tensor:
    return torch.stft(audio_signal, n_fft=n_fft, return_complex=False)

# --- test ---
audio_signal = torch.rand(1024)
n_fft=128
expected_shape = (65, 33, 2)
assert stft(audio_signal, n_fft).shape == expected_shape
