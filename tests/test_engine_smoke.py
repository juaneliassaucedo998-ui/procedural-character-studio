import unittest
from pcs.util.geometry import ellipse, smooth
from pcs.engine.scene import Scene, Prim, Pose, BoneState, radial_gradient
from pcs.engine.raster import render_vector, BakedRenderer

def make_scene():
    s = Scene(200, 200)
    s.add_bone("arm", "root", (100, 100))
    s.add(Prim(ellipse(100, 100, 40, 40), fill=radial_gradient((100, 100), 40, [(0, "#ff0000", 1), (1, "#0000ff", 1)]), stroke="#000000", stroke_width=3, layer="body"))
    s.add(Prim(smooth([(100, 100), (160, 90), (160, 110)]), fill="#00ff00", bone="arm", layer="arms"))
    return s

class Smoke(unittest.TestCase):
    def test_vector_and_baked(self):
        s = make_scene()
        pose = Pose(bones={"arm": BoneState(rot=30)})
        a = render_vector(s, pose, scale=1, ss=2)
        b = BakedRenderer(s, scale=1, ss=2).render(pose)
        self.assertEqual(a.size, (200, 200))
        self.assertEqual(b.size, (200, 200))
        self.assertIsNotNone(a.getbbox())
        self.assertIsNotNone(b.getbbox())

if __name__ == "__main__":
    unittest.main()
