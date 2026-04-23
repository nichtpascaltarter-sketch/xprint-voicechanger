"""
X-Print Voice Changer - Device Manager
=======================================
Listet Windows-Audio-Geraete und findet VB-CABLE.

VB-CABLE-Logik (wichtig!):
    "CABLE Input"  = virtuelles OUTPUT (wir schreiben hier rein)
    "CABLE Output" = virtuelles INPUT  (Discord liest hier)

Unsere App = Output -> "CABLE Input"
Discord    = Input  <- "CABLE Output"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import sounddevice as sd


VB_CABLE_DOWNLOAD_URL = "https://vb-audio.com/Cable/"
# Suchbegriffe fuer den CABLE-Eingang (= unser Output-Ziel)
_CABLE_OUTPUT_KEYWORDS = (
    "cable input",            # VB-Audio Virtual Cable (kostenlos)
    "vb-audio virtual cable",
)


@dataclass
class AudioDevice:
    id: int
    name: str                 # Roher Geraetename
    display: str              # Name + Host-API fuer eindeutiges Mapping
    channels: int
    samplerate: float
    hostapi: int
    hostapi_name: str


def _hostapi_name(idx: int) -> str:
    try:
        return sd.query_hostapis()[idx]["name"]
    except Exception:
        return "?"


def list_input_devices() -> List[AudioDevice]:
    out: List[AudioDevice] = []
    for i, d in enumerate(sd.query_devices()):
        if int(d.get("max_input_channels", 0)) <= 0:
            continue
        api = _hostapi_name(d["hostapi"])
        out.append(AudioDevice(
            id=i, name=d["name"],
            display=f"{d['name']}  [{api}]",
            channels=int(d["max_input_channels"]),
            samplerate=float(d["default_samplerate"]),
            hostapi=int(d["hostapi"]),
            hostapi_name=api,
        ))
    return out


def list_output_devices() -> List[AudioDevice]:
    out: List[AudioDevice] = []
    for i, d in enumerate(sd.query_devices()):
        if int(d.get("max_output_channels", 0)) <= 0:
            continue
        api = _hostapi_name(d["hostapi"])
        out.append(AudioDevice(
            id=i, name=d["name"],
            display=f"{d['name']}  [{api}]",
            channels=int(d["max_output_channels"]),
            samplerate=float(d["default_samplerate"]),
            hostapi=int(d["hostapi"]),
            hostapi_name=api,
        ))
    return out


def find_vb_cable_output() -> Optional[AudioDevice]:
    """Findet den CABLE-Eingang (= unser Output-Ziel).
    Bevorzugt WASAPI fuer niedrigste Latenz, faellt auf alles andere zurueck.
    """
    candidates = [d for d in list_output_devices()
                  if any(kw in d.name.lower() for kw in _CABLE_OUTPUT_KEYWORDS)]
    if not candidates:
        return None

    # Prioritaet: WASAPI > Windows WDM-KS > MME > DirectSound
    priority = {"Windows WASAPI": 0, "Windows WDM-KS": 1,
                "MME": 2, "Windows DirectSound": 3}
    candidates.sort(key=lambda d: priority.get(d.hostapi_name, 99))
    return candidates[0]


def is_vb_cable_installed() -> bool:
    return find_vb_cable_output() is not None


def default_input_device() -> Optional[int]:
    try:
        dev = sd.default.device
        val = dev[0] if isinstance(dev, (tuple, list)) else dev
        return int(val) if val is not None and val >= 0 else None
    except Exception:
        return None


def default_output_device() -> Optional[int]:
    try:
        dev = sd.default.device
        val = dev[1] if isinstance(dev, (tuple, list)) else dev
        return int(val) if val is not None and val >= 0 else None
    except Exception:
        return None
