"""Make a disposable Blender scene for verifying the preview renderer."""

import argparse
import sys

import bpy


def main():
    args_list = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(args_list)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.9))
    bpy.context.object.name = "Stone pedestal"
    material = bpy.data.materials.new("Warm stone")
    material.diffuse_color = (0.5, 0.34, 0.22, 1)
    material.use_nodes = True
    material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.5, 0.34, 0.22, 1)
    bpy.context.object.data.materials.append(material)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.8, location=(0.0, 0, 2.25))
    bpy.context.object.name = "Low poly crystal proxy"
    material2 = bpy.data.materials.new("Cyan crystal")
    material2.diffuse_color = (0.04, 0.7, 0.72, 1)
    material2.use_nodes = True
    material2.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.04, 0.7, 0.72, 1)
    bpy.context.object.data.materials.append(material2)

    bpy.ops.wm.save_as_mainfile(filepath=args.output)


if __name__ == "__main__":
    main()
