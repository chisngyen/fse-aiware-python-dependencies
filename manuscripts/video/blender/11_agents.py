"""CGAR 4-Agent Architecture — Blender hero shot for slide 11.

Run modes
---------
(A) Via Blender MCP — paste this whole file into ``mcp__blender__execute_blender_code``
    after starting the Blender addon. Good for iteration.

(B) Headless render::

        blender -b -P 11_agents.py -- --frames 1-240 --out ../renders/11_agents/

Scene design
------------
4 stylized "agent" capsules orbiting a glowing central Session Store (a torus
of constraint tokens). Each agent holds a small floating tool icon (a labeled
plane). Camera does a slow 360° dolly.

Color palette mirrors the Manim scenes (navy / orange / red / green) so the
two pipelines composite seamlessly.
"""
import bpy
import bmesh
import math
from mathutils import Vector

# ============================================================
# Palette
# ============================================================
NAVY    = (0.137, 0.216, 0.231, 1.0)   # #23373B
ACCENT  = (0.922, 0.506, 0.106, 1.0)   # #EB811B
ALERT   = (0.776, 0.157, 0.157, 1.0)   # #C62828
SUCCESS = (0.180, 0.490, 0.196, 1.0)   # #2E7D32
SOFTGRAY= (0.949, 0.957, 0.969, 1.0)   # #F2F4F7
INK     = (0.102, 0.102, 0.102, 1.0)

AGENTS = [
    ("Planner",        NAVY,    ["query_pypi", "wheel_filter"]),
    ("Executor",       ACCENT,  ["build_docker", "run_import"]),
    ("Error Analyzer", ALERT,   ["parse_error", "gen_constraint"]),
    ("Critic",         SUCCESS, ["analyze_failures"]),
]


# ============================================================
# Helpers
# ============================================================
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.materials):
        bpy.data.materials.remove(block)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.cameras):
        bpy.data.cameras.remove(block)
    for block in list(bpy.data.lights):
        bpy.data.lights.remove(block)


def make_material(name, rgba, emission=0.0, roughness=0.4, metallic=0.1):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission > 0:
        # Slot name moved across Blender versions — try both.
        for slot in ("Emission Color", "Emission"):
            if slot in bsdf.inputs:
                bsdf.inputs[slot].default_value = rgba
                break
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def add_capsule(name, location, color, height=2.0, radius=0.55):
    """Build a stylized agent body: cylinder + top sphere."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height,
                                        location=location)
    body = bpy.context.object
    body.name = f"{name}_body"
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius * 1.05,
        location=(location[0], location[1], location[2] + height / 2),
    )
    head = bpy.context.object
    head.name = f"{name}_head"

    mat = make_material(f"mat_{name}", color, emission=0.4, roughness=0.35)
    body.data.materials.append(mat)
    head.data.materials.append(mat)

    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True); head.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = f"agent_{name}"
    return body


def add_text(name, body, location, color=INK, size=0.35,
             extrude=0.02, rotation=(math.pi / 2, 0, 0)):
    bpy.ops.object.text_add(location=location, rotation=rotation)
    txt = bpy.context.object
    txt.name = name
    txt.data.body = body
    txt.data.size = size
    txt.data.extrude = extrude
    txt.data.align_x = "CENTER"
    txt.data.align_y = "CENTER"
    mat = make_material(f"mat_{name}", (*color[:3], 1.0))
    txt.data.materials.append(mat)
    return txt


def add_tool_chip(name, label, location, color):
    """A small floating rounded plane with a tool name."""
    bpy.ops.mesh.primitive_plane_add(size=1.2, location=location)
    chip = bpy.context.object
    chip.name = f"tool_{name}"
    chip.scale = (1.0, 0.35, 1.0)
    mat = make_material(f"mat_chip_{name}", color, emission=0.6)
    chip.data.materials.append(mat)
    add_text(f"tooltxt_{name}", label,
             (location[0], location[1] - 0.06, location[2]),
             color=SOFTGRAY, size=0.16)
    return chip


def add_session_store(location):
    """Glowing torus = the shared constraint store."""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.9, minor_radius=0.22, location=location,
    )
    torus = bpy.context.object
    torus.name = "session_store"
    mat = make_material("mat_store", ACCENT, emission=2.5, roughness=0.2)
    torus.data.materials.append(mat)

    # Floating constraint tokens around the torus.
    for i, label in enumerate(["scipy<1.2", "py<=3.7", "wheel-only"]):
        angle = i * (2 * math.pi / 3)
        x = location[0] + 1.4 * math.cos(angle)
        y = location[1] + 1.4 * math.sin(angle)
        z = location[2] + 0.05
        bpy.ops.mesh.primitive_cube_add(size=0.35, location=(x, y, z))
        cube = bpy.context.object
        cube.name = f"token_{i}"
        m = make_material(f"mat_token_{i}", NAVY, emission=1.0)
        cube.data.materials.append(m)
        add_text(f"tokentxt_{i}", label, (x, y - 0.18, z + 0.05),
                 color=SOFTGRAY, size=0.1)
    return torus


def add_ground():
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -1.2))
    g = bpy.context.object
    g.name = "ground"
    mat = make_material("mat_ground", SOFTGRAY, roughness=0.9)
    g.data.materials.append(mat)


def add_camera_and_track(target):
    bpy.ops.object.camera_add(location=(8, -8, 4.5))
    cam = bpy.context.object
    cam.name = "main_cam"
    cam.data.lens = 50
    # Track-to target
    cons = cam.constraints.new(type="TRACK_TO")
    cons.target = target
    cons.track_axis = "TRACK_NEGATIVE_Z"
    cons.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam


def add_lights():
    bpy.ops.object.light_add(type="AREA", location=(5, -5, 8))
    key = bpy.context.object
    key.data.energy = 800
    key.data.size = 5
    bpy.ops.object.light_add(type="AREA", location=(-6, 3, 6))
    fill = bpy.context.object
    fill.data.energy = 250
    fill.data.size = 6
    fill.data.color = (0.85, 0.9, 1.0)


def orbit_camera(cam, target_loc, n_frames=240, radius=10, height=4.5):
    """Keyframe a slow 360° orbit around target."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = n_frames
    for f in range(1, n_frames + 1):
        t = (f - 1) / (n_frames - 1)
        angle = t * 2 * math.pi
        cam.location = (
            target_loc[0] + radius * math.cos(angle),
            target_loc[1] + radius * math.sin(angle),
            target_loc[2] + height,
        )
        cam.keyframe_insert(data_path="location", frame=f)


# ============================================================
# Build scene
# ============================================================
def build():
    clear_scene()
    add_ground()

    store = add_session_store((0, 0, 0.5))
    add_text("store_label", "Session Store",
             (0, 0, 1.4), color=INK, size=0.28,
             rotation=(0, 0, 0))

    radius = 4.0
    for i, (name, color, tools) in enumerate(AGENTS):
        angle = i * (math.pi / 2) + math.pi / 4
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        body = add_capsule(name, (x, y, 0), color)
        add_text(f"label_{name}", name, (x, y - 0.7, 2.6),
                 color=INK, size=0.32, rotation=(math.pi / 2, 0, -angle))
        for j, tool in enumerate(tools):
            tx = x + 0.9 * math.cos(angle)
            ty = y + 0.9 * math.sin(angle)
            tz = 1.4 + j * 0.55
            add_tool_chip(f"{name}_{j}", tool, (tx, ty, tz), color)

    cam = add_camera_and_track(store)
    add_lights()
    orbit_camera(cam, (0, 0, 0.5), n_frames=240, radius=10, height=4.5)

    # Render settings
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "HIGH"
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*SOFTGRAY[:3], 1.0)
    bg.inputs[1].default_value = 1.0

    print("[blender] scene built — 4 agents + session store + orbit cam")


if __name__ == "__main__":
    build()
