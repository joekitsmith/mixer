import pathlib

import librosa
import numpy as np
import torch
import torchaudio
from logger import logger


def main():
    prev_audio_path = pathlib.Path("./data/track1.mp3")
    next_audio_path = pathlib.Path("./data/track2.mp3")

    prev_audio = load_audio(prev_audio_path)
    next_audio = load_audio(next_audio_path)

    prev_bpm, prev_downbeat = estimate_beat(prev_audio)
    logger.info(f"BPM for {prev_audio_path.stem} is {round(prev_bpm, 2)}")

    next_bpm, next_downbeat = estimate_beat(next_audio)
    logger.info(f"BPM for {next_audio_path.stem} is {round(next_bpm, 2)}")


def load_audio(audio_path: pathlib.Path) -> np.ndarray:
    """
    Load audio file into mono torch Tensor.

    Parameters
    ----------
    audio_path : pathlib.Path
        path to audio file

    Returns
    -------
    audio : np.ndarray
        array of shape ?
    """
    if audio_path.suffix == "mp3":
        torchaudio.set_audio_backend("soundfile")

    audio = torchaudio.load(audio_path)[0]
    audio = to_mono(audio)
    audio = squeeze_dim(audio).numpy()

    return audio


def estimate_beat(audio: np.ndarray) -> tuple[float, np.ndarray]:
    """
    Estimate bpm and downbeat times for a given mono audio tensor.

    Parameters
    ----------
    audio : np.ndarray
        array of shape ?

    Returns
    -------
    bpm : float
        tempo of audio in beats per minute
    downbeats : np.ndarray
        positions of downbeats for every bar
    """
    return librosa.beat.beat_track(y=audio)


def to_mono(audio: torch.Tensor, dim: int = -2) -> torch.Tensor:
    """
    If audio is stereo, convert to mono?

    Parameters
    ----------
    audio : torch.Tensor
        tensor of shape (x, y)
    dim : int
        ?

    Returns
    -------
    audio : torch.Tensor
        tensor of shape (1, y)
    """
    if len(audio.size()) > 1:
        return torch.mean(audio, dim=dim, keepdim=True)
    else:
        return audio


def squeeze_dim(audio: torch.Tensor) -> torch.Tensor:
    """
    Flatten multi-dimensional audio tensor to single dimension.

    Parameters
    ----------
    audio : torch.Tensor
        tensor of shape (1, y)

    Returns
    -------
    audio : torch.Tensor
        tensor of shape (y,)
    """
    dims = [i for i in range(len(audio.size())) if audio.size(i) == 1]
    for dim in dims:
        audio = audio.squeeze(dim)
    return audio


if __name__ == "__main__":
    main()
