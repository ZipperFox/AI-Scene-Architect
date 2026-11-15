"""Render non-destructive Blender previews from multiple cameras.

Run inside Blender:
  blender --background scene.blend --python render_previews.py -- --output previews/iteration-0

The source .blend is never saved. Preview output paths must be new per iteration.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


VIEWS = ("hero", "three_quarter", "top")


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="New directory for PNGs and a manifest")
    parser.add_argument("--resolution", type=int, default=512, help="Square preview size (128–2048)")
    parser.add_argument("--samples", type=int, default=16, help="Cycles sample cap (1–256)")
    parser.add_argument("--engine", choices=("scene", "cycles-cpu"), default="scene",
                        help="Use scene renderer or headless-friendly Cycles CPU")
    parser.add_argument("--camera-names", nargs=3, metavar=("HERO", "SECONDARY", "OVERVIEW"),
                        help="Optional three authored camera objects; retains v0.1 defaults when omitted")
    args = parser.parse_args(argv)
    if not 128 <= args.resolution <= 2048:
        parser.error("--resolution must be 128–2048")
    if not 1 <= args.samples <= 256:
        parser.error("--samples must be 1–256")
    return args


def get_bounds(scene):
    points = []
    for obj in scene.objects:
        if obj.type not in {"MESH", "CURVE", "SURFACE", "FONT", "META"} or obj.hide_render:
            continue
        for corner in obj.bound_box:
            point = obj.matrix_world @ Vector(corner)
            if all(math.isfinite(v) for v in point):
                points.append(point)
    if not points:
        raise RuntimeError("Scene has no renderable geometry; refusing meaningless previews")
    minimum = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    maximum = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    center = (minimum + maximum) / 2
    radius = max((maximum - minimum).length / 2, 0.5)
    return center, radius


def look_at(camera, target):
    direction = Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def create_camera(scene, name, position, target, radius, orthographic=False):
    data = bpy.data.cameras.new("ASA_Preview_" + name)
    camera = bpy.data.objects.new("ASA_Preview_" + name, data)
    scene.collection.objects.link(camera)
    camera.location = position
    look_at(camera, target)
    data.clip_end = max(1000.0, radius * 15)
    if orthographic:
        data.type = "ORTHO"
        data.ortho_scale = radius * 2.7
    else:
        data.type = "PERSP"
        data.lens = 35
    return camera


def add_preview_lighting(scene, center, radius):
    if any(obj.type == "LIGHT" and not obj.hide_render for obj in scene.objects):
        return False
    # Temporary lights exist only in memory; original scene and files are untouched.
    for name, offset, energy, size in (
        ("key", (1.2, -1.8, 2.5), 850, 2.5),
        ("fill", (-1.5, -0.3, 1.5), 350, 3.5),
    ):
        data = bpy.data.lights.new("ASA_Preview_" + name, "AREA")
        data.energy = energy * max(radius / 3, 0.3) ** 2
        data.shape = "DISK"
        data.size = size * max(radius / 3, 0.3)
        light = bpy.data.objects.new("ASA_Preview_" + name, data)
        scene.collection.objects.link(light)
        light.location = center + radius * Vector(offset)
        look_at(light, center)
    return True


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    args = arguments()
    authored_cameras = None
    if args.camera_names:
        authored_cameras = [bpy.context.scene.objects.get(name) for name in args.camera_names]
        if any(camera is None or camera.type != "CAMERA" for camera in authored_cameras):
            raise RuntimeError("All --camera-names must identify existing scene cameras")
        if len(set(args.camera_names)) != 3:
            raise RuntimeError("Three distinct authored cameras are required")
    target = Path(args.output).expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise RuntimeError("Preview directory is not empty; use a new directory for each iteration: " + str(target))
    target.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    center, radius = get_bounds(scene)
    temporary_lighting = add_preview_lighting(scene, center, radius)
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if args.engine == "cycles-cpu":
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        # Some minimal Blender builds omit OpenImageDenoise entirely.
        for layer in scene.view_layers:
            if hasattr(layer, "cycles") and hasattr(layer.cycles, "use_denoising"):
                layer.cycles.use_denoising = False
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = args.samples

    old_camera = scene.camera
    cameras = dict(zip(VIEWS, authored_cameras)) if authored_cameras else {
        "hero": old_camera if old_camera else create_camera(
            scene, "hero", center + radius * Vector((1.6, -3.0, 1.6)), center, radius
        ),
        "three_quarter": create_camera(
            scene, "three_quarter", center + radius * Vector((-2.1, -2.6, 1.9)), center, radius
        ),
        "top": create_camera(
            scene, "top", center + radius * Vector((0.01, 0.01, 3.5)), center, radius, orthographic=True
        ),
    }

    manifest = {
        "blender_version": bpy.app.version_string,
        "source_blend": bpy.data.filepath,
        "engine": scene.render.engine,
        "resolution": args.resolution,
        "temporary_lighting_added": temporary_lighting,
        "viewpoints": {},
    }
    for name in VIEWS:
        camera = cameras[name]
        scene.camera = camera
        destination = target / (name + ".png")
        scene.render.filepath = str(destination)
        bpy.ops.render.render(write_still=True)
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError("Rendering failed: " + str(destination))
        manifest["viewpoints"][name] = {
            "path": str(destination),
            "sha256": sha256(destination),
            "camera": camera.name,
            "location": [round(v, 5) for v in camera.location],
        }
    scene.camera = old_camera
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("ASA_PREVIEW_MANIFEST=" + str(target / "manifest.json"))


if __name__ == "__main__":
    main()
