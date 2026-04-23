"""
X-Print Voice Changer - Main Application
=========================================
GUI mit customtkinter, X-Print Industrial-Branding.

Tastenkuerzel (bei fokussiertem Fenster):
    F1 = BYPASS
    F2 = ERWACHSEN
    F3 = BABY
"""
from __future__ import annotations

import math
import sys
import webbrowser
from tkinter import TclError, messagebox

import customtkinter as ctk
import tkinter as tk

from audio_engine import AudioEngine, MODE_ADULT, MODE_BABY, MODE_BYPASS
from device_manager import (
    AudioDevice,
    VB_CABLE_DOWNLOAD_URL,
    default_input_device,
    find_vb_cable_output,
    is_vb_cable_installed,
    list_input_devices,
    list_output_devices,
)

# ============================================================================
# X-Print Branding
# ============================================================================
COLOR_BG              = "#0a0a0a"
COLOR_BG_DEEP         = "#050505"
COLOR_CARD            = "#141414"
COLOR_CARD_HOVER      = "#1d1d1d"
COLOR_BORDER          = "#2a2a2a"
COLOR_TEXT            = "#e6e6e6"
COLOR_TEXT_DIM        = "#7a7a7a"
COLOR_ACCENT_ORANGE   = "#ff6b00"
COLOR_ACCENT_ORANGE_H = "#ff8a33"
COLOR_ACCENT_CYAN     = "#00d4ff"
COLOR_ACCENT_CYAN_H   = "#33ddff"
COLOR_WARN            = "#ffb020"
COLOR_ERROR           = "#ff3040"

# Technische Sans-Serif. Consolas ist auf Windows immer verfuegbar.
FONT_BRAND     = ("Consolas", 22, "bold")
FONT_TAG       = ("Consolas", 11)
FONT_SECTION   = ("Consolas", 11, "bold")
FONT_BODY      = ("Consolas", 12)
FONT_MODE_BIG  = ("Consolas", 20, "bold")
FONT_MODE_DESC = ("Consolas", 10)
FONT_METER     = ("Consolas", 9)
FONT_LATENCY   = ("Consolas", 14, "bold")


# ============================================================================
# Mode-Card Widget
# ============================================================================
class ModeCard(ctk.CTkFrame):
    def __init__(self, parent, *, title: str, description: str,
                 accent: str, on_click):
        super().__init__(parent, fg_color=COLOR_CARD,
                         border_color=COLOR_BORDER, border_width=2,
                         corner_radius=8)
        self._accent = accent
        self._active = False
        self._on_click = on_click

        # Accent-Bar oben
        self._bar = tk.Frame(self, bg=COLOR_BORDER, height=3)
        self._bar.pack(fill="x", side="top")

        self._title = ctk.CTkLabel(self, text=title, font=FONT_MODE_BIG,
                                   text_color=accent)
        self._title.pack(pady=(22, 6))

        self._desc = ctk.CTkLabel(self, text=description, font=FONT_MODE_DESC,
                                  text_color=COLOR_TEXT_DIM,
                                  wraplength=220, justify="center")
        self._desc.pack(pady=(0, 22), padx=12)

        for w in (self, self._title, self._desc, self._bar):
            w.bind("<Button-1>", self._handle_click)
            w.bind("<Enter>",    self._handle_enter)
            w.bind("<Leave>",    self._handle_leave)
            try:
                w.configure(cursor="hand2")
            except tk.TclError:
                pass

    # ------------------------------------------------ Events
    def _handle_click(self, _event=None):
        self._on_click()

    def _handle_enter(self, _event=None):
        if not self._active:
            self.configure(fg_color=COLOR_CARD_HOVER)
            self._bar.configure(bg=self._accent)

    def _handle_leave(self, _event=None):
        if not self._active:
            self.configure(fg_color=COLOR_CARD)
            self._bar.configure(bg=COLOR_BORDER)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.configure(border_color=self._accent, border_width=3,
                           fg_color=COLOR_CARD_HOVER)
            self._bar.configure(bg=self._accent)
        else:
            self.configure(border_color=COLOR_BORDER, border_width=2,
                           fg_color=COLOR_CARD)
            self._bar.configure(bg=COLOR_BORDER)


# ============================================================================
# Level-Meter Widget (animiert, mit Peak-Hold)
# ============================================================================
class LevelMeter(ctk.CTkFrame):
    def __init__(self, parent, *, label: str, accent: str):
        super().__init__(parent, fg_color=COLOR_CARD, corner_radius=4)
        self._accent = accent
        self._level = 0.0
        self._peak_hold = 0.0
        self._peak_hold_frames = 0  # Peak fuer N Frames halten

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(top, text=label, font=FONT_SECTION,
                     text_color=COLOR_TEXT_DIM).pack(side="left")

        self._db_label = ctk.CTkLabel(top, text="-inf dB", font=FONT_METER,
                                      text_color=COLOR_TEXT_DIM)
        self._db_label.pack(side="right")

        self._canvas = tk.Canvas(self, height=18, bg=COLOR_BG_DEEP,
                                 highlightthickness=0, bd=0)
        self._canvas.pack(fill="x", padx=10, pady=(4, 8))

    def update_level(self, level: float) -> None:
        self._level = max(0.0, min(1.5, float(level)))

        # Peak-Hold mit Decay
        if self._level >= self._peak_hold:
            self._peak_hold = self._level
            self._peak_hold_frames = 25
        else:
            if self._peak_hold_frames > 0:
                self._peak_hold_frames -= 1
            else:
                self._peak_hold = max(self._level, self._peak_hold - 0.015)

        try:
            self._redraw()
            self._update_db_text()
        except TclError:
            pass

    def _update_db_text(self):
        if self._level > 1e-5:
            db = 20.0 * math.log10(self._level)
            self._db_label.configure(text=f"{db:+.1f} dB")
        else:
            self._db_label.configure(text="-inf dB")

    def _redraw(self):
        c = self._canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 4 or h < 4:
            return

        # Hintergrund + dezente Zonen
        c.create_rectangle(0, 0, w, h, fill=COLOR_BG_DEEP, outline="")

        level = min(1.0, self._level)
        bar_w = int(w * level)

        # Segment-Gradient: accent -> gelb -> rot
        segs = 64
        for i in range(segs):
            x1 = int(i * w / segs)
            x2 = int((i + 1) * w / segs)
            if x1 >= bar_w:
                break
            x2 = min(x2, bar_w)
            f = i / segs
            if f < 0.70:
                color = self._accent
            elif f < 0.90:
                color = COLOR_WARN
            else:
                color = COLOR_ERROR
            c.create_rectangle(x1, 2, x2, h - 2, fill=color, outline="")

        # Peak-Hold-Linie
        ph = min(1.0, self._peak_hold)
        px = int(w * ph)
        if px > 0:
            c.create_line(px, 0, px, h, fill=COLOR_TEXT, width=1)

        # -6dB / -12dB Marker (referenz)
        for ref_db in (-6.0, -12.0):
            ref = 10 ** (ref_db / 20.0)
            rx = int(w * ref)
            c.create_line(rx, h - 3, rx, h, fill=COLOR_TEXT_DIM, width=1)


# ============================================================================
# Main Application
# ============================================================================
class VoiceChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("X-PRINT // VOICE CHANGER")
        self.geometry("920x660")
        self.minsize(820, 600)
        self.configure(fg_color=COLOR_BG)

        # Engine
        self.engine = AudioEngine()

        # Name->ID Mappings (fuer Dropdown-Lookup)
        self._input_map: dict[str, int] = {}
        self._output_map: dict[str, int] = {}
        self._input_devices: list[AudioDevice] = []
        self._output_devices: list[AudioDevice] = []

        # Hotkey-State
        self.bind("<F1>", lambda e: self._set_mode(MODE_BYPASS))
        self.bind("<F2>", lambda e: self._set_mode(MODE_ADULT))
        self.bind("<F3>", lambda e: self._set_mode(MODE_BABY))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_devices()
        self._check_vb_cable()
        self._start_audio()
        self._schedule_meters()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # --- Header -------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color=COLOR_BG, height=56)
        header.pack(fill="x", padx=24, pady=(18, 4))

        brand = ctk.CTkLabel(header, text="X-PRINT // VOICE CHANGER",
                             font=FONT_BRAND, text_color=COLOR_ACCENT_ORANGE)
        brand.pack(side="left")

        tag = ctk.CTkLabel(header, text="  REALTIME / DISCORD-READY",
                           font=FONT_TAG, text_color=COLOR_ACCENT_CYAN)
        tag.pack(side="left", pady=(10, 0))

        self._hotkey_label = ctk.CTkLabel(
            header, text="F1 BYPASS  /  F2 ERWACHSEN  /  F3 BABY",
            font=FONT_METER, text_color=COLOR_TEXT_DIM)
        self._hotkey_label.pack(side="right", pady=(12, 0))

        sep = tk.Frame(self, bg=COLOR_ACCENT_ORANGE, height=2)
        sep.pack(fill="x", padx=24, pady=(0, 14))

        # --- Routing-Section ---------------------------------------------
        routing = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=6,
                               border_width=1, border_color=COLOR_BORDER)
        routing.pack(fill="x", padx=24, pady=(0, 14))

        ctk.CTkLabel(routing, text="[ AUDIO ROUTING ]", font=FONT_SECTION,
                     text_color=COLOR_ACCENT_CYAN
                     ).pack(anchor="w", padx=14, pady=(10, 2))

        grid = ctk.CTkFrame(routing, fg_color="transparent")
        grid.pack(fill="x", padx=14, pady=(0, 10))
        grid.grid_columnconfigure(0, weight=1, uniform="dev")
        grid.grid_columnconfigure(1, weight=1, uniform="dev")

        ctk.CTkLabel(grid, text="▸ INPUT  (Mikrofon)", font=FONT_TAG,
                     text_color=COLOR_TEXT_DIM
                     ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkLabel(grid, text="▸ OUTPUT (→ CABLE Input)", font=FONT_TAG,
                     text_color=COLOR_TEXT_DIM
                     ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self.input_dropdown = ctk.CTkOptionMenu(
            grid, values=["(Laden...)"],
            fg_color=COLOR_BG_DEEP,
            button_color=COLOR_ACCENT_ORANGE,
            button_hover_color=COLOR_ACCENT_ORANGE_H,
            text_color=COLOR_TEXT,
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_CARD_HOVER,
            command=self._on_input_changed, font=FONT_BODY,
            anchor="w",
        )
        self.input_dropdown.grid(row=1, column=0, sticky="ew",
                                 padx=(0, 8), pady=(4, 0))

        self.output_dropdown = ctk.CTkOptionMenu(
            grid, values=["(Laden...)"],
            fg_color=COLOR_BG_DEEP,
            button_color=COLOR_ACCENT_CYAN,
            button_hover_color=COLOR_ACCENT_CYAN_H,
            text_color=COLOR_TEXT,
            dropdown_fg_color=COLOR_CARD,
            dropdown_text_color=COLOR_TEXT,
            dropdown_hover_color=COLOR_CARD_HOVER,
            command=self._on_output_changed, font=FONT_BODY,
            anchor="w",
        )
        self.output_dropdown.grid(row=1, column=1, sticky="ew",
                                  padx=(8, 0), pady=(4, 0))

        self.cable_status = ctk.CTkLabel(
            routing, text="", font=FONT_TAG, text_color=COLOR_TEXT_DIM,
            anchor="w", justify="left")
        self.cable_status.pack(anchor="w", fill="x", padx=14, pady=(0, 10))

        # --- Mode-Cards ---------------------------------------------------
        modes = ctk.CTkFrame(self, fg_color="transparent")
        modes.pack(fill="x", padx=24, pady=(0, 14))
        modes.grid_columnconfigure(0, weight=1, uniform="card")
        modes.grid_columnconfigure(1, weight=1, uniform="card")
        modes.grid_columnconfigure(2, weight=1, uniform="card")

        self.card_adult = ModeCard(
            modes, title="ERWACHSEN",
            description="Pitch  −12 Halbtöne\nFormant-Absenkung\nTief & markant",
            accent=COLOR_ACCENT_ORANGE,
            on_click=lambda: self._set_mode(MODE_ADULT))
        self.card_adult.grid(row=0, column=0, sticky="nsew",
                             padx=(0, 8), ipady=6)

        self.card_baby = ModeCard(
            modes, title="BABY",
            description="Pitch  +7 Halbtöne\nFormant +25 %\nDezentes Doubling",
            accent=COLOR_ACCENT_CYAN,
            on_click=lambda: self._set_mode(MODE_BABY))
        self.card_baby.grid(row=0, column=1, sticky="nsew",
                            padx=8, ipady=6)

        self.card_bypass = ModeCard(
            modes, title="BYPASS",
            description="Originalstimme\ndurchleiten\nkein Effekt",
            accent=COLOR_TEXT,
            on_click=lambda: self._set_mode(MODE_BYPASS))
        self.card_bypass.grid(row=0, column=2, sticky="nsew",
                              padx=(8, 0), ipady=6)

        self._cards = {MODE_ADULT:  self.card_adult,
                       MODE_BABY:   self.card_baby,
                       MODE_BYPASS: self.card_bypass}
        self.card_bypass.set_active(True)

        # --- Signal Monitor ----------------------------------------------
        monitor = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=6,
                               border_width=1, border_color=COLOR_BORDER)
        monitor.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        ctk.CTkLabel(monitor, text="[ SIGNAL MONITOR ]", font=FONT_SECTION,
                     text_color=COLOR_ACCENT_CYAN
                     ).pack(anchor="w", padx=14, pady=(10, 2))

        self.meter_in = LevelMeter(monitor, label="▸ INPUT",
                                   accent=COLOR_ACCENT_ORANGE)
        self.meter_in.pack(fill="x", padx=14, pady=(4, 4))

        self.meter_out = LevelMeter(monitor, label="▸ OUTPUT",
                                    accent=COLOR_ACCENT_CYAN)
        self.meter_out.pack(fill="x", padx=14, pady=(0, 8))

        foot = ctk.CTkFrame(monitor, fg_color="transparent")
        foot.pack(fill="x", padx=14, pady=(4, 12))

        self.latency_label = ctk.CTkLabel(
            foot, text="LATENCY  --.- ms",
            font=FONT_LATENCY, text_color=COLOR_ACCENT_ORANGE)
        self.latency_label.pack(side="left")

        ctk.CTkLabel(foot, text="   //   BUFFER",
                     font=FONT_BODY, text_color=COLOR_TEXT_DIM
                     ).pack(side="left", padx=(12, 6))

        self.buffer_dropdown = ctk.CTkOptionMenu(
            foot, values=["128", "256", "512", "1024"],
            fg_color=COLOR_BG_DEEP,
            button_color=COLOR_ACCENT_ORANGE,
            button_hover_color=COLOR_ACCENT_ORANGE_H,
            text_color=COLOR_TEXT,
            dropdown_fg_color=COLOR_CARD,
            command=self._on_buffer_changed, width=84, font=FONT_BODY)
        self.buffer_dropdown.set("256")
        self.buffer_dropdown.pack(side="left")

        ctk.CTkLabel(foot, text="samples @ 48 kHz",
                     font=FONT_TAG, text_color=COLOR_TEXT_DIM
                     ).pack(side="left", padx=(6, 0))

        self.status_label = ctk.CTkLabel(
            foot, text="● READY", font=FONT_BODY,
            text_color=COLOR_ACCENT_CYAN)
        self.status_label.pack(side="right")

    # ------------------------------------------------------------------ Devices
    def _load_devices(self):
        try:
            self._input_devices = list_input_devices()
            self._output_devices = list_output_devices()
        except Exception as e:
            messagebox.showerror("Audio-Subsystem",
                                 f"Konnte Geraete nicht auflisten:\n{e}")
            return

        self._input_map = {d.display: d.id for d in self._input_devices}
        self._output_map = {d.display: d.id for d in self._output_devices}

        in_names = list(self._input_map.keys()) or ["(keine Eingaenge)"]
        out_names = list(self._output_map.keys()) or ["(keine Ausgaenge)"]

        self.input_dropdown.configure(values=in_names)
        self.output_dropdown.configure(values=out_names)

        # Default-Input: System-Default (sonst erster Eintrag)
        def_in = default_input_device()
        in_selected = None
        if def_in is not None:
            for d in self._input_devices:
                if d.id == def_in:
                    in_selected = d.display
                    break
        if in_selected is None and self._input_devices:
            # WASAPI bevorzugen
            for d in self._input_devices:
                if "WASAPI" in d.hostapi_name:
                    in_selected = d.display
                    break
            if in_selected is None:
                in_selected = self._input_devices[0].display
        if in_selected:
            self.input_dropdown.set(in_selected)

        # Default-Output: VB-CABLE (falls vorhanden), sonst System-Default
        cable = find_vb_cable_output()
        out_selected = None
        if cable is not None:
            out_selected = cable.display
        elif self._output_devices:
            for d in self._output_devices:
                if "WASAPI" in d.hostapi_name:
                    out_selected = d.display
                    break
            if out_selected is None:
                out_selected = self._output_devices[0].display
        if out_selected:
            self.output_dropdown.set(out_selected)

    def _on_input_changed(self, name: str):
        in_id = self._input_map.get(name)
        out_id = self._output_map.get(self.output_dropdown.get())
        self._restart_engine(in_id, out_id)

    def _on_output_changed(self, name: str):
        in_id = self._input_map.get(self.input_dropdown.get())
        out_id = self._output_map.get(name)
        self._restart_engine(in_id, out_id)

    def _on_buffer_changed(self, value: str):
        try:
            self.engine.set_blocksize(int(value))
            self._refresh_latency()
        except Exception as e:
            messagebox.showerror("Buffer-Fehler", str(e))

    def _restart_engine(self, in_id, out_id):
        try:
            self.engine.set_devices(in_id, out_id)
            self._refresh_latency()
            self._set_status("● LIVE", COLOR_ACCENT_CYAN)
        except Exception as e:
            self._set_status("● ERROR", COLOR_ERROR)
            messagebox.showerror("Audio-Engine", f"Stream-Start fehlgeschlagen:\n{e}")

    def _check_vb_cable(self):
        if is_vb_cable_installed():
            self.cable_status.configure(
                text="  ✓ VB-CABLE erkannt   //   In Discord  "
                     "'CABLE Output (VB-Audio Virtual Cable)'  als Mikrofon setzen",
                text_color=COLOR_ACCENT_CYAN)
        else:
            self.cable_status.configure(
                text="  ⚠ VB-CABLE nicht gefunden   //   Klicken fuer Download: "
                     f"{VB_CABLE_DOWNLOAD_URL}",
                text_color=COLOR_WARN, cursor="hand2")
            self.cable_status.bind(
                "<Button-1>", lambda _e: webbrowser.open(VB_CABLE_DOWNLOAD_URL))

    # ------------------------------------------------------------------ Modes
    def _set_mode(self, mode: str):
        self.engine.set_mode(mode)
        for m, card in self._cards.items():
            card.set_active(m == mode)

    # ------------------------------------------------------------------ Engine
    def _start_audio(self):
        in_id = self._input_map.get(self.input_dropdown.get())
        out_id = self._output_map.get(self.output_dropdown.get())
        self.engine.input_device = in_id
        self.engine.output_device = out_id
        try:
            self.engine.blocksize = int(self.buffer_dropdown.get())
            self.engine.start()
            self._refresh_latency()
            self._set_status("● LIVE", COLOR_ACCENT_CYAN)
        except Exception as e:
            self._set_status("● ERROR", COLOR_ERROR)
            messagebox.showerror(
                "Audio-Engine",
                f"Audio konnte nicht gestartet werden:\n{e}\n\n"
                "- Pruefe dass Mikrofon nicht von anderer App blockiert ist.\n"
                "- Teste verschiedene Host-APIs (MME/WASAPI/DirectSound).\n"
                "- Setze Buffer auf 512 oder 1024 bei Fehlermeldungen.")

    def _refresh_latency(self):
        lat = self.engine.actual_latency_ms
        self.latency_label.configure(text=f"LATENCY  {lat:5.1f} ms")
        # Faerbung: < 50ms = Cyan (gut), < 100ms = Orange, sonst Rot
        if 0 < lat < 50:
            self.latency_label.configure(text_color=COLOR_ACCENT_CYAN)
        elif lat < 100:
            self.latency_label.configure(text_color=COLOR_ACCENT_ORANGE)
        else:
            self.latency_label.configure(text_color=COLOR_ERROR)

    def _set_status(self, text: str, color: str):
        try:
            self.status_label.configure(text=text, text_color=color)
        except TclError:
            pass

    # ------------------------------------------------------------------ Meter-Loop
    def _schedule_meters(self):
        try:
            self.meter_in.update_level(self.engine.input_level)
            self.meter_out.update_level(self.engine.output_level)
        except TclError:
            return
        self.after(33, self._schedule_meters)  # ~30 fps

    # ------------------------------------------------------------------ Shutdown
    def _on_close(self):
        try:
            self.engine.stop()
        except Exception:
            pass
        self.destroy()


def main():
    try:
        app = VoiceChangerApp()
        app.mainloop()
    except Exception as e:
        # Fallback-Fehlerdialog, falls beim Start etwas total schief geht
        try:
            messagebox.showerror("X-Print Voice Changer", f"Fataler Fehler:\n{e}")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
