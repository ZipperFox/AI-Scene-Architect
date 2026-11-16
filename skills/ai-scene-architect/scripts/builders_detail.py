"""Small visual-quality extensions: continuous rock shell and crafted architecture.

No scene placements live here; existing v0.2 builders retain their old defaults.
"""
import math
import random
import bpy


def cave_shell(p,d):
    x,y,z=d
    rng=random.Random(p.asset['parameters'].get('seed',37))
    n=p.asset['parameters'].get('segments',22)
    levels=[(0,1),(.22,1.04),(.53,1),(.80,.94),(1,.77)]
    vertices=[]
    # Shared vertices connect curved walls and inward shoulder. Front and roof
    # remain an intentional cutaway, rather than three slabs and a floating lid.
    for outer in (False,True):
        for j,(height,radius) in enumerate(levels):
            for i in range(n+1):
                a=math.radians(-25+230*i/n)
                jitter=rng.uniform(-.035,.035) if j else 0
                r=radius+jitter+(.15 if outer else 0)
                # Lower side cuts preserve the crystal/furniture sightlines;
                # the rear remains tall, with an inward rock shoulder.
                zz=z*height*(.22+.78*max(0,math.sin(a))**4)
                if j==len(levels)-1:zz*=.92+.07*math.sin(i*1.9)**2
                vertices.append((x*.43*r*math.cos(a),y*.78*r*math.sin(a)-y*.30,zz))
    rows=len(levels);count=rows*(n+1);faces=[]
    for j in range(rows-1):
        for i in range(n):
            a=j*(n+1)+i;b=a+1;c=a+n+2;e=a+n+1
            faces.extend([(a,b,c),(a,c,e),(a+count,e+count,c+count),(a+count,c+count,b+count)])
    rim=list(range(n+1))+[j*(n+1)+n for j in range(1,rows)]+[(rows-1)*(n+1)+i for i in range(n-1,-1,-1)]+[j*(n+1) for j in range(rows-2,0,-1)]
    faces.extend([(a,a+count,b+count,b) for a,b in zip(rim,rim[1:]+rim[:1])])
    obj=p.mesh('continuous_cutaway_rock',vertices,faces)
    for mat in p.materials[1:]:obj.data.materials.append(mat)
    for face in obj.data.polygons:
        # Broad geological bands, not independent random colors per triangle.
        center=face.center.z/z
        face.material_index=min(len(p.materials)-1,int(center*len(p.materials)))


def platform(p,d):
    x,y,z=d
    outline=[(-.50,-.34),(-.40,-.50),(.31,-.50),(.50,-.35),(.50,.30),(.32,.50),(-.36,.50),(-.50,.27)]
    vertices=[(a*x,b*y,h) for h in (0,z) for a,b in outline]
    n=len(outline)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    p.mesh('cut_stone_plinth',vertices,faces)


def window_wall(p,d):
    x,y,z=d
    opening=x*.54;bottom=z*.36;top=z*.85
    wall=y*.45;t=min(.09,x*.02)
    side=(x-opening)/2
    for s in (-1,1):p.box('plaster_pier_'+str(s),(s*(opening/2+side/2),0,z/2),(side,wall,z),0,0)
    p.box('plaster_sill',(0,0,bottom/2),(opening,wall,bottom),0,0)
    p.box('plaster_header',(0,0,(top+z)/2),(opening,wall,z-top),0,0)
    for s in (-1,1):
        p.box('window_jamb_'+str(s),(s*(opening/2-t/2),0,(bottom+top)/2),(t,wall*1.05,top-bottom),1)
    for zz in (bottom,top):p.box('window_rail_'+str(zz),(0,0,zz),(opening,wall*1.05,t),1)
    for xx in (-opening/6,opening/6):p.box('window_mullion_'+str(xx),(xx,0,(bottom+top)/2),(t*.55,wall*.7,top-bottom),1)
    p.box('window_crossbar',(0,0,(bottom+top)/2),(opening,wall*.7,t*.55),1)
    p.box('projecting_sill',(0,-y*.15,bottom),(opening+.16,y,.065),1)
    # Deliberately open glazing: real light aperture, not an emissive rectangle.


def workbench(p,d):
    x,y,z=d;top=z*.15;thick=min(x*.055,y*.16)
    for i in range(3):
        if i==0:
            # Explicit shared-vertex cells keep square dog holes clean without
            # Boolean-created sliver polygons or coincident internal faces.
            centers=[x*(-.32+k*.16) for k in range(5)];half=.019
            xs=sorted([-x/2,x/2]+[c+s*half for c in centers for s in (-1,1)])
            ys=[-y/2+.004,-y*.32-half,-y*.32+half,-y/6-.004]
            cells={(u,v) for u in range(len(xs)-1) for v in range(3)
                   if not(v==1 and any(abs((xs[u]+xs[u+1])/2-c)<half for c in centers))}
            vertices=[];lookup={};faces=[]
            def vertex(u,v,h):
                key=(u,v,h)
                if key not in lookup:
                    lookup[key]=len(vertices);vertices.append((xs[u],ys[v],z-top+h*top))
                return lookup[key]
            for u,v in sorted(cells):
                for h in (0,1):faces.append(tuple(vertex(a,b,h) for a,b in [(u,v),(u+1,v),(u+1,v+1),(u,v+1)]))
                for du,dv,ends in [(-1,0,[(u,v),(u,v+1)]),(1,0,[(u+1,v+1),(u+1,v)]),(0,-1,[(u+1,v),(u,v)]),(0,1,[(u,v+1),(u+1,v+1)])]:
                    if (u+du,v+dv) not in cells:
                        faces.append((vertex(*ends[0],0),vertex(*ends[1],0),vertex(*ends[1],1),vertex(*ends[0],1)))
            p.mesh('longgrain_top_dogholes',vertices,faces,0)
        else:p.box('longgrain_top_'+str(i),(0,-y/2+y*(i+.5)/3,z-top/2),(x,y/3-.008,top),0)
    for a in (-1,1):
        for b in (-1,1):p.box(f'heavy_leg_{a}_{b}',(a*x*.38,b*y*.33,(z-top)/2),(thick,thick,z-top),0)
        p.box('end_stretcher_'+str(a),(a*x*.38,0,z*.25),(thick*.7,y*.8,thick*.7),0)
    p.box('long_stretcher',(0,y*.23,z*.25),(x*.78,thick*.55,thick*.7),0)
    p.box('front_apron',(0,-y*.37,z-top-top*.45),(x*.84,thick*.65,top*.9),0)
    # A fitted vise: fixed apron, moving jaw, screw, cross-handle.
    p.box('vise_jaw',(-x*.25,-y*.58,z-top),(x*.19,y*.11,top*1.3),0)
    p.cylinder('vise_screw',(-x*.25,-y*.54,z-top),.023,y*.35,1,'Y',12)
    p.cylinder('vise_hub',(-x*.25,-y*.69,z-top),.04,.055,1,'Y',12)
    p.cylinder('vise_handle',(-x*.25,-y*.72,z-top),.016,.24,0,'Z',10)
    # Two purposeful, separately editable work objects, not random tabletop clutter.
    p.box('workpiece',(x*.16,y*.07,z+.018),(x*.35,y*.30,.036),2)
    p.box('plane_body',(x*.22,y*.07,z+.075),(.23,.095,.075),0)
    p.box('plane_iron',(x*.22,y*.07,z+.116),(.035,.085,.012),1)
    p.cylinder('plane_front_knob',(x*.30,y*.07,z+.13),.024,.055,0)
    p.box('plane_rear_grip',(x*.15,y*.07,z+.14),(.035,.06,.07),0)


def tool_rack(p,d):
    x,y,z=d
    p.box('backboard',(0,y*.3,z*.5),(x,y*.25,z),0)
    p.box('hanging_rail',(0,0,z*.75),(x,y*.5,z*.08),0)
    for i,ratio in enumerate((.48,.60,.43,.55)):
        xx=x*(-.35+i*.23)
        p.cylinder('handle_'+str(i),(xx,-y*.35,z*.72),x*.027,z*.17,0,'Z',10)
        p.box('steel_blade_'+str(i),(xx,-y*.35,z*(.72-ratio/2)),(x*.025,y*.12,z*(ratio-.12)),1,.002)
    p.box('lower_rail',(0,0,z*.14),(x,y*.45,z*.055),0)


BUILDERS={'cave_shell':cave_shell,'platform':platform,'window_wall':window_wall}
