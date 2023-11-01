import pathlib
from typing import Optional

import essentia.standard as es
import numpy as np
import pyrubberband as pyrb
from madmom.features.downbeats import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor

from mixer.logger import logger

SAMPLE_RATE = 44100  # Sample rate fixed for essentia


class TrackProcessor:
    SAMPLE_RATE = SAMPLE_RATE

    def __init__(self, file_path: str) -> None:
        """
        Parameters
        ----------
        file_path : str
            absolute or relative location of track audio file
        """
        self._file_path = pathlib.Path(file_path)
        self._name = self._file_path.stem

        self._audio = np.array([])
        self._bpm = None
        self._downbeats = np.array([])

    def __str__(self):
        return self._name

    @property
    def audio(self) -> np.ndarray:
        return self._audio

    @property
    def downbeats(self) -> np.ndarray:
        return self._downbeats

    @property
    def bpm(self) -> Optional[float]:
        return self._bpm

    @bpm.setter
    def bpm(self, bpm: float) -> np.ndarray:
        """
        Time stretch audio file to increase BPM to target

        Parameters
        ----------
        bpm : float
            intended BPM of audio

        Returns
        -------
        np.ndarray
            time-stretched audio
        """
        if self._bpm is None:
            self.calculate_bpm()

        assert self._bpm is not None

        stretch_factor = bpm / self._bpm
        self._audio = pyrb.time_stretch(self._audio, SAMPLE_RATE, stretch_factor)
        self.calculate_bpm()

        logger.info(f"Tempo for {self} set to {round(self._bpm, 2)}")

        return self._audio

    def load(self, path: Optional[str] = None) -> np.ndarray:
        """
        Load an audio file from a given path.

        Parameters
        ----------
        path : Optional[str]
            local path to audio file
            if None, file_path attribute value used

        Returns
        -------
        np.ndarray
            mono representation of audio file
        """
        if path is None:
            path = str(self._file_path.resolve())

        loader = es.MonoLoader(filename=path, sampleRate=SAMPLE_RATE)
        self._audio = loader()

        logger.info(f"Loaded audio for {self}")

        return self._audio

    def crop(self, offset: int, length: int) -> None:
        """
        Crop track using number of downbeats.

        Parameters
        ----------
        offset : int
            number of downbeats into original audio to crop from
        length : int
            number of downbeats that new audio will contain
        """
        if self.downbeats.size == 0:
            self.calculate_downbeats()

        start_sample = int(self._downbeats[offset] * SAMPLE_RATE)
        end_sample = int(self._downbeats[offset + length] * SAMPLE_RATE)

        self._audio = self._audio[start_sample : end_sample + 1]

        logger.info(
            f"Cropped {self} audio between downbeats {offset} and {offset + length}"
        )

    def calculate_bpm(self) -> float:
        """
        Determine BPM for audio using essentia

        Returns
        -------
        bpm : float
            tempo of audio file
        """
        rhythm_extractor = es.RhythmExtractor2013(method="degara")
        self._bpm, _, _, _, _ = rhythm_extractor(self._audio)

        assert self._bpm is not None

        logger.info(f"Calculated tempo for {self} at {round(self._bpm, 2)}")

        return self._bpm

    def calculate_downbeats(self) -> None:
        """
        Use madmom downbeat tracking to estimate downbeat time points for audio file.
        """
        proc = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)
        act = RNNDownBeatProcessor()(self._audio)
        proc_res = proc(act)

        self._downbeats = proc_res[proc_res[:, 1] == 1, 0]

        logger.info(f"Calculated downbeats for {self}")


class TrackGroupProcessor:
    def __init__(self) -> None:
        self._tracks: list[TrackProcessor] = []
        self._bpm: Optional[float] = None

    @property
    def bpm(self) -> Optional[float]:
        return self._bpm

    @property
    def tracks(self) -> list[TrackProcessor]:
        return self._tracks

    def add_track(self, track: TrackProcessor) -> None:
        """
        Add a track to the track group.

        Parameters
        ----------
        track : TrackProcessor
            track to be added
        """
        self._tracks.append(track)
        self.calculate_bpm()

    def calculate_bpm(self):
        """
        Calculate average bpm of current tracks in group.
        """
        track_bpms = [track.bpm for track in self._tracks]
        self._bpm = sum(track_bpms) / len(track_bpms)
