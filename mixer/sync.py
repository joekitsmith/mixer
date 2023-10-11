from logger import logger
import pathlib
import numpy as np
import torch
import torchaudio
from madmom.features.downbeats import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor

def main():
    prev_audio_path = pathlib.Path("./data/track1.mp3")
    next_audio_path = pathlib.Path("./data/track2.mp3")

    prev_audio = load_audio(prev_audio_path)
    next_audio = load_audio(next_audio_path)

    prev_bpm, prev_downbeat = estimate_beat(prev_audio)
    logger.info(f"BPM for {prev_audio_path.stem} is {round(prev_bpm, 2)}")

    next_bpm, next_downbeat = estimate_beat(next_audio)
    logger.info(f"BPM for {next_audio_path.stem} is {round(next_bpm, 2)}")


def load_audio(audio_path: pathlib.Path) -> torch.Tensor:
    """
    Load audio file into mono torch Tensor.

    Parameters
    ----------
    audio_path : pathlib.Path
        path to audio file

    Returns
    -------
    audio : torch.Tensor
        tensor of shape (1, y)
    """
    if audio_path.suffix == "mp3":
        torchaudio.set_audio_backend('soundfile')

    audio = torchaudio.load(audio_path)[0]
    audio = to_mono(audio)

    return audio


def estimate_beat(audio: torch.Tensor) -> tuple[float, np.ndarray]:
    """
    Estimate bpm and downbeat times for a given mono audio tensor.

    Parameters
    ----------
    audio : torch.Tensor
        tensor of shape (1, y)

    Returns
    -------
    bpm : float
        tempo of audio in beats per minute
    downbeats : np.ndarray
        positions of downbeats for every bar
    """
    if isinstance(audio, torch.Tensor): 
        audio = squeeze_dim(audio).numpy()

    proc = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)

    logger.info("Getting joint beat and downbeat activation function")
    act = RNNDownBeatProcessor()(audio)
    
    logger.info("Obtaining beat positions using beat activation function")
    proc_res = proc(act)
    
    downbeats = proc_res[proc_res[:,1] == 1, 0]
    beat_curve = proc_res[:, 0]
    bpm = estimate_bpm(beat_curve)

    return bpm, downbeats

def estimate_bpm(beat_curve: np.ndarray) -> float:
    """
    Estimate tempo from beat times by sampling the middle third of an audio track.

    Parameters
    ----------
    beat_curve : np.ndarray
        times of every beat in every bar

    Returns
    -------
    bpm : float
        tempo of audio in beats per minute
    """
    total_beat = len(beat_curve)

    sample_start = int(total_beat / 3)
    sample_end = int(total_beat * 2 / 3)
    sample_beat_num = sample_end - sample_start
    sample_time = beat_curve[sample_end] - beat_curve[sample_start]

    bpm = float(sample_beat_num / (sample_time / 60))
    return bpm

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