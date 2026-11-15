"""Reusable local-space low-poly builders. No scene layouts or brief keywords here.

All builders return editable mesh parts, centered in XY, with base Z=0 and
overall bounds fitted to asset.dimensions. Materials are assigned by substance.
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector


class Parts:
    def __init__(self, asset, materials):
        self.asset = asset
        self.materials = materials
        self.objects = []
        self.bevel = asset['parameters'].get('bevel', 0.008)

    def mesh(self, label, vertices, faces, material=0, bevel=0):
        mesh = bpy.data.meshes.new(self.asset['id'] + '__' + label)
        mesh.from_pydata(vertices, [], faces)
        if mesh.validate(verbose=False):
            raise ValueError('Builder produced invalid mesh: ' + label)
        bm=bmesh.new();bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(mesh);bm.free()
        mesh.update()
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(obj)
        mesh.materials.append(self.materials[material % len(self.materials)])
        if bevel:
            modifier = obj.modifiers.new('edge_wear', 'BEVEL')
            modifier.width = bevel
            modifier.segments = 1
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        self.objects.append(obj)
        return obj

    def box(self, label, center, size, material=0, bevel=None):
        x, y, z = (v / 2 for v in size)
        vertices = [(center[0] + a*x, center[1] + b*y, center[2] + c*z)
                    for a, b, c in ((-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                                    (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1))]
        faces = [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
        edge = self.bevel if bevel is None else bevel
        return self.mesh(label, vertices, faces, material, min(edge, min(size)*0.12))

    def beam(self, label, start, end, thickness, material=0):
        direction = Vector(end) - Vector(start)
        obj = self.box(label, (0,0,0), (thickness, thickness, direction.length), material)
        transform = Matrix.Translation((Vector(start)+Vector(end))/2) @ direction.to_track_quat('Z','Y').to_matrix().to_4x4()
        obj.data.transform(transform)
        return obj

    def cylinder(self, label, center, radius, depth, material=0, axis='Z', vertices=12, top_radius=None):
        upper = radius if top_radius is None else top_radius
        points = []
        for z, r in ((-depth/2, radius),(depth/2, upper)):
            for i in range(vertices):
                angle = i*math.tau/vertices
                points.append((r*math.cos(angle),r*math.sin(angle),z))
        faces = [tuple(reversed(range(vertices))),tuple(range(vertices,2*vertices))]
        faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
        transform = Matrix.Translation(center)
        if axis != 'Z':
            transform @= Vector((1,0,0) if axis == 'X' else (0,1,0)).to_track_quat('Z','Y').to_matrix().to_4x4()
        obj = self.mesh(label, points, faces, material)
        obj.data.transform(transform)
        return obj

    def rock(self, label, center, size, seed, roughness=0.18, material=0):
        rng = random.Random(seed)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        obj = bpy.context.object
        obj.name = self.asset['id'] + '__' + label
        for v in obj.data.vertices:
            v.co *= 1 + rng.uniform(-roughness,roughness)
        mins = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
        spans = [max(v.co[i] for v in obj.data.vertices)-mins[i] for i in range(3)]
        for v in obj.data.vertices:
            for i in range(3):
                v.co[i] = (v.co[i]-mins[i])/spans[i]*size[i] + center[i]-size[i]/2
        obj.data.materials.append(self.materials[material % len(self.materials)])
        self.objects.append(obj)

    def fit(self):
        points = [v.co for o in self.objects for v in o.data.vertices]
        low = [min(v[i] for v in points) for i in range(3)]
        span = [max(v[i] for v in points)-low[i] for i in range(3)]
        dims = self.asset['dimensions']
        for o in self.objects:
            for v in o.data.vertices:
                v.co = Vector(tuple((v.co[i]-low[i])/span[i]*dims[i] - (dims[i]/2 if i<2 else 0) for i in range(3)))
            o.data.update()
            uv=o.data.uv_layers.new(name='ASA_BoxProjection')
            for face in o.data.polygons:
                dominant=max(range(3),key=lambda i:abs(face.normal[i]))
                axes=[i for i in range(3) if i!=dominant]
                for loop_index in face.loop_indices:
                    point=o.data.vertices[o.data.loops[loop_index].vertex_index].co
                    uv.data[loop_index].uv=tuple(point[i]/dims[i]+(.5 if i<2 else 0) for i in axes)
        return self.objects


def structure(p, d, kind):
    x,y,z = d
    if kind in ('ground','wall','beam'):
        p.box(kind, (0,0,z/2), d)
    elif kind == 'timber_frame':
        t = min(x*0.065,z*0.085,y)
        for side in (-1,1):
            xx = side*(x/2-t/2)
            p.box('post_' + str(side), (xx,0,(z-t)/2), (t,y,z-t))
            # Lower iron shoes wrap the foot, with visible bolt heads.
            p.box('shoe_' + str(side),(xx,0,z*0.08),(t*1.05,y*1.04,z*0.16),1)
            p.cylinder('shoe_bolt_' + str(side),(xx,-y*.54,z*.09),t*.11,.025,1,'Y',8)
        p.box('lintel',(0,0,z-t/2),(x,y,t))
        if p.asset['parameters'].get('braces',True):
            for side in (-1,1):
                p.beam('knee_brace_' + str(side),(side*(x/2-t),0,z*.65),(side*x*.27,0,z-t),t*.52)


def rock_wall(p, d):
    x,y,z=d
    params=p.asset['parameters']
    rng=random.Random(params.get('seed',0))
    nx=params.get('segments',8)
    nz=4
    rough=params.get('roughness',.16)
    vertices=[]
    for layer in range(2):
        for j in range(nz+1):
            for i in range(nx+1):
                # Shared grid yields a continuous slab, not intersecting boulders.
                xx=-x/2+x*i/nx
                zz=z*j/nz
                if 0<i<nx and 0<j<nz:
                    xx+=rng.uniform(-.2,.2)*x/nx
                    zz+=rng.uniform(-.2,.2)*z/nz
                if j==nz:
                    # An uneven skyline and battered edges keep natural slabs
                    # from reading as rectangular masonry panels.
                    zz-=z*(.025+.12*(.5+.5*math.sin(i*1.7+params.get('seed',0))))
                if i in (0,nx):
                    xx+=(1 if i==0 else -1)*x*.028*math.sin(j*1.3)**2
                yy=y/2 if layer else -y/2 + rng.uniform(-rough,rough)*y - math.sin(j/nz*math.pi)*y*.22
                vertices.append((xx,yy,zz))
    count=(nx+1)*(nz+1)
    faces=[]
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;c=a+nx+2;e=a+nx+1
            faces.extend([(a,b,c),(a,c,e),(a+count,e+count,c+count,b+count)])
    rim=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
    faces.extend([(a,a+count,b+count,b) for a,b in zip(rim,rim[1:]+rim[:1])])
    p.mesh('faceted_strata',vertices,faces)


def crystal(p,d):
    x,y,z=d
    n=p.asset['parameters'].get('segments',6)
    rng=random.Random(p.asset['parameters'].get('seed',0))
    vertices=[]
    for level, radius in ((0,.78),(z*.73,1)):
        for i in range(n):
            a=math.tau*i/n
            r=radius*(1+rng.uniform(-.09,.09))
            vertices.append((math.cos(a)*x/2*r,math.sin(a)*y/2*r,level))
    vertices.append((x*.10,-y*.05,z))
    faces=[tuple(reversed(range(n)))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    faces += [(i+n,(i+1)%n+n,2*n) for i in range(n)]
    p.mesh('six_sided_growth',vertices,faces)


def furniture(p,d):
    x,y,z=d
    variant=p.asset['parameters']['variant']
    if variant in ('table','bench'):
        top=z*.12
        n=5 if variant=='table' else 3
        for i in range(n):
            p.box('top_plank_'+str(i),(-x/2+x*(i+.5)/n,0,z-top/2),(x/n-.012,y,top))
        for a in (-1,1):
            for b in (-1,1):
                p.box(f'leg_{a}_{b}',(a*x*.39,b*y*.34,(z-top)/2),(x*.10,y*.16,z-top))
        p.box('lower_stretcher',(0,0,z*.22),(x*.82,y*.12,z*.10))
        for a in (-1,1):
            p.box('apron_'+str(a),(0,a*y*.34,z-top-z*.07),(x*.85,y*.09,z*.14))
    else:
        t=min(d)*.08
        p.box('bottom',(0,0,t/2),(x,y,t))
        for a in (-1,1):
            for i in range(4):
                zz=t+(z-t)*(i+.5)/4
                p.box(f'long_board_{a}_{i}',(0,a*(y/2-t/2),zz),(x,t,(z-t)/4-.008))
                p.box(f'end_board_{a}_{i}',(a*(x/2-t/2),0,zz),(t,y-t*2,(z-t)/4-.008))
        for a in (-1,1):
            p.box('strap_'+str(a),(a*x*.3,0,z*.5),(t*.65,y*1.02,z),1)


def minecart(p,d):
    x,y,z=d
    # X is axle direction; Y is travel. A hollow tapered hopper, real rim,
    # chassis, paired axles and four flanged wheels explain the construction.
    r=z*.16
    for axle in (-1,1):
        yy=axle*y*.29
        p.cylinder('axle_'+str(axle),(0,yy,r),r*.16,x*.95,1,'X')
        for side in (-1,1):
            xx=side*x*.43
            p.cylinder(f'wheel_{axle}_{side}',(xx,yy,r),r,x*.09,1,'X',12)
            p.cylinder(f'hub_{axle}_{side}',(xx+side*x*.05,yy,r),r*.35,x*.035,1,'X',8)
    for side in (-1,1):
        p.box('chassis_'+str(side),(side*x*.28,0,r*1.6),(x*.10,y*.90,z*.10),1)
    bottom=z*.37;top=z*.95;t=min(x,y)*.045
    p.box('hopper_floor',(0,0,bottom),(x*.64,y*.73,t),0)
    for side in (-1,1):
        # Sloping double-surface plates: mesh volumes, not closed solid bucket.
        bx=side*x*.32;tx=side*x*.43
        vertices=[]
        for dx in (-t/2,t/2):
            vertices.extend([(bx+dx,-y*.365,bottom),(bx+dx,y*.365,bottom),(tx+dx,y*.46,top),(tx+dx,-y*.46,top)])
        p.mesh('side_plate_'+str(side),vertices,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],0)
        by=side*y*.365;ty=side*y*.46
        vertices=[]
        for dy in (-t/2,t/2):
            vertices.extend([(-x*.32,by+dy,bottom),(x*.32,by+dy,bottom),(x*.43,ty+dy,top),(-x*.43,ty+dy,top)])
        p.mesh('end_plate_'+str(side),vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],0)
        p.box('long_rim_'+str(side),(side*x*.43,0,top),(t*1.5,y*.94,t*1.5),1)
        p.box('end_rim_'+str(side),(0,side*y*.46,top),(x*.88,t*1.5,t*1.5),1)
        for yy in (-.28,.28):
            p.cylinder(f'rivet_{side}_{yy}',(side*x*.446,yy*y,z*.74),t*.30,t,1,'X',8)
    p.beam('tow_loop_stem',(0,-y*.46,z*.30),(0,-y*.55,z*.25),t,1)


def winch(p,d):
    x,y,z=d
    p.box('skid_left',(-x*.35,0,z*.05),(x*.16,y,z*.10))
    p.box('skid_right',(x*.35,0,z*.05),(x*.16,y,z*.10))
    for side in (-1,1):
        p.box('bearing_post_'+str(side),(side*x*.32,0,z*.42),(x*.12,y*.35,z*.75))
        p.cylinder('drum_flange_'+str(side),(side*x*.24,0,z*.65),z*.25,x*.05,1,'X',12)
    p.cylinder('rope_drum',(0,0,z*.65),z*.19,x*.45,0,'X',12)
    p.cylinder('shaft',(0,0,z*.65),z*.06,x*.93,1,'X',12)
    p.beam('crank',(x*.46,0,z*.65),(x*.46,y*.30,z*.85),x*.05,1)
    p.cylinder('handle',(x*.50,y*.30,z*.85),z*.045,x*.16,0,'X',10)
    # Visible drum rings convey wound cable without a dense curve mesh.
    for i in range(9):
        p.cylinder('rope_turn_'+str(i),(-x*.19+i*x*.047,0,z*.65),z*.201,x*.025,2,'X',12)


def build_asset(asset, materials):
    p=Parts(asset,materials)
    d=asset['dimensions']
    kind=asset['kind']
    if kind in ('ground','wall','beam','timber_frame'):
        structure(p,d,kind)
    elif kind=='rock':
        p.rock('weathered_mass',(0,0,d[2]/2),d,asset['parameters'].get('seed',0),asset['parameters'].get('roughness',.18))
    elif kind=='rock_wall':
        rock_wall(p,d)
    elif kind=='crystal':
        crystal(p,d)
    elif kind=='furniture':
        furniture(p,d)
    elif kind=='mechanism':
        (minecart if asset['parameters']['variant']=='minecart' else winch)(p,d)
    else:
        raise ValueError('Unknown builder '+kind)
    return p.fit()


def create_material(spec):
    mat=bpy.data.materials.new(spec['id'])
    # Blender 5.x materials already have nodes; avoid deprecated use_nodes writes.
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    color=(*spec['color'],1)
    mat.diffuse_color=color
    mat.roughness=spec['roughness']
    mat.metallic=spec['metallic']
    bsdf.inputs['Base Color'].default_value=color
    bsdf.inputs['Roughness'].default_value=spec['roughness']
    bsdf.inputs['Metallic'].default_value=spec['metallic']
    bsdf.inputs['Emission Color'].default_value=color
    bsdf.inputs['Emission Strength'].default_value=spec['emission']
    if spec['variation']:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        coords=nodes.new('ShaderNodeTexCoord')
        scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY'
        scale.inputs[1].default_value=(3,3,35) if spec['surface']=='wood' else (4,4,4)
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3
        bump=nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=spec['variation']
        bump.inputs['Distance'].default_value=.035 if spec['surface']=='stone' else .012
        links.new(coords.outputs['Generated'],scale.inputs[0]);links.new(scale.outputs['Vector'],noise.inputs['Vector'])
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    mat['asa_surface']=spec['surface']
    mat['asa_export_note']='GLB uses portable PBR factors; procedural bump is Blender-only.'
    return mat
