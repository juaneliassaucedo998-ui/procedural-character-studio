from __future__ import annotations
import math, random
from pcs.engine.scene import Prim, Scene, radial_gradient
from pcs.util.geometry import ellipse, smooth, line

def add_effect(scene: Scene, kind='magic', color='#b45cff', intensity=1.0, particles=18, seed=1):
    rng=random.Random(seed); cx,cy=scene.width*.78,scene.height*.43
    glow=radial_gradient((cx,cy),85*intensity,[(0,color,.65),(1,color,0)])
    scene.add(Prim(ellipse(cx,cy,82*intensity,82*intensity),fill=glow,layer='fx_front',part='effect-glow',blend='screen'))
    if kind in ('magic','aura','circle'):
        scene.add(Prim(ellipse(cx,cy,44,44),fill=None,stroke=color,stroke_width=3,opacity=.8,layer='fx_front',part='magic-ring',blend='screen'))
        if kind=='circle':
            scene.add(Prim(ellipse(cx,cy,65,65),fill=None,stroke=color,stroke_width=2,opacity=.6,layer='fx_front',part='magic-ring'))
    elif kind in ('fire','smoke','energy','explosion'):
        for i in range(max(3,particles)):
            x=cx+rng.uniform(-45,45); y=cy+rng.uniform(-52,52); r=rng.uniform(5,15)*intensity
            p=smooth([(x,y-r*1.8),(x+r,y-r*.2),(x+r*.65,y+r),(x-r*.65,y+r),(x-r,y-r*.2)])
            scene.add(Prim(p,fill=color,opacity=rng.uniform(.35,.8),layer='fx_front',part=f'{kind}-particle',blend='screen',blur=2))
    elif kind=='lightning':
        for i in range(4):
            x=cx+rng.uniform(-40,40); y=cy-55
            pts=[(x,y)]
            for _ in range(5): x+=rng.uniform(-20,20); y+=rng.uniform(10,26); pts.append((x,y))
            scene.add(Prim(smooth(pts,closed=False),fill=None,stroke=color,stroke_width=3,layer='fx_front',part='lightning',blend='screen'))
    else:
        for _ in range(max(1,particles)):
            x=cx+rng.uniform(-60,60); y=cy+rng.uniform(-60,60); r=rng.uniform(2,7)*intensity
            scene.add(Prim(ellipse(x,y,r),fill=color,opacity=rng.uniform(.4,1),layer='fx_front',part='particle',blend='screen'))
    return scene
