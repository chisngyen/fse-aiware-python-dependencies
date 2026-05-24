"""Title intro — Blender 3D background for slide 1 (0:00–0:30).

A camera glides over a "ruined Python ecosystem": tilted broken cubes labelled
with old package names (scipy 0.x, numpy 1.0, cv2 ...), then craned up to
reveal floating clean text "MEMRES & CGAR" hovering above the wreckage.

The Manim Title scene composites on top — so this is just the 3D backdrop.

Run via Blender MCP execute_blender_code OR
    blender -b -P 01_title_intro.py -o ../renders/01_title/frame_####.png -F PNG -x 1 -a
"""
import bpy
import math
import random

NAVY    = (0.137, 0.216, 0.231, 1.0)
ACCENT  = (0.922, 0.506, 0.106, 1.0)
SOFTGRAY= (0.949, 0.957, 0.969, 1.0)
INK     = (0.102, 0.102, 0.102, 1.0)

WRECKAGE = [
    "scipy 0.19",  "numpy 1.0",   "cv2 2.4",    "sklearn 0.17",
    "tensorflow 0.12", "keras 1.2", "theano 0.9", "PIL 1.1",
    "py2.7", "py3.4", "PyV8", "appscript",
]

random.seed(42)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for c in (bpy.data.materials, bpy.data.meshes,
              bpy.data.cameras, bpy.data.lights):
        for b in list(c):
            c.remove(b)


def mat(name, rgba, emission=0.0, roughness=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    if emission > 0:
        for slot in ("Emission Color", "Emission"):
            if slot in bsdf.inputs:
                bsdf.inputs[slot].default_value = rgba
                break
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return m


def add_wreck():
    for i, label in enumerate(WRECKAGE):
        x = random.uniform(-8, 8)
        y = random.uniform(-5, 5)
        z = random.uniform(-0.3, 0.6)
        bpy.ops.mesh.primitive_cube_add(size=1.2, location=(x, y, z))
        cube = bpy.context.object
        cube.rotation_euler = (
            random.uniform(-0.5, 0.5),
            random.uniform(-0.5, 0.5),
            random.uniform(0, math.pi),
        )
        col = NAVY if i % 2 == 0 else (0.25, 0.30, 0.32, 1.0)
        cube.data.materials.append(mat(f"wreck_{i}", col, roughness=0.85))

        bpy.ops.object.text_add(location=(x, y, z + 0.85))
        t = bpy.context.object
        t.data.body = label
        t.data.size = 0.32
        t.data.extrude = 0.02
        t.data.align_x = "CENTER"
        t.rotation_euler = cube.rotation_euler
        t.data.materials.append(mat(f"wreck_t_{i}", SOFTGRAY))


def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -1))
    g = bpy.context.object
    g.data.materials.append(mat("ground", (0.15, 0.16, 0.18, 1.0), roughness=0.95))


def add_hero_text():
    bpy.ops.object.text_add(location=(0, 0, 4))
    t = bpy.context.object
    t.data.body = "MEMRES & CGAR"
    t.data.size = 1.6
    t.data.extrude = 0.12
    t.data.align_x = "CENTER"
    t.rotation_euler = (math.pi / 2, 0, 0)
    t.data.materials.append(mat("hero", ACCENT, emission=1.5))


def add_camera():
    bpy.ops.object.camera_add(location=(0, -14, 1.2))
    cam = bpy.context.object
    cam.data.lens = 35
    # animate crane-up
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 180  # 6 sec @ 30fps; loop or hold last frame
    cam.location = (0, -14, 0.6)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.keyframe_insert("location", frame=1)
    cam.keyframe_insert("rotation_euler", frame=1)
    cam.location = (0, -10, 5)
    cam.rotation_euler = (math.pi / 2.4, 0, 0)
    cam.keyframe_insert("location", frame=180)
    cam.keyframe_insert("rotation_euler", frame=180)
    bpy.context.scene.camera = cam


def add_lights():
    bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
    s = bpy.context.object
    s.data.energy = 3.0
    s.data.angle = math.radians(20)


def build():
    clear_scene()
    add_ground()
    add_wreck()
    add_hero_text()
    add_camera()
    add_lights()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 30
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.10, 0.12, 1)
    print("[blender] title intro built")


if __name__ == "__main__":
    build()
