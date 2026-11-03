"""Geometria 2D: matrices afines, rutas Bezier y utilidades de formas.

Convencion de matriz: (a, b, c, d, e, f) igual que SVG ``matrix(a b c d e f)``:
    x' = a*x + c*y + e
    y' = b*x + d*y + f
``mat_mul(m1, m2)`` aplica primero m2 y despues m1.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

Point = tuple[float, float]
Matrix = tuple[float, float, float, float, float, float]
IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


# --------------------------------------------------------------------------- matrices
def mat_mul(m1: Matrix, m2: Matrix) -> Matrix:
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def translate(tx: float, ty: float) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def scale_m(sx: float, sy: float | None = None) -> Matrix:
    return (sx, 0.0, 0.0, sx if sy is None else sy, 0.0, 0.0)


def rotate_m(deg: float) -> Matrix:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (c, s, -s, c, 0.0, 0.0)


def about(pivot: Point, m: Matrix) -> Matrix:
    """Aplica ``m`` alrededor de ``pivot``."""
    return mat_mul(translate(pivot[0], pivot[1]), mat_mul(m, translate(-pivot[0], -pivot[1])))


def apply(m: Matrix, p: Point) -> Point:
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def invert(m: Matrix) -> Matrix:
    a, b, c, d, e, f = m
    det = a * d - b * c
    if abs(det) < 1e-12:
        raise ValueError("Matriz no invertible")
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    ie = -(ia * e + ic * f)
    if_ = -(ib * e + id_ * f)
    return (ia, ib, ic, id_, ie, if_)


def det_scale(m: Matrix) -> float:
    """Factor de escala medio de la matriz (raiz del determinante)."""
    return math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))


def is_identity(m: Matrix, eps: float = 1e-6) -> bool:
    return all(abs(a - b) < eps for a, b in zip(m, IDENTITY))


# --------------------------------------------------------------------------- vectores
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_pt(p: Point, q: Point, t: float) -> Point:
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def dist(p: Point, q: Point) -> float:
    return math.hypot(q[0] - p[0], q[1] - p[1])


def unit(p: Point, q: Point) -> Point:
    d = dist(p, q) or 1.0
    return ((q[0] - p[0]) / d, (q[1] - p[1]) / d)


def perp(v: Point) -> Point:
    return (-v[1], v[0])


def add(p: Point, v: Point, k: float = 1.0) -> Point:
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


# --------------------------------------------------------------------------- Path
class Path:
    """Ruta vectorial con comandos absolutos M, L, C, Q y Z."""

    __slots__ = ("cmds",)

    def __init__(self, cmds: Iterable[tuple] | None = None) -> None:
        self.cmds: list[tuple] = list(cmds or [])

    # construccion encadenable
    def M(self, x: float, y: float) -> "Path":
        self.cmds.append(("M", x, y))
        return self

    def L(self, x: float, y: float) -> "Path":
        self.cmds.append(("L", x, y))
        return self

    def C(self, x1: float, y1: float, x2: float, y2: float, x: float, y: float) -> "Path":
        self.cmds.append(("C", x1, y1, x2, y2, x, y))
        return self

    def Q(self, x1: float, y1: float, x: float, y: float) -> "Path":
        self.cmds.append(("Q", x1, y1, x, y))
        return self

    def Z(self) -> "Path":
        self.cmds.append(("Z",))
        return self

    def extend(self, other: "Path") -> "Path":
        self.cmds.extend(other.cmds)
        return self

    def copy(self) -> "Path":
        return Path(self.cmds)

    def __bool__(self) -> bool:
        return bool(self.cmds)

    # transformaciones
    def transformed(self, m: Matrix) -> "Path":
        out: list[tuple] = []
        for c in self.cmds:
            if c[0] == "Z":
                out.append(c)
                continue
            pts = []
            for i in range(1, len(c), 2):
                pts.extend(apply(m, (c[i], c[i + 1])))
            out.append((c[0], *pts))
        return Path(out)

    def translated(self, dx: float, dy: float) -> "Path":
        return self.transformed(translate(dx, dy))

    def scaled(self, sx: float, sy: float | None = None, about_pt: Point = (0.0, 0.0)) -> "Path":
        return self.transformed(about(about_pt, scale_m(sx, sy)))

    def rotated(self, deg: float, about_pt: Point = (0.0, 0.0)) -> "Path":
        return self.transformed(about(about_pt, rotate_m(deg)))

    def mirrored(self, cx: float) -> "Path":
        """Refleja respecto a la recta vertical x = cx."""
        return self.transformed((-1.0, 0.0, 0.0, 1.0, 2 * cx, 0.0))

    def points(self) -> list[Point]:
        pts: list[Point] = []
        for c in self.cmds:
            for i in range(1, len(c), 2):
                pts.append((c[i], c[i + 1]))
        return pts

    def bbox(self) -> tuple[float, float, float, float]:
        pts = self.points()
        if not pts:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    # salida
    def to_d(self, m: Matrix | None = None, nd: int = 2) -> str:
        path = self if m is None else self.transformed(m)
        parts: list[str] = []
        for c in path.cmds:
            if c[0] == "Z":
                parts.append("Z")
            else:
                nums = " ".join(_fmt(v, nd) for v in c[1:])
                parts.append(f"{c[0]}{nums}")
        return " ".join(parts)

    def flatten(self, m: Matrix = IDENTITY) -> list[tuple[list[Point], bool]]:
        """Devuelve subrutas poligonales ``[(puntos, cerrada)]`` ya transformadas por ``m``."""
        subs: list[tuple[list[Point], bool]] = []
        cur: list[Point] = []
        start: Point = (0.0, 0.0)
        pos: Point = (0.0, 0.0)
        closed = False

        def flush() -> None:
            nonlocal cur, closed
            if len(cur) >= 2:
                subs.append((cur, closed))
            cur = []
            closed = False

        for c in self.cmds:
            op = c[0]
            if op == "M":
                flush()
                pos = apply(m, (c[1], c[2]))
                start = pos
                cur = [pos]
            elif op == "L":
                pos = apply(m, (c[1], c[2]))
                cur.append(pos)
            elif op == "C":
                p1 = apply(m, (c[1], c[2]))
                p2 = apply(m, (c[3], c[4]))
                p3 = apply(m, (c[5], c[6]))
                n = _steps(pos, p1, p2, p3)
                for i in range(1, n + 1):
                    t = i / n
                    u = 1 - t
                    cur.append((
                        u * u * u * pos[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
                        u * u * u * pos[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
                    ))
                pos = p3
            elif op == "Q":
                p1 = apply(m, (c[1], c[2]))
                p2 = apply(m, (c[3], c[4]))
                n = _steps(pos, p1, p1, p2)
                for i in range(1, n + 1):
                    t = i / n
                    u = 1 - t
                    cur.append((
                        u * u * pos[0] + 2 * u * t * p1[0] + t * t * p2[0],
                        u * u * pos[1] + 2 * u * t * p1[1] + t * t * p2[1],
                    ))
                pos = p2
            elif op == "Z":
                closed = True
                flush()
                pos = start
                cur = [pos]
        flush()
        return subs


def _fmt(v: float, nd: int = 2) -> str:
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def _steps(p0: Point, p1: Point, p2: Point, p3: Point) -> int:
    length = dist(p0, p1) + dist(p1, p2) + dist(p2, p3)
    return int(clamp(length / 4.0, 4, 48))


# --------------------------------------------------------------------------- constructores
def polygon(points: Sequence[Point], closed: bool = True) -> Path:
    p = Path()
    for i, (x, y) in enumerate(points):
        p.M(x, y) if i == 0 else p.L(x, y)
    if closed:
        p.Z()
    return p


def polyline(points: Sequence[Point]) -> Path:
    return polygon(points, closed=False)


def line(p0: Point, p1: Point) -> Path:
    return Path().M(*p0).L(*p1)


_K = 0.5522847498


def ellipse(cx: float, cy: float, rx: float, ry: float | None = None, rot: float = 0.0) -> Path:
    ry = rx if ry is None else ry
    k = _K
    p = (
        Path()
        .M(cx + rx, cy)
        .C(cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry)
        .C(cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy)
        .C(cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry)
        .C(cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy)
        .Z()
    )
    return p.rotated(rot, (cx, cy)) if rot else p


def rrect(x0: float, y0: float, x1: float, y1: float, r: float = 0.0) -> Path:
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    if r <= 0:
        return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    k = _K * r
    return (
        Path()
        .M(x0 + r, y0).L(x1 - r, y0).C(x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r)
        .L(x1, y1 - r).C(x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1)
        .L(x0 + r, y1).C(x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r)
        .L(x0, y0 + r).C(x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0).Z()
    )


def smooth(points: Sequence[tuple], closed: bool = True, tension: float = 1.0) -> Path:
    """Curva suave (Catmull-Rom -> Bezier) por los puntos.

    Cada punto es ``(x, y)`` o ``(x, y, 'c')``; el tercer elemento marca una esquina
    (tangente nula) para obtener picos o aristas afiladas.
    """
    n = len(points)
    if n < 2:
        return Path()
    pts = [(float(p[0]), float(p[1])) for p in points]
    corner = [len(p) > 2 and p[2] == "c" for p in points]
    path = Path().M(*pts[0])

    def tangent(i: int) -> Point:
        if corner[i % n if closed else i]:
            return (0.0, 0.0)
        if closed:
            a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else:
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, n - 1)]
        return ((b[0] - a[0]) * tension / 6.0, (b[1] - a[1]) * tension / 6.0)

    last = n if closed else n - 1
    for i in range(last):
        j = (i + 1) % n
        t0, t1 = tangent(i), tangent(j)
        p0, p1 = pts[i], pts[j]
        path.C(p0[0] + t0[0], p0[1] + t0[1], p1[0] - t1[0], p1[1] - t1[1], p1[0], p1[1])
    if closed:
        path.Z()
    return path


def mirror_points(right: Sequence[tuple], cx: float, include_axis: bool = True) -> list[tuple]:
    """Dado el lado derecho (de arriba hacia abajo) devuelve el contorno cerrado simetrico.

    Los puntos sobre el eje (x == cx) no se duplican.
    """
    pts = list(right)
    left = []
    for p in reversed(pts):
        if abs(p[0] - cx) < 1e-6:
            continue
        left.append((2 * cx - p[0], p[1]) + tuple(p[2:]))
    return pts + left


def limb(p0: Point, p1: Point, w0: float, w1: float, bulge: float = 0.0, mid: float = 0.4,
         cap0: float = 0.85, cap1: float = 0.85) -> tuple[Path, Path, Path]:
    """Segmento conico para brazos y piernas.

    Devuelve ``(relleno, lado_a, lado_b)``: el relleno es el contorno cerrado y los
    lados son polilineas abiertas utiles para dibujar solo los bordes (sin tapas).
    """
    d = unit(p0, p1)
    n = perp(d)
    wm = (w0 + (w1 - w0) * mid) + bulge
    m = lerp_pt(p0, p1, mid)
    a0, a1, am = add(p0, n, w0 / 2), add(p1, n, w1 / 2), add(m, n, wm / 2)
    b0, b1, bm = add(p0, n, -w0 / 2), add(p1, n, -w1 / 2), add(m, n, -wm / 2)
    c0 = add(p0, d, -w0 / 2 * cap0)
    c1 = add(p1, d, w1 / 2 * cap1)
    fill = smooth([c0, a0, am, a1, c1, b1, bm, b0], closed=True)
    side_a = smooth([a0, am, a1], closed=False)
    side_b = smooth([b0, bm, b1], closed=False)
    return fill, side_a, side_b
