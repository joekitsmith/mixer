import pathlib
from typing import Optional, Tuple

import essentia.standard as es
import matplotlib.pyplot as plt
import numpy as np
import pyrubberband as pyrb
import soundfile as sf
from madmom.features.downbeats import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor

SAMPLE_RATE = 44100  # Sample rate fixed for essentia


def main():
    prev_audio_path = pathlib.Path("data/track5.mp3")
    next_audio_path = pathlib.Path("data/track6.mp3")

    prev_audio = load_audio(str(prev_audio_path.resolve()))
    next_audio = load_audio(str(next_audio_path.resolve()))

    prev_audio = prev_audio[int(30 * SAMPLE_RATE) :]
    next_audio = next_audio[int(30 * SAMPLE_RATE) :]

    prev_bpm, prev_downbeats = extract_bpm_and_downbeats(prev_audio)
    next_bpm, next_downbeats = extract_bpm_and_downbeats(next_audio)

    next_audio_stretch = stretch_audio(next_audio, prev_bpm, next_bpm)
    next_bpm_stretch, next_downbeats_stretch = extract_bpm_and_downbeats(
        next_audio_stretch
    )

    prev_audio_aligned, next_audio_aligned = overlap_tracks(
        prev_audio,
        prev_downbeats,
        next_audio_stretch,
        next_downbeats_stretch,
        prev_overlap_cue=48,
        next_overlap_cue=30,
        overlap_length=8,
    )

    combined_audio = combine_audio_tracks(prev_audio_aligned, next_audio_aligned)

    sf.write("combined.mp3", combined_audio, int(SAMPLE_RATE))


def load_audio(path: str) -> np.ndarray:
    """
    Load an audio file from a given path.

    Parameters
    ----------
    path : str
        local path to audio file

    Returns
    -------
    np.ndarray
        mono representation of audio file
    """
    loader = es.MonoLoader(filename=path, sampleRate=SAMPLE_RATE)
    return loader()


def extract_bpm_and_downbeats(audio: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Determine BPM and downbeat locations for audio

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file

    Returns
    -------
    bpm : float
        tempo of the audio file
    downbeats : np.ndarray
        time points of downbeats in audio file
    """
    # Extract BPM and beats
    rhythm_extractor = es.RhythmExtractor2013(method="degara")
    bpm, _, _, _, _ = rhythm_extractor(audio)

    downbeats = get_downbeats(audio)

    return bpm, downbeats


def stretch_audio(
    audio: np.ndarray, original_bpm: float, target_bpm: float
) -> np.ndarray:
    """
    Time stretch audio file to increase BPM to target

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file
    original_bpm : float
        BPM of audio before time stretching
    target_bpm : float
        intended BPM of audio

    Returns
    -------
    np.ndarray
        time-stretched audio
    """
    stretch_factor = original_bpm / target_bpm
    return pyrb.time_stretch(audio, SAMPLE_RATE, stretch_factor)


def align_on_beat(
    prev_audio: np.ndarray,
    prev_downbeats: np.ndarray,
    next_audio: np.ndarray,
    next_downbeats: np.ndarray,
    prev_downbeat_offset: int = 0,
    next_downbeat_offset: int = 0,
    downbeat_adjust_factor: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align two audio tracks with the same tempo based on their downbeat information.
    Each track can be started from its own defined downbeat.
    The next audio track can be configured to start a fraction of a downbeat later than a whole beat.

    Parameters
    ----------
    prev_audio : np.ndarray
        mono representation of previous audio file
    prev_downbeats : np.ndarray
        time points of downbeats in previous audio file
    next_audio : np.ndarray
        mono representation of next audio file
    next_downbeats : np.ndarray
        time points of downbeats in next audio file
    prev_downbeat_offset : int
        index of downbeat to start previous audio file from
    next_beat_offset : int
        index of downbeat to start next audio file from
    downbeat_adjust_factor : int
        fraction of bar that next audio should be adjusted by
        e.g. if set to 2, next audio will start 1/2 a bar later

    Returns
    -------
    prev_audio_aligned : np.ndarray
        mono representation of previous audio file aligned to next audio
    next_audio_aligned : np.ndarray
        mono representation of next audio file aligned to previous audio
    """
    # Find the start sample of first beat for each audio
    prev_start_sample = int(prev_downbeats[prev_downbeat_offset] * SAMPLE_RATE)
    next_start_sample = int(next_downbeats[next_downbeat_offset] * SAMPLE_RATE)

    # Use numpy slicing to align both audios to start on their respective first downbeats
    prev_audio_aligned = prev_audio[prev_start_sample:]
    next_audio_aligned = next_audio[next_start_sample:]

    if isinstance(downbeat_adjust_factor, int):
        next_avg_downbeat_duration = np.mean(np.diff(next_downbeats))
        half_downbeat_duration = next_avg_downbeat_duration / downbeat_adjust_factor
        next_audio_aligned = next_audio_aligned[
            int(half_downbeat_duration * SAMPLE_RATE) :
        ]

    return prev_audio_aligned, next_audio_aligned


def overlap_tracks(
    prev_audio: np.ndarray,
    prev_downbeats: np.ndarray,
    next_audio: np.ndarray,
    next_downbeats: np.ndarray,
    prev_overlap_cue: int,
    next_overlap_cue: int,
    overlap_length: int = 4,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Overlap two audio files at defined downbeat cue points for a defined overlap length.
    Previous audio file is faded out during overlap region and next audio file is faded out.

    Parameters
    ----------
    prev_audio : np.ndarray
        mono representation of previous audio file
    prev_downbeats : np.ndarray
        time points of downbeats in previous audio file
    next_audio : np.ndarray
        mono representation of next audio file
    next_downbeats : np.ndarray
        time points of downbeats in next audio file
    prev_overlap_cue : int
        index of downbeat to use as starting cue point for previous audio file
    next_overlap_cue : int
        index of downbeat to use as starting cue point for next audio file
    overlap_length : int
        length of overlap region in bars

    Returns
    -------
    prev_audio_faded : np.ndarray
        previous audio file trimmed and fading applied
    next_audio_faded : np.ndarray
        next audio file trimmed and fading applied
    """
    # Find the start sample of first beat for each audio
    prev_start_sample = int(
        prev_downbeats[prev_overlap_cue - (2 * overlap_length)] * SAMPLE_RATE
    )
    prev_end_sample = int(
        prev_downbeats[prev_overlap_cue + overlap_length] * SAMPLE_RATE
    )
    next_start_sample = int(
        next_downbeats[next_overlap_cue - overlap_length] * SAMPLE_RATE
    )
    next_end_sample = int(
        next_downbeats[next_overlap_cue + (3 * overlap_length)] * SAMPLE_RATE
    )

    prev_audio_trimmed = prev_audio[prev_start_sample : prev_end_sample + 1]
    next_audio_trimmed = next_audio[next_start_sample : next_end_sample + 1]

    # assume same SR here
    fade_duration = next_end_sample - prev_start_sample
    prev_audio_faded = fade_track(prev_audio_trimmed, fade_duration, mode="out")
    next_audio_faded = fade_track(next_audio_trimmed, fade_duration, mode="in")

    length_diff = len(next_audio_faded) - len(prev_audio_faded)

    prev_audio_faded = np.pad(prev_audio_faded, (0, length_diff))
    next_audio_faded = np.pad(next_audio_faded, (length_diff, 0))

    return prev_audio_faded, next_audio_faded


def combine_audio_tracks(
    prev_audio: np.ndarray, next_audio: np.ndarray, normalise: bool = True
) -> np.ndarray:
    """
    Combine two audio tracks into one audio track.

    Parameters
    ----------
    prev_audio : np.ndarray
        mono representation of previous audio file
    next_audio : np.ndarray
        mono representation of next audio file
    normalise : bool
        If True, amplitude of final audio track will be normalised between -1.0 and 1.0

    Returns
    -------
    combined_audio : np.ndarray
    """
    # Pad the shorter audio with zeros at end so that they have the same length
    length_diff = len(prev_audio) - len(next_audio)

    if length_diff > 0:
        next_audio = np.pad(next_audio, (0, length_diff))
    elif length_diff < 0:
        prev_audio = np.pad(prev_audio, (0, -length_diff))

    combined_audio = prev_audio + next_audio

    if normalise:
        if np.max(np.abs(combined_audio)) > 1.0:
            combined_audio /= np.max(np.abs(combined_audio))

    return combined_audio


def add_beat_markers_to_audio(audio: np.ndarray, beats: np.ndarray) -> np.ndarray:
    """
    Add beat markers as bleeps to audio file.

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file
    beats : np.ndarray
        time points of beats in audio

    Returns
    -------
    np.ndarray
        audio with beat markers added as bleep sounds
    """
    marker = es.AudioOnsetsMarker(onsets=beats, type="beep")
    return marker(audio)


def plot_beats(audio: np.ndarray, beats: np.ndarray, audio_name: str) -> None:
    """
    Plot audio waveform with lines representing positions of beat markers.

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file
    beats : np.ndarray
        time points of beats in audio
    """
    # Plot waveform
    plt.figure(figsize=(10, 4))
    plt.plot(
        np.linspace(0, len(audio) / SAMPLE_RATE, len(audio)),
        audio,
        label="Waveform",
        alpha=0.7,
    )

    # Plot beat markers
    for beat in beats:
        plt.axvline(beat, color="red", alpha=0.8, linestyle="--", lw=1)

    plt.title("Waveform with Beat Markers")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.tight_layout()
    plt.show()


def get_downbeats(audio: np.ndarray) -> np.ndarray:
    """
    Use madmom downbeat tracking to estimate downbeat time points for audio file.

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file

    Returns
    -------
    downbeats : np.ndarray
        time points of downbeats in audio file
    """
    proc = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)

    act = RNNDownBeatProcessor()(audio)

    proc_res = proc(act)

    downbeats = proc_res[proc_res[:, 1] == 1, 0]
    # beat_curve = proc_res[:, 0]
    return downbeats


def fade_track(audio: np.ndarray, fade_duration: int, mode: str = "in") -> np.ndarray:
    """
    Fade an audio track in or out with a linear envelope.

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file
    fade_duration : int
        number of samples over which fade will be applied
    mode : str
        If 'in', amplitude of audio file will increase from 0 to 1 over fade duration
        If 'out' amplitude of audio file decrease from 1 to 0 over fade duration
    """
    if mode not in ["in", "out"]:
        raise ValueError("Mode must be 'in' or 'out'.")

    if mode == "in":
        start_sample = 0
        end_sample = fade_duration
        fade_envelope = np.linspace(0, 1, fade_duration)
    else:
        start_sample = len(audio) - fade_duration
        end_sample = len(audio)
        fade_envelope = np.linspace(1, 0, fade_duration)

    audio[start_sample:end_sample] *= fade_envelope

    return audio


if __name__ == "__main__":
    main()
