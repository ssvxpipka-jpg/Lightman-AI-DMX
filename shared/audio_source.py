"""
Cross-platform audio analyzer (sounddevice + librosa).

Platform detection:
    macOS   → looks for a "BlackHole" loopback device.
    Windows → default OUTPUT device opened with WASAPI loopback.
    Linux   → default monitor source (PulseAudio/PipeWire).

If no suitable loopback device is found, the analyzer runs in a dummy mode
that emits zero BPM / zero energy / zero beats — the app never crashes.
"""

import sys
import threading
import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    SD_OK = True
except Exception as _e:  # pragma: no cover
    sd = None  # type: ignore
    SD_OK = False
    logger.warning("sounddevice unavailable: %s", _e)

try:
    import librosa
    LIBROSA_OK = True
except Exception as _e:  # pragma: no cover
    librosa = None  # type: ignore
    LIBROSA_OK = False
    logger.warning("librosa unavailable: %s", _e)


class AudioAnalyzer:
    SAMPLE_RATE = 22050
    BUFFER_SECONDS = 2.0
    HOP_SECONDS = 0.5

    def __init__(self, device=None, on_bpm=None, on_beat=None, on_energy=None):
        self.device = device
        self.on_bpm = on_bpm
        self.on_beat = on_beat
        self.on_energy = on_energy

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._buffer = np.zeros(
            int(self.SAMPLE_RATE * self.BUFFER_SECONDS), dtype=np.float32
        )
        self._last_beat_time = 0.0
        self._prev_beat_count = 0

    # ------------------------------------------------------------- control
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="AudioAnalyzer", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    # ------------------------------------------------------------- device
    def _detect_loopback_device(self):
        """Return the index of the platform-appropriate loopback device."""
        if not SD_OK:
            return None
        try:
            devices = sd.query_devices()
        except Exception as e:
            logger.warning("Cannot enumerate audio devices: %s", e)
            return None

        if sys.platform == "darwin":
            for i, d in enumerate(devices):
                name = (d.get("name") or "").lower()
                if "blackhole" in name:
                    logger.info("Detected BlackHole at index %d", i)
                    return i
            logger.warning(
                "BlackHole not found. Install it via: brew install blackhole-2ch"
            )
            return None

        if sys.platform == "win32":
            # Default OUTPUT device is where WASAPI loopback taps
            try:
                default_out = sd.default.device[1]
                if default_out is not None and default_out >= 0:
                    logger.info(
                        "Using default output device %d for WASAPI loopback",
                        default_out,
                    )
                    return default_out
            except Exception as e:
                logger.warning("Cannot read default output device: %s", e)
            # Fallback: first WASAPI output
            try:
                hostapis = sd.query_hostapis()
                for api in hostapis:
                    api_name = (api.get("name") or "").lower()
                    if "wasapi" not in api_name:
                        continue
                    for dev_idx in api.get("devices", []):
                        d = sd.query_devices(dev_idx)
                        if d.get("max_output_channels", 0) > 0:
                            logger.info(
                                "Using WASAPI output %d for loopback", dev_idx
                            )
                            return dev_idx
            except Exception as e:
                logger.warning("WASAPI discovery failed: %s", e)
            return None

        if sys.platform.startswith("linux"):
            # Look for a monitor source (PulseAudio / PipeWire)
            for i, d in enumerate(devices):
                name = (d.get("name") or "").lower()
                if ("monitor" in name or ".monitor" in name) and \
                        d.get("max_input_channels", 0) > 0:
                    logger.info("Detected monitor source at index %d", i)
                    return i
            # Fallback: default input
            try:
                default_in = sd.default.device[0]
                if default_in is not None and default_in >= 0:
                    logger.info("Using default input %d", default_in)
                    return default_in
            except Exception:
                pass
            return None

        return None

    def _open_stream(self, device_idx, block_size):
        """Open InputStream with platform-specific extra settings."""
        kwargs = dict(
            samplerate=self.SAMPLE_RATE,
            channels=1,
            blocksize=block_size,
            dtype="float32",
            device=device_idx,
        )
        if sys.platform == "win32":
            try:
                kwargs["extra_settings"] = sd.WasapiSettings(loopback=True)
            except Exception as e:
                logger.warning("WASAPI loopback not supported: %s", e)
        return sd.InputStream(**kwargs)

    # ------------------------------------------------------------- worker
    def _run(self) -> None:
        if not (SD_OK and LIBROSA_OK):
            logger.error(
                "Audio stack incomplete (sounddevice=%s, librosa=%s) — "
                "running dummy mode",
                SD_OK, LIBROSA_OK,
            )
            self._run_dummy()
            return

        if self.device is None:
            self.device = self._detect_loopback_device()

        if self.device is None:
            logger.warning(
                "No loopback device detected for platform '%s'. "
                "Running dummy mode (silent, zero values).",
                sys.platform,
            )
            self._run_dummy()
            return

        block = int(self.SAMPLE_RATE * self.HOP_SECONDS)
        try:
            stream = self._open_stream(self.device, block)
            stream.start()
            logger.info(
                "Audio capture started (device=%s, os=%s)",
                self.device, sys.platform,
            )
            try:
                while not self._stop_event.is_set():
                    data, _ = stream.read(block)
                    if data is None or len(data) == 0:
                        self._stop_event.wait(0.05)
                        continue
                    mono = data[:, 0] if data.ndim > 1 else data
                    with self._lock:
                        self._buffer = np.concatenate(
                            [self._buffer, mono.astype(np.float32)]
                        )[-len(self._buffer):]
                    self._analyze()
                    self._stop_event.wait(0.02)
            finally:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
                logger.info("Audio capture stopped.")
        except Exception as e:
            logger.error(
                "Audio stream failed: %s — falling back to dummy mode", e
            )
            self._run_dummy()

    def _run_dummy(self) -> None:
        """Silent fallback loop: emits zeros without crashing the app."""
        logger.info("Dummy audio thread active (silent)")
        while not self._stop_event.is_set():
            try:
                if self.on_energy:
                    self.on_energy(0.0)
                if self.on_bpm:
                    self.on_bpm(0.0)
                if self.on_beat:
                    self.on_beat(0)
            except Exception as e:
                logger.debug("Dummy callback error: %s", e)
            self._stop_event.wait(0.5)

    # ------------------------------------------------------------- analysis
    def _analyze(self) -> None:
        try:
            with self._lock:
                y = self._buffer.copy()

            if not np.any(y):
                return

            rms = float(np.sqrt(np.mean(y ** 2)))
            if self.on_energy:
                try:
                    self.on_energy(rms)
                except Exception as e:
                    logger.error("on_energy callback failed: %s", e)

            try:
                tempo, beats = librosa.beat.beat_track(
                    y=y, sr=self.SAMPLE_RATE
                )
                bpm_val = float(np.atleast_1d(tempo)[0])
                if self.on_bpm:
                    try:
                        self.on_bpm(bpm_val)
                    except Exception as e:
                        logger.error("on_bpm callback failed: %s", e)

                if len(beats) > 0 and self.on_beat:
                    last_beat = int(beats[-1])
                    t = float(
                        librosa.frames_to_time(last_beat, sr=self.SAMPLE_RATE)
                    )
                    if t > self._last_beat_time + 0.1 and \
                            len(beats) > self._prev_beat_count:
                        self._last_beat_time = t
                        self._prev_beat_count = len(beats)
                        try:
                            self.on_beat(len(beats))
                        except Exception as e:
                            logger.error("on_beat callback failed: %s", e)
            except Exception as e:
                logger.debug("librosa analysis skipped: %s", e)
        except Exception as e:
            logger.error("Analyzer loop error: %s", e)