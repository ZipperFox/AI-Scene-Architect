"""Blender-only geometry and revision guard regression; does not save scenes."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/ai-scene-architect/scripts'))
import bpy
import bmesh
from builders import build_asset, create_material
from build_scene import assemble, authorize_revision, bounds
from scene_plan import PlanError, read_json


class BuilderContracts(unittest.TestCase):
    def setUp(self):
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        self.material=create_material(dict(id='fixture_wood',color=[.2,.1,.04],roughness=.8,metallic=0,emission=0,surface='wood',variation=.1))

    def test_all_builder_variants_have_dimensions_uvs_and_outward_closed_meshes(self):
        cases=[('ground',{}),('wall',{}),('beam',{}),('timber_frame',{'braces':True}),
               ('rock',{'seed':17}),('rock_wall',{'seed':21,'segments':7}),
               ('crystal',{'segments':5}),('furniture',{'variant':'table'}),
               ('furniture',{'variant':'bench'}),('furniture',{'variant':'crate'}),
               ('mechanism',{'variant':'minecart'}),('mechanism',{'variant':'winch'})]
        for index,(kind,parameters) in enumerate(cases):
            with self.subTest(kind=kind,parameters=parameters):
                asset=dict(id='fixture_'+str(index),kind=kind,dimensions=[2,1,1.5],materials=['fixture_wood'],parameters=parameters)
                parts=build_asset(asset,[self.material]*3)
                bpy.context.view_layer.update()
                box=bounds(parts)
                self.assertAlmostEqual(box[0][2],0,places=5)
                for axis,dimension in enumerate(asset['dimensions']):self.assertAlmostEqual(box[1][axis]-box[0][axis],dimension,places=4)
                for part in parts:
                    self.assertTrue(part.data.uv_layers)
                    bm=bmesh.new();bm.from_mesh(part.data)
                    self.assertTrue(all(e.is_manifold for e in bm.edges),part.name)
                    self.assertGreater(bm.calc_volume(signed=True),0,part.name)
                    bm.free()

    def test_seed_is_repeatable_and_changes_natural_geometry(self):
        asset=dict(id='seed_fixture',kind='rock',dimensions=[2,1,1],materials=['fixture_wood'],parameters={'seed':7})
        def coordinates():return [tuple(v.co) for o in build_asset(asset,[self.material]) for v in o.data.vertices]
        first=coordinates();self.assertEqual(first,coordinates())
        asset['parameters']['seed']=8;self.assertNotEqual(first,coordinates())

    def test_shared_asset_mesh_is_reused_but_objects_are_editable(self):
        plan=read_json(ROOT/'examples/woodwork-shop/scene_plan.json')
        groups=assemble(plan)
        a=groups['storage_lower'];b=groups['storage_upper']
        self.assertIs(a[0].data,b[0].data)
        self.assertIsNot(a[0],b[0])
        self.assertNotEqual(a[0].parent,b[0].parent)
        self.assertAlmostEqual(bounds(b)[0][2],.65,places=5)

    def test_revision_three_and_existing_history_reset_are_rejected(self):
        with self.assertRaises(PlanError):authorize_revision(3,None)
        with tempfile.TemporaryDirectory() as directory:
            history=Path(directory)/'existing.json';history.write_text('[]')
            with self.assertRaises(PlanError):authorize_revision(0,history)
        with self.assertRaises(PlanError):authorize_revision(2,None)


suite=unittest.defaultTestLoader.loadTestsFromTestCase(BuilderContracts)
result=unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful():raise RuntimeError('Blender contract checks failed')
