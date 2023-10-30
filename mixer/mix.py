import numpy as np

from mixer.logger import logger
from mixer.track import SAMPLE_RATE, Track


class Mix:
    def __init__(self, bpm: float):
        """
        Parameters
        ----------
        bpm : float
            tempo of mix that all tracks will by stretched to
        """
        self._audio = np.array([])
        self._bpm = bpm
        self._track_count = 0

        self.prev_downbeats = np.array([])
        self.prev_start_sample = None
        self.prev_end_sample = None
        self.prev_overlap_start_sample = None

    @property
    def audio(self) -> np.ndarray:
        return self._audio

    @property
    def bpm(self) -> float:
        return self._bpm

    @property
    def track_count(self) -> int:
        return self._track_count

    def add_track(
        self, track: Track, cue_in: int, cue_out: int, overlap: int = 16
    ) -> None:
        """
        Add a new track to the existing mix audio.
        Tracks can be cued in and out at specific downbeats.
        An overlap of the previous track and current track can be defined so that they
        fade in and out respectively over that period.

        Parameters
        ----------
        track : Track
            track to be added to mix
        cue_in : int
            track's downbeat where the track's audio will start
        cue_out : int
            track's downbeat where the track's audio will end
        overlap : int
            number of downbeats for previous and current tracks where they will overlap
        """
        track.bpm = self._bpm
        if track.downbeats.size == 0:
            track.calculate_downbeats()

        curr_downbeats = track.downbeats
        curr_downbeats = curr_downbeats[cue_in:cue_out]

        curr_cue_in_sample = int(curr_downbeats[0] * SAMPLE_RATE)
        curr_cue_out_sample = int(curr_downbeats[-1] * SAMPLE_RATE)
        curr_audio = track.audio[curr_cue_in_sample:curr_cue_out_sample]
        curr_downbeats -= curr_downbeats[0]

        if self._track_count == 0:
            self._audio = curr_audio
            self._track_count += 1
            self.prev_downbeats = curr_downbeats
            return

        curr_fade_duration = int(curr_downbeats[overlap] * SAMPLE_RATE)
        prev_fade_duration = int(
            (self.prev_downbeats[-1] - self.prev_downbeats[-1 * overlap]) * SAMPLE_RATE
        )

        prev_track_faded = fade_track(self._audio, prev_fade_duration, mode="out")
        curr_track_faded = fade_track(curr_audio, curr_fade_duration, mode="in")

        curr_track_faded = np.pad(
            curr_track_faded, (len(self._audio) - prev_fade_duration, 0)
        )

        self._audio = combine_tracks(prev_track_faded, curr_track_faded)

        self._track_count += 1
        self.prev_downbeats = curr_downbeats

        logger.info(f"Added {track} to mix")


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


def combine_tracks(
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
