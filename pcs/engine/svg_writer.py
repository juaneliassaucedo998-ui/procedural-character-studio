"Editable SVG export retaining paths, gradients and articulated transforms."""
from __future__ import annotations
import html
from pcs.engine.scene import Gradient, Pose, Scene

def scene_to_svg(scene: Scene, pose: Pose | None = None) -> str:
    pose=pose or Pose(); defs=[]; body=[]; gradient_ids={}; matrices=scene.world_matrices(pose)
    for prim in scene.sorted_prims(pose.expression):
        transform=''
        if prim.bone in pose.bones:
            transform=' transform="matrix(%s)"' % ' '.join(f'{v:.5g}' for v in matrices[prim.bone])
        fill='none'
        if isinstance(prim.fill,Gradient):
            g=prim.fill; key=g.transformed_key()
            if key not in gradient_ids:
                gid=f'g{len(gradient_ids)}'; gradient_ids[key]=gid
                if g.kind=='linear':
                    x1,y1,x2,y2=g.coords; tag=f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="userSpaceOnUse">'
                else:
                    cx,cy,r=g.coords; tag=f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="userSpaceOnUse">'
                stops=''.join(f'<stop offset="{o*100:.3f}%" stop-color="{col}" stop-opacity="{a}"/>' for o,col,a in g.stops)
                end='</linearGradient>' if g.kind=='linear' else '</radialGradient>'; defs.append(tag+stops+end)
            fill=f'url(#{gradient_ids[key]})'
        elif prim.fill: fill=html.escape(prim.fill,quote=True)
        attrs=[f'd="{prim.path.to_d()}"',f'fill="{fill}"',f'opacity="{prim.opacity:.4g}"']
        if prim.stroke: attrs.extend([f'stroke="{html.escape(prim.stroke,quote=True)}"',f'stroke-width="{prim.stroke_width}"','stroke-linejoin="round"','stroke-linecap="round"'])
        if prim.blend=='screen': attrs.append('style="mix-blend-mode:screen"')
        if prim.blur:
            attrs.append(f'filter="url(#blur{prim.seq})"')
            defs.append(f'<filter id="blur{prim.seq}"><feGaussianBlur stdDeviation="{prim.blur}"/></filter>')
        body.append(f'<path {" ".join(attrs)}{transform} data-layer="{html.escape(prim.layer)}" data-part="{html.escape(prim.part)}"/>')
    title=html.escape(str(scene.meta.get('name','Procedural character')))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.width}" height="{scene.height}" viewBox="0 0 {scene.width} {scene.height}"><title>{title}</title><defs>{''.join(defs)}</defs>{''.join(body)}</svg>'
def save_svg(scene: Scene,path,pose: Pose|None=None)->None:
    from pathlib import Path
    Path(path).write_text(scene_to_svg(scene,pose),encoding='utf-8')
