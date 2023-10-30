import os
from typing import cast

import essentia.standard as es
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from mixer.logger import logger
from mixer.mix import Mix
from mixer.track import SAMPLE_RATE, Track, TrackGroup


def main():
    track_groups = evaluate_tracklist()
    track_group = max(track_groups, key=lambda x: len(x.tracks))
    combined_audio = mix_track_group(track_group)
    sf.write("combined.mp3", combined_audio, int(SAMPLE_RATE))


def mix_track_group(track_group: TrackGroup) -> np.ndarray:
    """
    Mix a group of tracks to their average tempo.
    If no average tempo for track group, mix to default tempo value.

    Parameters
    ----------
    track_group : TrackGroup
        a group of tracks with similar tempos

    Returns
    -------
    np.ndarray
        a mono audio signal with input tracks mixed at their average tempo
    """
    bpm = track_group.bpm
    if bpm is None:
        bpm = 130.0

    mix = Mix(bpm)

    for i, track in enumerate(track_group.tracks):
        track.crop(0, 90)

        if i == 0:
            mix.add_track(track, 30, 60)
            continue

        mix.add_track(track, 30, 60)

    logger.info(f"{len(track_group.tracks)} tracks successfully mixed")

    return mix.audio


def evaluate_tracklist(tracklist_dir: str = "./data") -> list[TrackGroup]:
    """
    Identify tracks in an input directory and combine them into groups.

    Parameters
    ----------
    tracklist_dir : str
        directory containing input tracks

    Returns
    -------
    track_groups : list[TrackGroups]
        all tracks in directory bundled into groups with similar tempos
    """
    tracklist: list[Track] = []
    for file in os.listdir(tracklist_dir):
        if file.endswith(".mp3"):
            track = Track(f"{tracklist_dir}/{file}")
            track.load()
            track.calculate_bpm()
            tracklist.append(track)

    logger.info(f"Loaded {len(tracklist)} tracks from {tracklist_dir}")

    track_groups = get_track_groups(tracklist)

    return track_groups


def get_track_groups(tracklist: list[Track], tempo_diff: int = 10) -> list[TrackGroup]:
    """
    Bundle tracks into groups based on how similar their tempos are.

    Parameters
    ----------
    tracklist : list[Track]
        input tracks
    tempo_diff : int
        maximum absolute difference in tempo between tracks in a group

    Returns
    -------
    groups : list[TrackGroup]
        track groups for input tracks
    """
    tracklist_bpm_sorted = sorted(tracklist, key=lambda x: cast(float, x.bpm))

    groups: list[TrackGroup] = []
    for track in tracklist_bpm_sorted:
        if track.bpm is not None:
            if not groups:
                group = TrackGroup()
                group.add_track(track)
                groups.append(group)
            elif groups[-1].tracks[0].bpm is not None:
                if track.bpm - groups[-1].tracks[0].bpm <= tempo_diff:
                    groups[-1].tracks.append(track)
                else:
                    group = TrackGroup()
                    group.add_track(track)
                    groups.append(group)

    for group in groups:
        group.calculate_bpm()

    logger.info(f"Organised tracks into {len(groups)} groups:")
    for i, group in enumerate(groups):
        if group.bpm is None:
            logger.info(
                f"Group {i+1} contains {len(group.tracks)} tracks but no average tempo could be deduced"
            )
        else:
            logger.info(
                f"Group {i+1} contains {len(group.tracks)} tracks with an average tempo of {round(group.bpm, 2)}"
            )

    return groups


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


if __name__ == "__main__":
    main()
