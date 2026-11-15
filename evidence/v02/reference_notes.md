# References and API decisions

Structural references support construction, not the fantasy palette or exact
historical reconstruction. No external photo is embedded in the generated
models, textures or committed evidence.

- [Universalmuseum Joanneum, CoSA mine exhibit](https://www.museum-joanneum.at/presse/pressetermine/event/cosa-escape),
  [source image](https://www.museum-joanneum.at/fileadmin/user_upload/PRESSE/19_CoSA/Dauerausstellung/Escape_Room/Schaubergwerk_02.jpg).
  Downloaded and opened locally during refinement on 2026-11-15. Observed thick
  posts carrying a transverse lintel, overhead members supported at joints,
  narrow paired rails and a boarded cart with straps/fasteners. These informed
  construction checks; the generated cart is a stylized metal hopper, not a
  copy. Image reuse rights were not assumed; the downloaded photo is excluded
  from the PR. The first build preceded the successful full-image retrieval.
- [Monte Amiata mine museum](https://www.parcoamiata.com/miniere-monte-amiata/abbadia-san-salvatore-miniera/):
  search located an additional tunnel image, but direct download failed; no
  detailed visual inspection of that photo is claimed.

Official Blender sources consulted before adopting/refining relevant API use:

- [Blender 5.3 BMesh operators](https://docs.blender.org/api/5.3/bmesh.ops.html):
  `recalc_face_normals` for closed generated mesh parts. Blender contract tests
  independently verify manifold edges and positive signed volume.
- [Mesh / from_pydata](https://docs.blender.org/api/current/bpy.types.Mesh.html?highlight=transform):
  vertices/edges/faces and validation; generated meshes run `Mesh.validate`.
- [glTF export operator](https://docs.blender.org/api/main/bpy.ops.export_scene.html):
  GLB format, apply, cameras/lights/extras options; exercised in Blender 5.3.0.
- [glTF material and light limitations](https://docs.blender.org/manual/en/5.3/addons/scene_gltf2.html):
  Blender area/world lights are omitted; procedural bump is not a portable glTF
  material graph. Export verification uses explicit diagnostic relighting and
  compares portable PBR values separately from Blender-only surface effects.

Some direct documentation-page fetches returned an upstream 402 error; official
indexed API/manual excerpts were available and were used, followed by local
runtime introspection/execution. No unsupported API was silently assumed to pass.
