# Fix Jack's remeshed duct cutter (iteration 3) while keeping its path and rounded shape.
import bpy, bmesh, os
W = r"C:\Users\derpy\Documents\cfd_blender"
def nm_count(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); n = sum(1 for e in bm.edges if not e.is_manifold); bm.free(); return n
def apply_bool(target, cutter, op):
    mod = target.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.solver = 'EXACT'; mod.object = cutter
    bpy.context.view_layer.objects.active = target; bpy.ops.object.modifier_apply(modifier=mod.name)
def dup(ob, name, dz):
    c = ob.copy(); c.data = ob.data.copy(); c.name = name; c.location.z += dz; bpy.context.collection.objects.link(c)
    bpy.context.view_layer.objects.active = c; c.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); c.select_set(False); return c
def box(name, x0, x1, ya, yb, z0, z1):
    pts = [(x0,ya,z0),(x1,ya,z0),(x1,yb,z0),(x0,yb,z0),(x0,ya,z1),(x1,ya,z1),(x1,yb,z1),(x0,yb,z1)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    me = bpy.data.meshes.new(name); me.from_pydata(pts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

jack_cut = bpy.data.objects["Cube"]; jack_cut.name = "jack_cutter_original"
old_car = bpy.data.objects["f499p"]; old_car.name = "f499p_jack3_broken"
bpy.ops.object.select_all(action='DESELECT')
# 1. cutter: Jack's tube lowered 2 cm off the bonnet skin, thickened downward with copies 2.5 and 5 cm lower
cut = dup(jack_cut, "cutter_fixed", -0.020)
for i, dz in enumerate((-0.030, -0.040, -0.050, -0.060, -0.070)):     # 1 cm steps: only shallow grooves
    c = dup(jack_cut, f"cutter_step_{i}", dz); apply_bool(cut, c, 'UNION'); c.hide_set(True)
# melt the stack into one smooth, thick tube (cutter only; the car is never remeshed)
rm = cut.modifiers.new("remesh", 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = 0.006; rm.adaptivity = 0.0
bpy.context.view_layer.objects.active = cut; bpy.ops.object.modifier_apply(modifier=rm.name)
sm = cut.modifiers.new("smooth", 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
bpy.ops.object.modifier_apply(modifier=sm.name)
print(f"TUBE faces {len(cut.data.polygons)} non-manifold {nm_count(cut)}")
# 2. exit risers inside each vent recess (x 0.70-0.95, |y| 0.29-0.44), from inside the tube's top end to open air
for s in (1, -1):
    ya, yb = sorted((s*0.300, s*0.425))
    r = box(f"riser_{'L' if s>0 else 'R'}", 0.72, 0.90, ya, yb, 0.43, 0.66); apply_bool(cut, r, 'UNION'); r.hide_set(True)
print(f"CUTTER faces {len(cut.data.polygons)} non-manifold {nm_count(cut)}")
# 3. fresh v2 car and the cut
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.stl_import(filepath=os.path.join(W, "f499p_v2.stl")); car = bpy.context.selected_objects[0]; car.name = "f499p"
bpy.context.view_layer.objects.active = car
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=1e-6); bpy.ops.object.mode_set(mode='OBJECT')
apply_bool(car, cut, 'DIFFERENCE')
bpy.context.view_layer.objects.active = car
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-6); bpy.ops.mesh.dissolve_degenerate(threshold=1e-6); bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new(); bm.from_mesh(car.data)
nm = sum(1 for e in bm.edges if not e.is_manifold); deg = sum(1 for f in bm.faces if f.calc_area() < 1e-12); bm.free()
print(f"RESULT faces {len(car.data.polygons)} non-manifold {nm} zero-area {deg}")
for ob in (jack_cut, old_car, cut): ob.hide_set(True)
bpy.ops.object.select_all(action='DESELECT'); car.hide_set(False); car.select_set(True); bpy.context.view_layer.objects.active = car
bpy.ops.wm.stl_export(filepath=os.path.join(W, "jack3", "499p_v3_jack3_fixed.stl"), export_selected_objects=True, ascii_format=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, "jack3", "499p_v3_jack3_fixed.blend"))
print("SAVED")
