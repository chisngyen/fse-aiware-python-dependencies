import librosa
import numpy as np

# Save the stream in variable stream. Save each stream block with the array stream_blocks
def compute_stream(y, sr, n_fft, hop_length):
    stream_blocks = []



    stream =  librosa.stream(filename, block_length=16,
                        frame_length=n_fft,
                        hop_length=hop_length,
                        mono=True,
                        fill_value=0)

    for c, y_block in enumerate(stream):
        stream_blocks.append(librosa.stft(y_block, n_fft=n_fft, hop_length=hop_length, center=False))
    return stream, stream_blocks

# --- test ---

filename = librosa.util.example_audio_file()
y, sr = librosa.load(filename)

n_fft = 4096
hop_length = n_fft // 2
stream, stream_blocks = compute_stream(y, sr, n_fft, hop_length)
sol_stream =  librosa.stream(filename, block_length=16,
                        frame_length=n_fft,
                        hop_length=hop_length,
                        mono=True,
                        fill_value=0)
for c, y_block in enumerate(sol_stream):
    assertion_value = np.array_equal(librosa.stft(y_block, n_fft=n_fft, hop_length=hop_length, center=False), stream_blocks[c])
    assert  assertion_value
