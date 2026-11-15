"""Schema, relationships, genuine reuse, and journal preservation boundaries."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/ai-scene-architect/scripts'))
from scene_plan import PlanError, preview_cameras, read_json, validate_plan, validate_schema
from prepare_planning import planning_request
from review_history import append_review


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan=read_json(ROOT/'examples/crystal-mine/scene_plan.json')

    def invalid(self, change):
        change(self.plan)
        with self.assertRaises(PlanError):validate_plan(self.plan)

    def test_two_different_valid_plans_reuse_families(self):
        first=validate_plan(self.plan)
        second=validate_plan(read_json(ROOT/'examples/woodwork-shop/scene_plan.json'))
        self.assertNotEqual(first['scene_type'],second['scene_type'])
        self.assertFalse(any(a['kind']=='crystal' for a in second['assets']))
        self.assertTrue({'furniture','mechanism','beam','timber_frame'} <=
                        {a['kind'] for a in first['assets']} & {a['kind'] for a in second['assets']})

    def test_unknown_fields_fail(self):self.invalid(lambda p:p.update(typo=True))
    def test_wrong_coordinate_system(self):self.invalid(lambda p:p['space'].update(up_axis='Y'))
    def test_negative_dimensions(self):self.invalid(lambda p:p['assets'][0].update(dimensions=[1,-1,1]))
    def test_boolean_is_not_seed(self):self.invalid(lambda p:p.update(seed=True))
    def test_nonfinite(self):self.invalid(lambda p:p['objects'][0].update(position=[float('nan'),0,0]))
    def test_wrong_vector_size(self):self.invalid(lambda p:p['objects'][0].update(position=[0,0]))
    def test_unsupported_builder(self):self.invalid(lambda p:p['assets'][0].update(kind='mystery'))
    def test_material_reference(self):self.invalid(lambda p:p['assets'][0].update(materials=['missing']))
    def test_asset_reference(self):self.invalid(lambda p:p['objects'][0].update(asset='missing'))
    def test_duplicate_id(self):self.invalid(lambda p:p['objects'].append(copy.deepcopy(p['objects'][0])))
    def test_support_reference(self):self.invalid(lambda p:p['objects'][1].update(support='missing'))
    def test_support_cycle(self):
        def change(p):
            p['objects'][0]['support']='back_wall'
        self.invalid(change)
    def test_unknown_overlap(self):self.invalid(lambda p:p['objects'][1].update(allow_overlap_with=['missing']))
    def test_unknown_camera(self):self.invalid(lambda p:p.update(hero_camera='missing'))
    def test_hero_selection_is_not_array_order(self):
        self.plan['hero_camera']=self.plan['cameras'][-1]['id']
        self.assertEqual(preview_cameras(self.plan)[0],self.plan['hero_camera'])
        self.assertEqual(len(set(preview_cameras(self.plan))),3)
    def test_global_identifiers(self):self.invalid(lambda p:p['lights'][0].update(id='floor'))
    def test_wrong_parameter_for_builder(self):self.invalid(lambda p:p['assets'][0]['parameters'].update(segments=9))
    def test_missing_furniture_variant(self):
        def change(p):
            next(a for a in p['assets'] if a['kind']=='furniture')['parameters'].pop('variant')
        self.invalid(change)
    def test_unimplemented_schema_keyword_fails_closed(self):
        with self.assertRaises(PlanError):validate_schema(1,{'type':'number','multipleOf':2})
    def test_brief_is_kept_not_keyword_mapped(self):
        brief='A courtyard with a hand winch; do not create a mine.'
        result=planning_request(brief)
        self.assertIn(brief,result)
        self.assertIn('do not copy an',result)
    def test_empty_brief_rejected(self):
        with self.assertRaises(ValueError):planning_request(' ')


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.history=self.dir/'reviews.json'
        self.manifest=self.dir/'manifest.json'
        views={}
        for name in ('hero','three_quarter','top'):
            image=self.dir/(name+'.png');image.write_bytes(name.encode())
            views[name]={'path':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()}
        self.manifest.write_text(json.dumps({'viewpoints':views}),encoding='utf-8')
        self.review={'iteration':0,'visual_reviewed':True,'change_signature':'synthetic-fixture',
                     'renders':{k:v['sha256'] for k,v in views.items()},
                     'issues':[{'id':'test','severity':1,'evidence':'Synthetic journal test'}]}

    def test_append_preserves_history_and_stops_after_two(self):
        for i in range(3):
            self.review['iteration']=i
            result=append_review(self.history,self.review,self.manifest)
            self.assertEqual(len(read_json(self.history)),i+1)
        self.assertEqual(result['reason'],'revision_budget_reached')
        before=self.history.read_bytes()
        self.review['iteration']=3
        with self.assertRaises(PlanError):append_review(self.history,self.review,self.manifest)
        self.assertEqual(before,self.history.read_bytes())

    def test_cannot_reset_existing_history(self):
        append_review(self.history,self.review,self.manifest)
        before=self.history.read_bytes()
        with self.assertRaises(PlanError):append_review(self.history,self.review,self.manifest)
        self.assertEqual(before,self.history.read_bytes())

    def test_hash_mismatch_cannot_append(self):
        (self.dir/'top.png').write_bytes(b'changed')
        with self.assertRaises(PlanError):append_review(self.history,self.review,self.manifest)
        self.assertFalse(self.history.exists())

    def test_all_three_views_required(self):
        self.review['renders'].pop('top')
        with self.assertRaises(PlanError):append_review(self.history,self.review,self.manifest)

    def test_incomplete_manifest_rejected(self):
        manifest=read_json(self.manifest)
        manifest['viewpoints'].pop('top')
        self.manifest.write_text(json.dumps(manifest))
        self.review['renders'].pop('top')
        with self.assertRaises(PlanError):append_review(self.history,self.review,self.manifest)

    def test_uninspected_review_rejected(self):
        self.review['visual_reviewed']=False
        with self.assertRaises(ValueError):append_review(self.history,self.review,self.manifest)

    def test_existing_lock_prevents_overwrite(self):
        self.history.with_name(self.history.name+'.lock').write_text('other-writer')
        with self.assertRaises(FileExistsError):append_review(self.history,self.review,self.manifest)


if __name__=='__main__':unittest.main()
