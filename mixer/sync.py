from typing import Optional, Tuple

import essentia.standard as es
import matplotlib.pyplot as plt
import numpy as np
import pyrubberband as pyrb
import soundfile as sf

SAMPLE_RATE = 44100  # Sample rate fixed for essentia


def main():
    prev_audio = load_audio("data/track1.mp3")
    next_audio = load_audio("data/track2.mp3")

    prev_bpm, prev_beats = extract_bpm_and_beats(prev_audio)
    next_bpm, next_beats = extract_bpm_and_beats(next_audio)

    next_audio_stretch = stretch_audio(next_audio, prev_bpm, next_bpm)
    next_beats_stretch = next_beats / (prev_bpm / next_bpm)

    prev_audio_aligned, next_audio_aligned = align_on_beat(
        prev_audio,
        prev_beats,
        next_audio_stretch,
        next_beats_stretch,
        prev_beat_offset=200,
        next_beat_offset=200,
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


def extract_bpm_and_beats(audio: np.ndarray) -> Tuple[float, np.ndarray]:
    """
    Determine BPM and beat locations for audio

    Parameters
    ----------
    audio : np.ndarray
        mono representation of audio file

    Returns
    -------
    bpm : float
        tempo of the audio file
    beats : np.ndarray
        time points of beats in audio file
    """
    # Extract BPM and beats
    rhythm_extractor = es.RhythmExtractor2013(method="degara")
    bpm, beats, _, _, _ = rhythm_extractor(audio)

    return bpm, beats


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
    prev_beats: np.ndarray,
    next_audio: np.ndarray,
    next_beats: np.ndarray,
    prev_beat_offset: int = 0,
    next_beat_offset: int = 0,
    beat_adjust_factor: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align two audio tracks with the same tempo based on their beat information.
    Each track can be started from its own defined beat.
    The next audio track can be configured to start a fraction of a beat later than a whole beat.

    Parameters
    ----------
    prev_audio : np.ndarray
        mono representation of previous audio file
    prev_beats : np.ndarray
        time points of beats in previous audio file
    next_audio : np.ndarray
        mono representation of next audio file
    next_beats : np.ndarray
        time points of beats in next audio file
    prev_beat_offset : int
        index of beat to start previous audio file from
    next_beat_offset : int
        index of beat to start next audio file from
    beat_adjust_factor : int
        fraction of beat that next audio should be adjusted by
        e.g. if set to 2, next audio will start 1/2 a beat later

    Returns
    -------
    prev_audio_aligned : np.ndarray
        mono representation of previous audio file aligned to next audio
    next_audio_aligned : np.ndarray
        mono representation of next audio file aligned to previous audio
    """
    # Find the start sample of first beat for each audio
    start_sample1 = int(prev_beats[prev_beat_offset] * SAMPLE_RATE)
    start_sample2 = int(next_beats[next_beat_offset] * SAMPLE_RATE)

    # Use numpy slicing to align both audios to start on their respective first beats
    prev_audio_aligned = prev_audio[start_sample1:]
    next_audio_aligned = next_audio[start_sample2:]

    if isinstance(beat_adjust_factor, int):
        average_beat2_duration = np.mean(np.diff(next_beats))
        half_beat_duration = average_beat2_duration / beat_adjust_factor
        next_audio_aligned = next_audio_aligned[int(half_beat_duration * SAMPLE_RATE) :]

    return prev_audio_aligned, next_audio_aligned


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


def plot_beats(audio: np.ndarray, beats: np.ndarray) -> None:
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


if __name__ == "__main__":
    main()
