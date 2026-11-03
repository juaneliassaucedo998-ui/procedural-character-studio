from __future__ import annotations
import json, math, random
from dataclasses import asdict, dataclass, field
from pathlib import Path as FilePath
from typing import Any
from pcs.engine.scene import BoneState, Prim, Scene, linear_gradient, radial_gradient
from pcs.util.colors import lighten
from pcs.util.geometry import ellipse, limb, smooth, polygon, line
PALETTES = {
'dark_fantasy':dict(skin='#e7c5ad',shadow='#9e6e68',hair='#211c2c',cloth='#30243b',accent='#a84762',metal='#b69b79',eye='#b95572',outline='#201a27',magic='#b45cff'),
'crimson':dict(skin='#ebc4ab',shadow='#9f6561',hair='#281c28',cloth='#48202e',accent='#bd394b',metal='#d3ad80',eye='#c9474c',outline='#211721',magic='#e74c78'),
'violet':dict(skin='#e8c8b9',shadow='#9b7180',hair='#282139',cloth='#382e55',accent='#8755b8',metal='#c3a6d8',eye='#9871df',outline='#211c30',magic='#bd75ff'),
'golden':dict(skin='#edc8a6',shadow='#a66d58',hair='#583528',cloth='#34404c',accent='#bd8737',metal='#e5c779',eye='#659994',outline='#28222a',magic='#f5d465'),
'ice':dict(skin='#d9e7e9',shadow='#829baa',hair='#31475a',cloth='#355b70',accent='#69b6cb',metal='#c9e6eb',eye='#63c5d1',outline='#1d303f',magic='#78e6ff'),
'poison':dict(skin='#d9cfae',shadow='#898553',hair='#29382b',cloth='#34482f',accent='#82a83f',metal='#c1b77e',eye='#b3d954',outline='#20291e',magic='#a3ec4d'),
'fire':dict(skin='#f0c4a0',shadow='#a96652',hair='#3a2424',cloth='#56312d',accent='#d85b2d',metal='#d7ad75',eye='#f1843c',outline='#2a1c1c',magic='#ff9d38'),
'holy':dict(skin='#edcfb8',shadow='#aa7968',hair='#74513a',cloth='#e4dfd1',accent='#c79d49',metal='#e4ca85',eye='#629c9b',outline='#37303a',magic='#fff0a6'),
'shadow':dict(skin='#c9b8b4',shadow='#796875',hair='#171a25',cloth='#202634',accent='#596384',metal='#8f9aa9',eye='#a56cbe',outline='#141721',magic='#8e69df')}
@dataclass
class CharacterConfig:
    name:str='Gothic Arcanist'; character_class:str='witch'; style:str='dark_fantasy'; palette:str='dark_fantasy'; hair:str='long_black'; outfit:str='gothic_dress'; face:str='calm'; accessories:list[str]=field(default_factory=lambda:['hat','brooch']); seed:int=42; proportions:dict[str,float]=field(default_factory=lambda:{'height':1.0,'head':1.0,'shoulders':1.0}); effect:str='orb'
    @classmethod
    def from_dict(cls,data):
        keys={'name','character_class','style','palette','hair','outfit','face','accessories','seed','proportions','effect'}; payload={k:v for k,v in data.items() if k in keys}
        if 'class' in data and 'character_class' not in payload: payload['character_class']=data['class']
        return cls(**payload)
    def to_dict(self):
        data=asdict(self); data['class']=data.pop('character_class'); return data
    def save(self,path): FilePath(path).write_text(json.dumps(self.to_dict(),indent=2),encoding='utf-8')
    @classmethod
    def load(cls,path): return cls.from_dict(json.loads(FilePath(path).read_text(encoding='utf-8')))
def _add(s,path,fill,layer,bone='root',part='anatomy',stroke=None,width=2,opacity=1,z=0):
    return s.add(Prim(path,fill=fill,stroke=stroke,stroke_width=width,layer=layer,bone=bone,part=part,opacity=opacity,z=z))
def build_character(config: CharacterConfig|dict[str,Any])->Scene:
    '''Compose an original layered fantasy figure from editable vector components.'''
    if isinstance(config,dict): config=CharacterConfig.from_dict(config)
    c=PALETTES.get(config.palette,PALETTES['dark_fantasy']); rng=random.Random(config.seed); s=Scene(640,880); s.meta={'name':config.name,'config':config.to_dict(),'seed':config.seed}
    cx=320; hs=max(.78,min(1.25,config.proportions.get('head',1))); sh=max(.75,min(1.25,config.proportions.get('shoulders',1)))
    s.add_bone('torso','root',(cx,495)); s.add_bone('head','torso',(cx,305)); s.add_bone('arm_l','torso',(cx-83*sh,438)); s.add_bone('arm_r','torso',(cx+83*sh,438)); s.add_bone('leg_l','root',(286,674)); s.add_bone('leg_r','root',(354,674)); s.add_bone('weapon_bone','arm_r',(430,487))
    s.anchors.update({'head':('head',(cx,305)),'left_hand':('arm_l',(195,584)),'right_hand':('arm_r',(445,584)),'weapon':('weapon_bone',(445,500))}); ink=c['outline']
    # Flowing back hair, cape and a rich tailored skirt.
    if config.hair!='short_bob':
        _add(s,smooth([(257,270),(253,348),(223,426),(248,501),(277,465),(290,365),(383,365),(396,469),(422,498),(442,410),(407,327),(390,265)]),c['hair'],'hair_back','head','hair',ink,5)
        for i in range(5):
            x=274+i*20; _add(s,smooth([(x,300),(x-8,355),(x+8,405),(x+2,449)],False),None,'hair_back','head','hair-detail',lighten(c['hair'],.24),2)
    else: _add(s,smooth([(256,270),(255,343),(280,382),(320,365),(363,386),(391,340),(386,265)]),c['hair'],'hair_back','head','hair',ink,5)
    _add(s,smooth([(274,421),(240,456),(203,663),(262,704),(307,539),(320,462)]),c['cloth'],'cape_back','torso','cape',ink,5)
    _add(s,smooth([(366,421),(400,456),(437,663),(378,704),(333,539),(320,462)]),c['cloth'],'cape_back','torso','cape',ink,5)
    _add(s,smooth([(275,650),(365,650),(400,822),(351,838),(322,733),(293,838),(244,822)]),c['cloth'],'outfit_lower','torso','skirt',ink,6)
    _add(s,smooth([(287,678),(353,678),(370,814),(344,820),(322,739),(299,820),(272,814)]),c['accent'],'outfit_lower','torso','skirt-inset',None,2,.82)
    for bone,bx in [('leg_l',294),('leg_r',346)]:
        _add(s,smooth([(bx-17,690),(bx+17,690),(bx+23,775),(bx+17,803),(bx-17,803),(bx-23,775)]),c['shadow'],'legs',bone,'legs',ink,4)
        _add(s,smooth([(bx-29,788),(bx+20,788),(bx+31,833),(bx+20,843),(bx-42,843),(bx-46,831)]),c['metal'],'boots',bone,'boots',ink,4)
        _add(s,line((bx-20,811),(bx+19,811)),None,'boots',bone,'boot-detail',c['accent'],4)
    _add(s,smooth([(282,407),(304,391),(336,391),(359,407),(379,488),(368,575),(391,672),(249,672),(272,575),(261,488)]),linear_gradient((275,400),(380,670),[(0,c['accent'],1),(1,c['cloth'],1)]),'outfit_upper','torso','bodice',ink,6)
    _add(s,smooth([(300,415),(320,427),(340,415),(352,501),(320,570),(288,501)]),c['cloth'],'outfit_upper','torso','bodice-panel',c['metal'],3)
    _add(s,smooth([(278,568),(320,592),(362,568),(375,663),(265,663)]),c['accent'],'armor_lower','torso','waist-panel',c['metal'],3)
    for y in (597,620,643): _add(s,smooth([(280,y),(320,y+10),(360,y)],False),None,'armor_lower','torso','embroidery',c['metal'],2)
    _add(s,smooth([(289,408),(320,440),(351,408),(338,459),(320,472),(302,459)]),c['metal'],'outfit_upper','torso','collar',ink,3)
    _add(s,smooth([(298,353),(342,353),(347,411),(320,436),(293,411)]),c['skin'],'neck','head','neck',ink,4)
    _add(s,smooth([(320,216),(366,230),(388,268),(380,322),(350,365),(320,380),(290,365),(260,322),(252,268),(274,230)]),radial_gradient((307,275),115,[(0,lighten(c['skin'],.16),1),(1,c['skin'],1)]),'head','head','head',ink,5)
    _add(s,ellipse(284,315,19,8,-16),c['shadow'],'face','head','face-shading',None,2,.38); _add(s,ellipse(356,315,19,8,16),c['shadow'],'face','head','face-shading',None,2,.38)
    for ex in (291,349):
        _add(s,ellipse(ex,296,15,9,-5 if ex<320 else 5),'#fff0df','face','head','eyes',ink,2); _add(s,ellipse(ex,297,5.5,7),c['eye'],'face','head','eyes',ink,1); _add(s,ellipse(ex+1,294,2,3),'#ffffff','face','head','eye-highlight')
        _add(s,smooth([(ex-17,284),(ex-8,278),(ex+8,279),(ex+17,286)],False),None,'face','head','brows',ink,4)
    _add(s,smooth([(320,302),(313,326),(321,329)],False),None,'face','head','nose',c['shadow'],2)
    _add(s,smooth([(304,345),(316,350),(324,350),(337,343)],False),None,'face','head','mouth',c['accent'],3)
    _add(s,smooth([(255,277),(259,235),(285,208),(320,198),(359,211),(386,245),(385,285),(360,267),(340,291),(322,260),(299,288),(278,269)]),c['hair'],'hair_front','head','hair',ink,5)
    _add(s,smooth([(273,250),(292,221),(319,210)],False),None,'hair_front','head','hair-detail',lighten(c['hair'],.3),3)
    _add(s,smooth([(366,240),(349,226),(333,222)],False),None,'hair_front','head','hair-detail',lighten(c['hair'],.3),3)
    for bone,sign in [('arm_l',-1),('arm_r',1)]:
        shoulder=(cx+sign*78,437); elbow=(cx+sign*104,510); wrist=(cx+sign*124,584)
        fill,_,_=limb(shoulder,elbow,51,35,6); _add(s,fill,c['cloth'],'sleeves',bone,'sleeve',ink,4)
        fill,_,_=limb(elbow,wrist,34,23,4); _add(s,fill,c['skin'],'arms',bone,'arm',ink,4)
        _add(s,ellipse(*wrist,17,19),c['skin'],'hands',bone,'hand',ink,3)
        _add(s,smooth([(shoulder[0]-25,shoulder[1]+6),(shoulder[0],shoulder[1]-21),(shoulder[0]+25,shoulder[1]+6),(shoulder[0]+18,shoulder[1]+30),(shoulder[0]-18,shoulder[1]+30)]),c['metal'],'pauldrons',bone,'pauldron',ink,4)
    if 'hat' in config.accessories:
        _add(s,smooth([(246,241),(269,188),(292,136),(310,179),(348,114),(351,197),(389,239),(365,250),(270,251)]),c['cloth'],'hat','head','hat',ink,5)
        _add(s,smooth([(263,226),(371,226),(391,248),(245,248)]),c['accent'],'hat','head','hat-band',ink,4)
        _add(s,ellipse(323,236,10,12),c['metal'],'accessories_head','head','hat-buckle',ink,2); _add(s,ellipse(323,236,4,6),c['magic'],'accessories_head','head','gem')
    if {'brooch','skull_brooch'}&set(config.accessories):
        _add(s,ellipse(320,499,16,19),c['metal'],'accessories_body','torso','brooch',ink,3); _add(s,ellipse(320,499,8,10),c['magic'],'accessories_body','torso','brooch-gem',ink,1)
        _add(s,polygon([(320,487),(323,497),(332,499),(323,502),(320,511),(317,502),(308,499),(317,497)]),'#fff0ba','accessories_body','torso','brooch-star')
    if config.character_class in ('witch','mage','warlock'):
        _add(s,smooth([(438,382),(447,389),(391,654),(382,650)]),c['metal'],'weapon','weapon_bone','staff',ink,3)
        _add(s,ellipse(448,365,27,31),c['magic'],'weapon','weapon_bone','staff-crystal',ink,4,.92)
        _add(s,ellipse(448,365,15,20),radial_gradient((443,356),28,[(0,'#fff6d7',.95),(1,c['magic'],.08)]),'weapon','weapon_bone','crystal-glow',opacity=.95)
        for a in (-35,35,145): _add(s,ellipse(448+31*math.cos(math.radians(a)),365+34*math.sin(math.radians(a)),4),c['metal'],'weapon','weapon_bone','crystal-rune')
    for x in (293,347):
        for y in (526,551): _add(s,ellipse(x,y,3.2),c['metal'],'outfit_upper','torso','buttons')
    for _ in range(5):
        x=rng.randint(270,370); y=rng.randint(684,780); _add(s,polygon([(x,y-4),(x+1,y-1),(x+4,y),(x+1,y+1),(x,y+4),(x-1,y+1),(x-4,y),(x-1,y-1)]),c['metal'],'outfit_lower','torso','embroidery',opacity=.8)
    return s
def random_variant(config: CharacterConfig,seed:int)->CharacterConfig:
    rng=random.Random(seed); out=CharacterConfig.from_dict(config.to_dict()); out.seed=seed; out.name=f'{config.name} Variant {seed}'; out.palette=rng.choice(list(PALETTES)); out.hair=rng.choice(['long_black','short_bob','braided','silver_wave']); out.face=rng.choice(['calm','determined','mysterious']); out.proportions={'height':rng.uniform(.92,1.08),'head':rng.uniform(.9,1.12),'shoulders':rng.uniform(.9,1.12)}; return out
