import json, tempfile, unittest, zipfile
from pathlib import Path
from PIL import Image
from pcs.generator import CharacterConfig, build_character, random_variant
from pcs.engine.svg_writer import scene_to_svg
from pcs.engine.raster import render_vector
from pcs.animation import AnimationClip, render_frames, create_spritesheet
from pcs.export import export_order
from pcs.projects.manager import save_project
class ProductTests(unittest.TestCase):
 def test_character_svg_png_json(self):
  cfg=CharacterConfig(); scene=build_character(cfg)
  self.assertGreater(len(scene.prims),60); self.assertIn('<svg',scene_to_svg(scene))
  im=render_vector(scene,scale=.3,ss=1); self.assertEqual(im.mode,'RGBA'); self.assertIsNotNone(im.getbbox())
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'c.json'; cfg.save(p); self.assertEqual(CharacterConfig.load(p).seed,cfg.seed)
 def test_animation_spritesheet(self):
  frames=render_frames(build_character(CharacterConfig()),AnimationClip('walking',8,4),scale=.2)
  sheet=create_spritesheet(frames,columns=2); self.assertEqual(sheet.size,(frames[0].width*2,frames[0].height*2))
 def test_order_zip_content(self):
  with tempfile.TemporaryDirectory() as d:
   out=export_order(CharacterConfig(),Path(d)/'CLIENT_DELIVERY',animations=('idle','walking','attacking'))
   self.assertTrue(out.exists())
   with zipfile.ZipFile(out) as z:
    names=z.namelist(); self.assertTrue(any(n.endswith('character/character.svg') for n in names)); self.assertTrue(any(n.endswith('spritesheets/character_spritesheet.png') for n in names))
    png=next(n for n in names if n.endswith('character/character.png'))
    with z.open(png) as f: self.assertEqual(Image.open(f).format,'PNG')
 def test_variants_reproducible(self):
  self.assertEqual(random_variant(CharacterConfig(),100).to_dict(),random_variant(CharacterConfig(),100).to_dict())
if __name__=='__main__': unittest.main()
