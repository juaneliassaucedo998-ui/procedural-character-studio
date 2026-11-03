"Discoverable presets and component manifest API."""
from __future__ import annotations
from dataclasses import dataclass
from pcs.generator.character import PALETTES
@dataclass(frozen=True)
class Component:
    id: str
    category: str
    label: str
    description: str
COMPONENTS=[Component(i,c,l,d) for i,c,l,d in [
('head_oval','heads','Oval face','Stylized sculpted face'),('eyes_almond','eyes','Almond eyes','Expressive detailed eyes'),('hair_long','hair','Long waves','Layered long hair'),('hair_bob','hair','Short bob','Short bob haircut'),('hair_braided','hair','Braided','Braided hair variant'),('body_female','bodies','Fantasy silhouette','Stylized fantasy anatomy'),('dress_gothic','outfits','Gothic dress','Layered tailored dress'),('armor_light','armor','Light armor','Decorative shoulder armor'),('boots_tall','boots','Tall boots','Knee-high fantasy boots'),('staff_crystal','weapons','Crystal staff','Arcane staff with crystal'),('hat_witch','accessories','Witch hat','Pointed hat with band'),('brooch_gem','accessories','Gem brooch','Enamel and gem ornament')]]
def list_components(category: str | None=None):
    return [c for c in COMPONENTS if category is None or c.category==category]
def add_component(component: Component) -> None:
    '''Runtime extension hook; custom components can be registered without editing core.'''
    if any(c.id==component.id for c in COMPONENTS): raise ValueError(f'Component id already registered: {component.id}')
    COMPONENTS.append(component)
def list_palettes(): return sorted(PALETTES)
