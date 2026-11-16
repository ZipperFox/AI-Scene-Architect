"""Dependency-free validation of the bundled Scene Plan JSON Schema and relations.

This deliberately implements only the JSON Schema keywords used by our schema;
it is not advertised as a general JSON Schema implementation. Unknown keywords
fail closed. The schema can also be used with a standard Draft 2020-12 validator.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / 'references/scene-plan.schema.json'
KINDS = ('ground', 'wall', 'rock', 'rock_wall', 'beam', 'timber_frame',
         'crystal', 'furniture', 'mechanism')


class PlanError(ValueError):
    pass


def read_json(path):
    def reject(value):
        raise PlanError('Non-finite JSON number: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=reject)


def validate_schema(value, schema, root=None, path='$'):
    root = schema if root is None else root
    supported = {'$schema', '$id', '$defs', '$ref', 'title', 'description',
                 'type', 'properties', 'required', 'additionalProperties',
                 'items', 'minItems', 'maxItems', 'minimum', 'maximum',
                 'exclusiveMinimum', 'minLength', 'maxLength', 'pattern', 'enum', 'const'}
    unknown = set(schema) - supported
    if unknown:
        raise PlanError(f'{path}: unsupported schema keywords {sorted(unknown)}')
    if '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/'):
            raise PlanError('Only local schema references are supported')
        target = root
        for part in ref[2:].split('/'):
            target = target[part.replace('~1', '/').replace('~0', '~')]
        return validate_schema(value, target, root, path)
    expected = schema.get('type')
    matches = {'object': isinstance(value, dict), 'array': isinstance(value, list),
               'string': isinstance(value, str), 'boolean': type(value) is bool,
               'integer': type(value) is int,
               'number': type(value) in (int, float) and math.isfinite(value)}
    if expected and not matches.get(expected, False):
        raise PlanError(f'{path}: expected {expected}')
    if 'enum' in schema and value not in schema['enum']:
        raise PlanError(f'{path}: expected one of {schema["enum"]}')
    if 'const' in schema and value != schema['const']:
        raise PlanError(f'{path}: expected {schema["const"]!r}')
    if isinstance(value, dict):
        missing = set(schema.get('required', [])) - set(value)
        if missing:
            raise PlanError(f'{path}: missing {sorted(missing)}')
        props = schema.get('properties', {})
        for key, item in value.items():
            if key in props:
                validate_schema(item, props[key], root, path + '.' + key)
            elif schema.get('additionalProperties') is False:
                raise PlanError(f'{path}: unknown field {key}')
            elif isinstance(schema.get('additionalProperties'), dict):
                validate_schema(item, schema['additionalProperties'], root, path + '.' + key)
    elif isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', math.inf):
            raise PlanError(f'{path}: array length outside allowed range')
        for i, item in enumerate(value):
            validate_schema(item, schema.get('items', {}), root, f'{path}[{i}]')
    elif isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', math.inf):
            raise PlanError(f'{path}: string length outside allowed range')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            raise PlanError(f'{path}: invalid identifier')
    elif type(value) in (int, float):
        if not math.isfinite(value):
            raise PlanError(f'{path}: non-finite number')
        if value < schema.get('minimum', -math.inf) or value > schema.get('maximum', math.inf):
            raise PlanError(f'{path}: number outside allowed range')
        if 'exclusiveMinimum' in schema and value <= schema['exclusiveMinimum']:
            raise PlanError(f'{path}: number must exceed {schema["exclusiveMinimum"]}')


def validate_plan(plan):
    validate_schema(plan, read_json(SCHEMA))
    def index(items, label):
        result = {}
        for item in items:
            if item['id'] in result:
                raise PlanError(f'duplicate {label} id: {item["id"]}')
            result[item['id']] = item
        return result
    materials = index(plan['materials'], 'material')
    assets = index(plan['assets'], 'asset')
    objects = index(plan['objects'], 'object')
    lights = index(plan['lights'], 'light')
    cameras = index(plan['cameras'], 'camera')
    if set(objects) & (set(lights) | set(cameras)) or set(lights) & set(cameras):
        raise PlanError('object, light and camera identifiers must be globally unique')
    if plan['hero_camera'] not in cameras:
        raise PlanError('hero_camera does not exist')
    for asset in assets.values():
        for material in asset['materials']:
            if material not in materials:
                raise PlanError(f'{asset["id"]}: unknown material {material}')
        p = asset['parameters']
        if asset['kind'] == 'furniture' and p.get('variant') not in ('table', 'bench', 'crate'):
            raise PlanError('furniture requires variant table, bench or crate')
        if asset['kind'] == 'mechanism' and p.get('variant') not in ('minecart', 'winch'):
            raise PlanError('mechanism requires variant minecart or winch')
        if asset['kind'] not in ('furniture', 'mechanism') and 'variant' in p:
            raise PlanError('variant is only supported for furniture/mechanism')
        if 'segments' in p and asset['kind'] not in ('crystal', 'rock_wall'):
            raise PlanError('segments is only supported for crystal/rock_wall')
        if 'roughness' in p and asset['kind'] not in ('rock', 'rock_wall'):
            raise PlanError('geometric roughness is only supported for rock/rock_wall')
        if 'braces' in p and asset['kind'] != 'timber_frame':
            raise PlanError('braces is only supported for timber_frame')
        if 'bevel' in p and asset['kind'] not in ('beam', 'wall', 'ground', 'furniture', 'mechanism', 'timber_frame'):
            raise PlanError('bevel is unsupported for this builder')
    for obj in objects.values():
        if obj['asset'] not in assets:
            raise PlanError(f'{obj["id"]}: unknown asset')
        support = obj.get('support')
        if support:
            if support not in objects or support == obj['id']:
                raise PlanError(f'{obj["id"]}: invalid support')
            if assets[objects[support]['asset']]['kind'] not in ('ground', 'wall', 'beam', 'furniture'):
                raise PlanError('support must be ground, wall, beam or furniture')
        for exempt in obj.get('allow_overlap_with', []):
            if exempt not in objects or exempt == obj['id']:
                raise PlanError(f'{obj["id"]}: invalid overlap exemption')
        seen = {obj['id']}
        parent = support
        while parent:
            if parent in seen:
                raise PlanError('support cycle')
            seen.add(parent)
            parent = objects[parent].get('support')
        if any(abs(v) > plan['space']['size'][i] * 2 for i, v in enumerate(obj['position'])):
            raise PlanError(f'{obj["id"]}: position implausible for declared space')
    return plan


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preview_cameras(plan):
    """Honor the hero selection even when the planner lists it last."""
    return [plan['hero_camera']]+[c['id'] for c in plan['cameras'] if c['id']!=plan['hero_camera']][:2]


def load_plan(path):
    """Load a plan and, when present, its hash-bound reference dossier."""
    plan = validate_plan(read_json(path))
    if 'research' in plan:
        from reference_scout import validate_plan_research
        validate_plan_research(plan, Path(path).resolve().parent)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
    except (PlanError, ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'INVALID: {exc}\n')
    print(json.dumps({'valid': True, 'scene': plan['id'], 'objects': len(plan['objects']),
                      'assets': len(plan['assets']), 'sha256': digest(args.plan)}, indent=2))


if __name__ == '__main__':
    main()
