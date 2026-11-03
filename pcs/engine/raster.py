"""Rasterizador propio basado en Pillow + NumPy (sin Cairo ni dependencias nativas).

Dos modos:

* ``render_vector``  - dibuja cada primitiva vectorial directamente (resultado exacto).
* ``BakedRenderer``  - pre-renderiza "runs" de primitivas por hueso a sprites y los
  transforma (afin) en cada fotograma. Es mucho mas rapido para animaciones.

Ambos usan supersampling (``ss``) y reducen con alfa premultiplicado para evitar
halos oscuros en los bordes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from pcs.util.colors import hex_to_rgb
from pcs.util.geometry import IDENTITY, Matrix, apply, det_scale, invert, mat_mul, scale_m, translate
from .scene import Gradient, Pose, Prim, Scene

Polys = list[tuple[list[tuple[float, float]], bool]]


# --------------------------------------------------------------------------- helpers
def _polys(path, m: Matrix, cache: dict) -> Polys:
    key = (id(path), m)
    hit = cache.get(key)
    if hit is None:
        hit = (path, path.flatten(m))  # se conserva la ruta para evitar reutilizar ids
        cache[key] = hit
    return hit[1]


def _bounds(polys: Polys) -> tuple[float, float, float, float] | None:
    xs = [p[0] for pts, _ in polys for p in pts]
    ys = [p[1] for pts, _ in polys for p in pts]
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _fill_mask(polys: Polys, region: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, w, h = region
    subs = [pts for pts, _ in polys if len(pts) >= 3]
    mask = Image.new("L", (w, h), 0)
    if not subs:
        return mask
    if len(subs) == 1:
        ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in subs[0]], fill=255)
        return mask
    for pts in subs:  # regla par-impar: XOR de las subrutas
        tmp = Image.new("L", (w, h), 0)
        ImageDraw.Draw(tmp).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
        mask = ImageChops.difference(mask, tmp)
    return mask


def _stroke_mask(polys: Polys, width_px: float, region: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, w, h = region
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    wi = max(1, int(round(width_px)))
    for pts, closed in polys:
        P = [(x - x0, y - y0) for x, y in pts]
        if closed:
            P.append(P[0])
        d.line(P, fill=255, width=wi, joint="curve")
        if wi > 2:
            r = wi / 2.0
            ends = P if closed else [P[0], P[-1]]
            for ex, ey in ends:
                d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=255)
    return mask


def _gradient_array(g: Gradient, m: Matrix, box: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = box
    xs = (np.arange(x0, x1, dtype=np.float32) + 0.5)[None, :]
    ys = (np.arange(y0, y1, dtype=np.float32) + 0.5)[:, None]
    if g.kind == "linear":
        p1 = apply(m, (g.coords[0], g.coords[1]))
        p2 = apply(m, (g.coords[2], g.coords[3]))
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        den = dx * dx + dy * dy or 1.0
        t = ((xs - p1[0]) * dx + (ys - p1[1]) * dy) / den
    else:
        c = apply(m, (g.coords[0], g.coords[1]))
        r = max(g.coords[2] * det_scale(m), 1e-3)
        t = np.hypot(xs - c[0], ys - c[1]) / r
    t = np.clip(t, 0.0, 1.0)
    offs = np.array([s[0] for s in g.stops], dtype=np.float32)
    cols = np.array([hex_to_rgb(s[1]) for s in g.stops], dtype=np.float32)
    alph = np.array([s[2] for s in g.stops], dtype=np.float32)
    out = np.empty(t.shape + (4,), dtype=np.uint8)
    for ch in range(3):
        out[..., ch] = np.interp(t, offs, cols[:, ch]).astype(np.uint8)
    out[..., 3] = (np.interp(t, offs, alph) * 255).astype(np.uint8)
    return out


def _screen(canvas: Image.Image, rgb: np.ndarray, alpha: np.ndarray, x0: int, y0: int) -> None:
    """Mezcla 'screen' sobre ``canvas`` (RGBA, alfa recto) en la region indicada."""
    h, w = alpha.shape
    box = (x0, y0, x0 + w, y0 + h)
    dst = np.asarray(canvas.crop(box), dtype=np.float32) / 255.0
    da = dst[..., 3]
    d_p = dst[..., :3] * da[..., None]
    s_p = rgb * alpha[..., None]
    out_p = d_p + s_p - d_p * s_p
    out_a = da + alpha - da * alpha
    out_rgb = out_p / np.maximum(out_a, 1e-6)[..., None]
    res = np.dstack([out_rgb, out_a])
    canvas.paste(Image.fromarray((np.clip(res, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA"), box)


def _paint(canvas: Image.Image, fill, mask: Image.Image, prim: Prim, m: Matrix,
           box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    op = prim.opacity
    if isinstance(fill, str):
        rgb = hex_to_rgb(fill)
        if op < 0.999:
            mask = mask.point([int(i * op) for i in range(256)])
        if prim.blend == "screen":
            alpha = np.asarray(mask, dtype=np.float32) / 255.0
            col = np.broadcast_to(np.array(rgb, dtype=np.float32) / 255.0, alpha.shape + (3,))
            _screen(canvas, col, alpha, x0, y0)
        else:
            layer = Image.new("RGBA", mask.size, rgb + (0,))
            layer.putalpha(mask)
            canvas.alpha_composite(layer, (x0, y0))
        return
    arr = _gradient_array(fill, m, box)
    alpha = arr[..., 3].astype(np.float32) * np.asarray(mask, dtype=np.float32) / 255.0 * op / 255.0
    if prim.blend == "screen":
        _screen(canvas, arr[..., :3].astype(np.float32) / 255.0, alpha, x0, y0)
    else:
        layer = Image.fromarray(np.dstack([arr[..., :3], (alpha * 255 + 0.5).astype(np.uint8)]), "RGBA")
        canvas.alpha_composite(layer, (x0, y0))


def _prim_box(prim: Prim, m: Matrix, cache: dict, limit: tuple[int, int] | None
              ) -> tuple[int, int, int, int] | None:
    polys = _polys(prim.path, m, cache)
    b = _bounds(polys)
    if b is None:
        return None
    s = det_scale(m)
    pad = (prim.stroke_width * s / 2 if prim.stroke else 0) + 3 * prim.blur * s + 2
    x0, y0, x1, y1 = b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad
    if prim.clip is not None:
        cb = _bounds(_polys(prim.clip, m, cache))
        if cb is None:
            return None
        x0, y0, x1, y1 = max(x0, cb[0] - 1), max(y0, cb[1] - 1), min(x1, cb[2] + 1), min(y1, cb[3] + 1)
    ix0, iy0, ix1, iy1 = int(math.floor(x0)), int(math.floor(y0)), int(math.ceil(x1)), int(math.ceil(y1))
    if limit is not None:
        ix0, iy0, ix1, iy1 = max(0, ix0), max(0, iy0), min(limit[0], ix1), min(limit[1], iy1)
    if ix1 <= ix0 or iy1 <= iy0:
        return None
    return ix0, iy0, ix1, iy1


def draw_prim(canvas: Image.Image, prim: Prim, m: Matrix, cache: dict) -> None:
    """Dibuja una primitiva sobre ``canvas`` usando la matriz ``m`` (unidades -> pixeles)."""
    box = _prim_box(prim, m, cache, canvas.size)
    if box is None:
        return
    x0, y0, x1, y1 = box
    region = (x0, y0, x1 - x0, y1 - y0)
    s = det_scale(m)
    blur = prim.blur * s
    polys = _polys(prim.path, m, cache)
    clip_mask = None
    if prim.clip is not None:
        clip_mask = _fill_mask(_polys(prim.clip, m, cache), region)

    def finish(mask: Image.Image) -> Image.Image:
        if blur > 0.05:
            mask = mask.filter(ImageFilter.GaussianBlur(blur))
        if clip_mask is not None:
            mask = ImageChops.multiply(mask, clip_mask)
        return mask

    if prim.fill is not None:
        _paint(canvas, prim.fill, finish(_fill_mask(polys, region)), prim, m, box)
    if prim.stroke and prim.stroke_width > 0:
        smask = finish(_stroke_mask(polys, prim.stroke_width * s, region))
        _paint(canvas, prim.stroke, smask, prim, m, box)


# --------------------------------------------------------------------------- finalizacion
def _downsample(canvas: Image.Image, ss: int) -> Image.Image:
    if ss <= 1:
        return canvas
    return canvas.convert("RGBa").reduce(ss).convert("RGBA")


def _post(img: Image.Image, pose: Pose, background) -> Image.Image:
    if pose.flash > 0.001 or pose.opacity < 0.999:
        arr = np.asarray(img, dtype=np.float32).copy()
        if pose.flash > 0.001:
            f = min(1.0, pose.flash)
            arr[..., :3] = arr[..., :3] * (1 - f) + 255.0 * f
        if pose.opacity < 0.999:
            arr[..., 3] *= max(0.0, pose.opacity)
        img = Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8), "RGBA")
    if background is not None:
        bg = Image.new("RGBA", img.size, tuple(background) + (255,) if len(background) == 3 else tuple(background))
        bg.alpha_composite(img)
        img = bg
    return img


def _canvas_size(scene: Scene, scale: float, ss: int) -> tuple[int, int]:
    return (max(1, int(round(scene.width * scale))) * ss, max(1, int(round(scene.height * scale))) * ss)


# --------------------------------------------------------------------------- render vectorial
def render_vector(scene: Scene, pose: Pose | None = None, scale: float = 1.0, ss: int = 2,
                  background=None) -> Image.Image:
    pose = pose or Pose()
    W, H = _canvas_size(scene, scale, ss)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base = scale_m(W / scene.width, H / scene.height)
    mats = scene.world_matrices(pose)
    cache: dict = {}
    for prim in scene.sorted_prims(pose.expression):
        draw_prim(canvas, prim, mat_mul(base, mats[prim.bone]), cache)
    return _post(_downsample(canvas, ss), pose, background)


# --------------------------------------------------------------------------- render por sprites
@dataclass
class _Run:
    bone: str
    when: frozenset | None
    x0: int
    y0: int
    rgba: Image.Image
    premult: Image.Image


def _over(canvas: Image.Image, img: Image.Image, x: int, y: int) -> None:
    """alpha_composite con recorte (admite destinos parcialmente fuera del lienzo)."""
    cw, ch = canvas.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(img.width, cw - x), min(img.height, ch - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, img.width, img.height):
        img = img.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(img, (x + sx0, y + sy0))


class BakedRenderer:
    """Renderizador rapido para animaciones: sprites por hueso + transformacion afin."""

    def __init__(self, scene: Scene, scale: float = 1.0, ss: int = 2) -> None:
        self.scene = scene
        self.ss = ss
        self.W, self.H = _canvas_size(scene, scale, ss)
        self.base = scale_m(self.W / scene.width, self.H / scene.height)
        self.runs: list[_Run] = []
        self._bake()

    def _bake(self) -> None:
        cache: dict = {}
        groups: list[tuple[str, frozenset | None, list[Prim]]] = []
        for prim in self.scene.sorted_prims(None):
            if groups and groups[-1][0] == prim.bone and groups[-1][1] == prim.when:
                groups[-1][2].append(prim)
            else:
                groups.append((prim.bone, prim.when, [prim]))
        for bone, when, prims in groups:
            boxes = [b for b in (_prim_box(p, self.base, cache, None) for p in prims) if b]
            if not boxes:
                continue
            x0 = min(b[0] for b in boxes)
            y0 = min(b[1] for b in boxes)
            x1 = max(b[2] for b in boxes)
            y1 = max(b[3] for b in boxes)
            w, h = max(1, min(x1 - x0, 6000)), max(1, min(y1 - y0, 6000))
            sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            m = mat_mul(translate(-x0, -y0), self.base)
            sub_cache: dict = {}
            for p in prims:
                draw_prim(sprite, p, m, sub_cache)
            self.runs.append(_Run(bone, when, x0, y0, sprite, sprite.convert("RGBa")))

    def render(self, pose: Pose | None = None, background=None) -> Image.Image:
        pose = pose or Pose()
        mats = self.scene.world_matrices(pose)
        canvas = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        base_inv = invert(self.base)
        for run in self.runs:
            if run.when is not None and pose.expression not in run.when:
                continue
            a = mat_mul(self.base, mat_mul(mats[run.bone], base_inv))  # espacio de pixeles
            w, h = run.rgba.size
            if abs(a[0] - 1) < 1e-6 and abs(a[3] - 1) < 1e-6 and abs(a[1]) < 1e-6 and abs(a[2]) < 1e-6:
                _over(canvas, run.rgba, int(round(run.x0 + a[4])), int(round(run.y0 + a[5])))
                continue
            corners = [apply(a, (run.x0 + u, run.y0 + v)) for u, v in ((0, 0), (w, 0), (w, h), (0, h))]
            ox0 = max(0, int(math.floor(min(c[0] for c in corners))))
            oy0 = max(0, int(math.floor(min(c[1] for c in corners))))
            ox1 = min(self.W, int(math.ceil(max(c[0] for c in corners))))
            oy1 = min(self.H, int(math.ceil(max(c[1] for c in corners))))
            if ox1 <= ox0 or oy1 <= oy0:
                continue
            ia, ib, ic, id_, ie, if_ = invert(a)
            # entrada(sprite) = inv(a)(salida) - (x0, y0), con salida = region + (ox0, oy0)
            data = (ia, ic, ia * ox0 + ic * oy0 + ie - run.x0,
                    ib, id_, ib * ox0 + id_ * oy0 + if_ - run.y0)
            warped = run.premult.transform((ox1 - ox0, oy1 - oy0), Image.AFFINE, data,
                                           resample=Image.BICUBIC)
            _over(canvas, warped.convert("RGBA"), ox0, oy0)
        return _post(_downsample(canvas, self.ss), pose, background)
