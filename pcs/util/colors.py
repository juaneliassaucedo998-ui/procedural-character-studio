"""Utilidades de color (hex <-> RGB, mezcla, aclarado/oscurecido en HLS)."""
from __future__ import annotations

import colorsys

RGB = tuple[int, int, int]


def hex_to_rgb(h: str) -> RGB:
    """Convierte '#rgb' o '#rrggbb' a (r, g, b)."""
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Color hexadecimal invalido: {h!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r: float, g: float, b: float) -> str:
    c = [max(0, min(255, int(round(v)))) for v in (r, g, b)]
    return "#{:02x}{:02x}{:02x}".format(*c)


def is_hex(value: str) -> bool:
    try:
        hex_to_rgb(value)
        return True
    except (ValueError, AttributeError):
        return False


def mix(a: str, b: str, t: float) -> str:
    """Mezcla lineal de dos colores (t=0 -> a, t=1 -> b)."""
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    return rgb_to_hex(ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t)


def to_hls(c: str) -> tuple[float, float, float]:
    r, g, b = hex_to_rgb(c)
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def from_hls(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, max(0.0, min(1.0, l)), max(0.0, min(1.0, s)))
    return rgb_to_hex(r * 255, g * 255, b * 255)


def adjust(c: str, dl: float = 0.0, ds: float = 0.0, dh: float = 0.0) -> str:
    """Ajuste aditivo en HLS (dl, ds en [-1, 1]; dh en vueltas de matiz)."""
    h, l, s = to_hls(c)
    return from_hls(h + dh, l + dl, s + ds)


def darken(c: str, amt: float) -> str:
    """Oscurece multiplicando la luminosidad; ligero giro de matiz hacia frios."""
    h, l, s = to_hls(c)
    return from_hls(h - 0.012 * amt, l * (1.0 - amt), min(1.0, s * (1.0 + 0.1 * amt)))


def lighten(c: str, amt: float) -> str:
    h, l, s = to_hls(c)
    return from_hls(h + 0.008 * amt, l + (1.0 - l) * amt, s)


def saturate(c: str, k: float) -> str:
    h, l, s = to_hls(c)
    return from_hls(h, l, min(1.0, s * k))


def rotate_hue(c: str, turns: float) -> str:
    return adjust(c, dh=turns)


def luminance(c: str) -> float:
    r, g, b = hex_to_rgb(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
