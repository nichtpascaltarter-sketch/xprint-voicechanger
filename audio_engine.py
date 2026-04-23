"""
X-Print Voice Changer - Audio Engine
=====================================
Echtzeit-Audio-Pipeline:
    Mikrofon -> sounddevice-Callback -> pedalboard-Chain -> VB-CABLE / Output

- Thread-safe Live-Switching zwischen Modi (kein Dropout)
- Level-Meter (Input/Output) werden im Callback aktualisiert
- Konfigurierbare Blocksize fuer Latenz-Tuning
"""
from __future__ import annotations

import threading
import numpy as np
import sounddevice as sd
from pedalboard import (
    Pedalboard,
    PitchShift,
    HighpassFilter,
    LowShelfFilter,
    HighShelfFilter,
    Chorus,
    Compressor,
    Gain,
    Limiter,
)

# --- Konstanten -------------------------------------------------------------
SAMPLE_RATE = 48_000          # Discord- und VB-CABLE-kompatibel
DEFAULT_BLOCKSIZE = 256       # ~5.3 ms @ 48kHz

MODE_BYPASS = "bypass"
MODE_ADULT = "adult"          # ERWACHSEN
MODE_BABY = "baby"            # BABY


class AudioEngine:
    """Kapselt sounddevice-Stream + pedalboard-Effektketten."""

    def __init__(self) -> None:
        self.samplerate: int = SAMPLE_RATE
        self.blocksize: int = DEFAULT_BLOCKSIZE
        self.input_device: int | None = None
        self.output_device: int | None = None

        self._mode: str = MODE_BYPASS
        self._lock = threading.Lock()
        self._running = False
        self._stream: sd.Stream | None = None

        # Effektketten vorbauen (nicht im Callback!)
        self._board_adult = self._build_adult_board()
        self._board_baby = self._build_baby_board()

        # Telemetrie (atomare Float-Reads aus dem UI-Thread)
        self.input_level: float = 0.0
        self.output_level: float = 0.0
        self.actual_latency_ms: float = 0.0
        self.last_error: str | None = None

    # ------------------------------------------------------------------ Boards
    @staticmethod
    def _build_adult_board() -> Pedalboard:
        """ERWACHSEN: Pitch -12 Halbtoene + leichte Formant-Absenkung via LowShelf.
        Kompressor + Limiter fuer gleichmaessigen Pegel.
        """
        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=70),
            PitchShift(semitones=-12),
            LowShelfFilter(cutoff_frequency_hz=220, gain_db=3.5),
            HighShelfFilter(cutoff_frequency_hz=4500, gain_db=-2.0),
            Compressor(threshold_db=-20, ratio=3.0, attack_ms=5, release_ms=80),
            Gain(gain_db=2.5),
            Limiter(threshold_db=-1.0, release_ms=60),
        ])

    @staticmethod
    def _build_baby_board() -> Pedalboard:
        """BABY: Pitch +7 Halbtoene, Formant-Anhebung via HighShelf, dezentes Doubling.
        Kein 'Chipmunk'-Effekt dank moderater Shift und Kompression.
        """
        return Pedalboard([
            HighpassFilter(cutoff_frequency_hz=120),
            PitchShift(semitones=7),
            HighShelfFilter(cutoff_frequency_hz=3200, gain_db=4.0),
            LowShelfFilter(cutoff_frequency_hz=180, gain_db=-2.5),
            Chorus(rate_hz=0.7, depth=0.12, centre_delay_ms=7.5, feedback=0.0, mix=0.22),
            Compressor(threshold_db=-18, ratio=2.5, attack_ms=3, release_ms=70),
            Gain(gain_db=1.0),
            Limiter(threshold_db=-1.0, release_ms=60),
        ])

    # ------------------------------------------------------------------ Setter
    def set_mode(self, mode: str) -> None:
        if mode not in (MODE_BYPASS, MODE_ADULT, MODE_BABY):
            raise ValueError(f"Unbekannter Modus: {mode}")
        with self._lock:
            self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    def set_blocksize(self, blocksize: int) -> None:
        was_running = self._running
        if was_running:
            self.stop()
        self.blocksize = int(blocksize)
        if was_running:
            self.start()

    def set_devices(self, input_device: int | None, output_device: int | None) -> None:
        was_running = self._running
        if was_running:
            self.stop()
        self.input_device = input_device
        self.output_device = output_device
        if was_running:
            self.start()

    # ------------------------------------------------------------------ Audio-Callback
    def _callback(self, indata: np.ndarray, outdata: np.ndarray,
                  frames: int, time_info, status) -> None:
        # Mono-Input
        mono = indata[:, 0] if indata.ndim > 1 else indata
        self.input_level = float(np.max(np.abs(mono))) if frames else 0.0

        with self._lock:
            mode = self._mode

        if mode == MODE_BYPASS:
            processed = mono.astype(np.float32, copy=True)
        else:
            board = self._board_baby if mode == MODE_BABY else self._board_adult
            # reset=False -> Filter-State bleibt erhalten (kein Knacken zwischen Bloecken)
            processed = board(mono.astype(np.float32), self.samplerate, reset=False)

        # Pedalboard kann wegen interner Buffer leicht abweichende Laengen liefern
        n_out = processed.shape[-1] if processed.ndim else 0
        if n_out != frames:
            if n_out > frames:
                processed = processed[:frames]
            else:
                pad = np.zeros(frames, dtype=np.float32)
                pad[:n_out] = processed
                processed = pad

        self.output_level = float(np.max(np.abs(processed))) if frames else 0.0

        # Output verteilen (mono -> stereo fuer VB-CABLE)
        if outdata.ndim > 1:
            outdata[:, 0] = processed
            if outdata.shape[1] > 1:
                outdata[:, 1] = processed
        else:
            outdata[:] = processed

    # ------------------------------------------------------------------ Lifecycle
    def start(self) -> None:
        if self._running:
            return
        self.last_error = None

        # Output-Channels an Device anpassen (max 2)
        try:
            if self.output_device is not None:
                out_info = sd.query_devices(self.output_device)
                out_ch = min(2, int(out_info.get("max_output_channels", 2)) or 1)
            else:
                out_ch = 2
        except Exception:
            out_ch = 2

        try:
            self._stream = sd.Stream(
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                device=(self.input_device, self.output_device),
                channels=(1, out_ch),
                dtype="float32",
                latency="low",
                callback=self._callback,
            )
            self._stream.start()
            self._running = True

            try:
                lat = self._stream.latency
                # lat = (input_latency, output_latency) in Sekunden
                self.actual_latency_ms = (float(lat[0]) + float(lat[1])) * 1000.0
            except Exception:
                self.actual_latency_ms = 0.0
        except Exception as e:
            self.last_error = str(e)
            self._stream = None
            self._running = False
            raise

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        self._stream = None
        self._running = False

    @property
    def running(self) -> bool:
        return self._running
