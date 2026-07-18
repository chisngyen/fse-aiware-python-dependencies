import librosa
import numpy as np
import soundfile as sf 


# Save the stream in variable stream. Save each stream block with the array stream_blocks
def compute_stream(filename, y, sr, n_fft, hop_length):
    stream_blocks = []


    stream = sf.blocks(filename, blocksize=n_fft + 15 * hop_length, overlap=n_fft - hop_length,  fill_value=0)

    for c, block in enumerate(stream):
        y = librosa.to_mono(block.T)
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, center=False)
        stream_blocks.append(D)

    return stream, stream_blocks

# --- test ---


filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)

n_fft = 4096
hop_length = n_fft // 2

stream, stream_blocks = compute_stream(filename, y, sr, n_fft, hop_length)
sol_stream = sf.blocks(filename, blocksize=n_fft + 15 * hop_length, overlap=n_fft - hop_length, fill_value=0)
sol_blocks = []
for c, block in enumerate(sol_stream):
    y = librosa.to_mono(block.T)
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, center=False)
    sol_blocks.append(D)
for i in range(0, len(stream_blocks)):
    assert np.array_equal(sol_blocks[i], stream_blocks[i])
