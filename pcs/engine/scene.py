"""Grafo de escena: primitivas vectoriales, huesos (jerarquia) y poses.

Las primitivas se dibujan en coordenadas de la pose de reposo. Cada primitiva esta
asociada a un hueso; la transformacion de un hueso se compone con la de su padre:

    W_hueso = W_padre * T(pivote + desplazamiento) * R(rot) * S(sx, sy) * T(-pivote)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from pcs.util.geometry import (IDENTITY, Matrix, Path, Point, apply, mat_mul, rotate_m, scale_m,
                               translate)

CANVAS_W = 640
CANVAS_H = 880

# Orden de capas de atras hacia adelante.
LAYER_ORDER: list[str] = [
    "fx_back", "cape_back", "weapon_back", "hair_back", "hat_back", "legs", "pants", "boots", "body",
    "neck", "outfit_lower", "outfit_upper", "armor_lower", "armor_upper", "arms", "sleeves", "pauldrons",
    "weapon", "hands", "gloves", "cape_front", "accessories_body", "head", "ears", "face", "hair_front",
    "hat", "accessories_head", "fx_front",
]


@dataclass
class Gradient:
    """Degradado lineal ('linear': x1,y1,x2,y2) o radial ('radial': cx,cy,r)."""

    kind: str
    coords: tuple
    stops: list[tuple[float, str, float]]  # (offset, color hex, opacidad)

    def transformed_key(self) -> tuple:
        return (self.kind, tuple(round(c, 2) for c in self.coords),
                tuple((round(o, 3), c, round(a, 3)) for o, c, a in self.stops))


def linear_gradient(p0: Point, p1: Point, stops: list[tuple[float, str, float]]) -> Gradient:
    return Gradient("linear", (p0[0], p0[1], p1[0], p1[1]), stops)


def radial_gradient(c: Point, r: float, stops: list[tuple[float, str, float]]) -> Gradient:
    return Gradient("radial", (c[0], c[1], r), stops)


@dataclass
class Prim:
    path: Path
    fill: "str | Gradient | None" = None
    stroke: str | None = None
    stroke_width: float = 0.0
    opacity: float = 1.0
    blur: float = 0.0
    clip: Path | None = None
    blend: str = "normal"          # 'normal' | 'screen'
    bone: str = "root"
    layer: str = "body"
    z: float = 0.0
    part: str = ""                  # componente que genero la primitiva
    when: frozenset | None = None   # expresiones en las que es visible
    seq: int = 0


@dataclass
class BoneDef:
    name: str
    parent: str | None
    pivot: Point


@dataclass
class BoneState:
    rot: float = 0.0
    tx: float = 0.0
    ty: float = 0.0
    sx: float = 1.0
    sy: float = 1.0


@dataclass
class Pose:
    bones: dict[str, BoneState] = field(default_factory=dict)
    expression: str = "neutral"
    flash: float = 0.0     # 0..1 destello blanco (dano)
    opacity: float = 1.0   # opacidad global (desvanecer)

    def state(self, name: str) -> BoneState:
        return self.bones.get(name) or BoneState()


class Scene:
    def __init__(self, width: int = CANVAS_W, height: int = CANVAS_H) -> None:
        self.width = width
        self.height = height
        self.bones: dict[str, BoneDef] = {"root": BoneDef("root", None, (width / 2, height * 0.94))}
        self.prims: list[Prim] = []
        self.meta: dict = {}
        self.anchors: dict[str, tuple[str, Point]] = {}
        self._layer_idx = {n: i for i, n in enumerate(LAYER_ORDER)}

    # --- huesos
    def add_bone(self, name: str, parent: str | None, pivot: Point) -> None:
        if parent is not None and parent not in self.bones:
            raise KeyError(f"Hueso padre desconocido: {parent}")
        self.bones[name] = BoneDef(name, parent, pivot)

    def world_matrices(self, pose: Pose | None = None) -> dict[str, Matrix]:
        pose = pose or Pose()
        out: dict[str, Matrix] = {}
        for name, b in self.bones.items():  # los padres siempre se definen antes
            st = pose.state(name)
            px, py = b.pivot
            local = mat_mul(translate(px + st.tx, py + st.ty),
                            mat_mul(rotate_m(st.rot), mat_mul(scale_m(st.sx, st.sy), translate(-px, -py))))
            out[name] = local if b.parent is None else mat_mul(out[b.parent], local)
        return out

    def anchor_point(self, name: str, pose: Pose | None = None) -> Point:
        """Posicion (en el lienzo) de un ancla nombrada tras aplicar la pose."""
        bone, pt = self.anchors[name]
        return apply(self.world_matrices(pose)[bone], pt)

    # --- primitivas
    def add(self, prim: Prim) -> Prim:
        prim.seq = len(self.prims)
        self.prims.append(prim)
        return prim

    def sorted_prims(self, expression: str | None = "neutral") -> list[Prim]:
        """Primitivas ordenadas por (capa, z, secuencia).

        ``expression=None`` devuelve todas las primitivas, sin filtrar por expresion.
        """
        n = len(LAYER_ORDER)
        items: Iterable[Prim] = self.prims
        if expression is not None:
            items = [p for p in self.prims if p.when is None or expression in p.when]
        return sorted(items, key=lambda p: (self._layer_idx.get(p.layer, n), p.z, p.seq))


def pose_from_dict(d: dict[str, tuple], expression: str = "neutral") -> Pose:
    """Atajo para tests: {'hueso': (rot, tx, ty, sx, sy)}."""
    pose = Pose(expression=expression)
    for k, v in d.items():
        v = tuple(v) + (0.0, 0.0, 0.0, 1.0, 1.0)[len(v):]
        pose.bones[k] = BoneState(*v)
    return pose
