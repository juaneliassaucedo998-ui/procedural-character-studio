from __future__ import annotations
import math
from dataclasses import dataclass
from pcs.engine.scene import BoneState, Pose, Scene
from pcs.engine.raster import BakedRenderer
@dataclass
class AnimationClip:
    name: str
    fps: int = 12
    frames: int = 12
    loop: bool = True
    amplitude: float = 1.0
    speed: float = 1.0
    def pose_at(self,index: int) -> Pose:
        phase=(index/max(1,self.frames if self.loop else self.frames-1))*2*math.pi*self.speed
        p=Pose(); a=self.amplitude
        if self.name in ('idle','breathing'):
            p.bones['torso']=BoneState(ty=math.sin(phase)*4*a,sy=1+math.sin(phase)*.008*a)
            p.bones['head']=BoneState(rot=math.sin(phase+.4)*2*a)
        elif self.name in ('walking','running'):
            factor=1.0 if self.name=='walking' else 1.65
            p.bones['leg_l']=BoneState(rot=math.sin(phase)*22*a*factor,ty=abs(math.sin(phase))*5*a)
            p.bones['leg_r']=BoneState(rot=-math.sin(phase)*22*a*factor,ty=abs(math.sin(phase+math.pi))*5*a)
            p.bones['arm_l']=BoneState(rot=-math.sin(phase)*18*a*factor)
            p.bones['arm_r']=BoneState(rot=math.sin(phase)*18*a*factor)
            p.bones['torso']=BoneState(ty=abs(math.sin(phase*2))*4*a)
        elif self.name=='jumping':
            p.bones['root']=BoneState(ty=-abs(math.sin(phase/2))*95*a)
            p.bones['leg_l']=BoneState(rot=math.sin(phase)*18*a); p.bones['leg_r']=BoneState(rot=-math.sin(phase)*18*a)
        elif self.name in ('attacking','casting'):
            strike=max(0,math.sin(phase))
            p.bones['arm_r']=BoneState(rot=-70*strike*a)
            p.bones['weapon_bone']=BoneState(rot=80*strike*a)
            p.bones['torso']=BoneState(rot=-10*strike*a)
        elif self.name=='taking_damage':
            p.bones['torso']=BoneState(rot=math.sin(phase)*9*a,tx=math.sin(phase*3)*8*a); p.flash=max(0,math.sin(phase))*.5
        elif self.name=='death':
            t=index/max(1,self.frames-1); p.bones['torso']=BoneState(rot=82*t*a); p.opacity=max(0,1-t)
        elif self.name=='victory':
            p.bones['arm_l']=BoneState(rot=-55*abs(math.sin(phase))*a); p.bones['arm_r']=BoneState(rot=55*abs(math.sin(phase))*a)
            p.bones['torso']=BoneState(ty=-abs(math.sin(phase))*10*a)
        return p

def default_clips():
    return [AnimationClip(n,fps=12,frames=12,loop=n in ('idle','breathing','walking','running')) for n in ('idle','breathing','walking','running','jumping','attacking','casting','taking_damage','death','victory')]
def render_frames(scene: Scene, clip: AnimationClip, scale: float=0.5):
    renderer=BakedRenderer(scene,scale=scale,ss=1)
    return [renderer.render(clip.pose_at(i)) for i in range(clip.frames)]
def create_spritesheet(frames, columns: int | None=None):
    from PIL import Image
    if not frames: raise ValueError('No animation frames')
    cols=columns or len(frames); rows=math.ceil(len(frames)/cols)
    sheet=Image.new('RGBA',(frames[0].width*cols,frames[0].height*rows),(0,0,0,0))
    for i,im in enumerate(frames):
        if im.size != frames[0].size: raise ValueError('Frames must have uniform dimensions')
        sheet.alpha_composite(im,((i%cols)*im.width,(i//cols)*im.height))
    return sheet
