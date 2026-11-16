"""Technical contracts for the v0.3 additions; no aesthetic score implied."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/ai-scene-architect/scripts'))
import bpy
import bmesh
from builders import build_asset,create_material
from build_scene import bounds


class DetailContracts(unittest.TestCase):
    def setUp(self):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        self.material=create_material(dict(id='v03_contract',color=[.2,.1,.04],roughness=.8,metallic=0,
            emission=0,surface='wood',variation=.04,texture_style='wood_grain'))

    def test_new_meshes_closed_outward_uv_and_sized(self):
        for kind,params in [('cave_shell',{'segments':22,'seed':47}),('platform',{}),('window_wall',{'craft_detail':True}),
                            ('furniture',{'variant':'table','craft_detail':True}),('furniture',{'variant':'tool_rack','craft_detail':True})]:
            with self.subTest(kind=kind,params=params):
                parts=build_asset(dict(id='contract_asset',kind=kind,dimensions=[3,1.5,2],parameters=params),[self.material]*3)
                bpy.context.view_layer.update();box=bounds(parts)
                for axis,dimension in enumerate([3,1.5,2]):self.assertAlmostEqual(box[1][axis]-box[0][axis],dimension,places=4)
                self.assertAlmostEqual(box[0][2],0,places=5)
                for part in parts:
                    self.assertTrue(part.data.uv_layers)
                    bm=bmesh.new();bm.from_mesh(part.data)
                    self.assertTrue(all(e.is_manifold for e in bm.edges),part.name)
                    self.assertGreater(bm.calc_volume(signed=True),0,part.name)
                    bm.free()

    def test_procedural_albedo_packed_with_srgb_encoding(self):
        texture=next(n.image for n in self.material.node_tree.nodes if n.type=='TEX_IMAGE')
        self.assertEqual(list(texture.size),[128,128]);self.assertTrue(texture.packed_file)
        values=list(texture.pixels)
        red=sum(values[0::4])/(len(values)/4)
        expected=1.055*.2**(1/2.4)-.055
        self.assertAlmostEqual(red,expected,delta=.015)
        self.assertFalse(texture.filepath)  # No external photo dependency.


result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DetailContracts))
if not result.wasSuccessful():raise RuntimeError('v0.3 technical contract failed')
