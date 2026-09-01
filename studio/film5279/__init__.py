"""film5279 — a standalone Kodak VISION 500T 5279 / 2383 emulsion engine.

The package re-implements the research engine's evidence-minimal V72 record
formation, the V49 conservative common-density grain boundary and the two
material observers (2383 xenon projection, Spirit/Cineon Blu-ray scan) as a
CPU-only, ffmpeg-fed video processor.  The spectral stages use the V87 dense
lattices instead of the historical 29-cube / 25-cube caches.
"""

from .pipeline import FILM_GAUGES, PRESETS, FilmParams, decode_to_scene_linear, encode_display, render_frame

__all__ = ["FILM_GAUGES", "PRESETS", "FilmParams", "decode_to_scene_linear", "encode_display", "render_frame"]
