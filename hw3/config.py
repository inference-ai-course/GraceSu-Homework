import torch

# TODO: remove before commit
DEVICE = "cuda:3" if torch.cuda.is_available() else "cpu"

WAV_PARAMS = {
    "setnchannels": 2,
    "setframerate": 44100,
    "setsamplewidth": 2,
}
