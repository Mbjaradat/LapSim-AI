"""Original Blender primitives, camera and lighting for a dry training box."""

import math
import bpy
from mathutils import Vector
from config import (
    TROCARS, SHAFT_LENGTH, SHAFT_RADIUS, JAW_LENGTH, CAMERA_POSITION,
    CAMERA_TARGET, CAMERA_LENS_MM, CAMERA_SENSOR_MM, RESOLUTION, FPS,
    FRAME_START, FRAME_END, LIGHTS,
)
from mechanics import create_rig, empty


def material(name, color, metallic=0, roughness=.4, emission=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Emission Color"].default_value = (*color, 1)
    bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def cube(name, location, dimensions, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = location
    obj.scale = dimensions
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Soft edges", "BEVEL")
    bevel.width = .06
    bevel.segments = 3
    return obj


def cylinder(name, location, radius, depth, mat, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = location
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def ring(name, location, radius, thickness, mat, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=thickness,
                                   major_segments=48, minor_segments=12)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = location
    obj.data.materials.append(mat)
    return obj


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def build_scene():
    # Factory reset makes object naming and geometry independent of prior files.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.seed = 0
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = RESOLUTION
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = FRAME_START, FRAME_END
    world = bpy.data.worlds.new("Dark environment")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (.025, .035, .05, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = .25
    scene.world = world
    dark = material("Cavity charcoal", (.018, .027, .038), roughness=.7)
    grid = material("Grid muted blue", (.045, .10, .13), emission=.25)
    metal = material("Shaft brushed steel", (.48, .58, .65), metallic=.8, roughness=.25)
    colors = {"LEFT": material("Left cyan", (.02, .65, .9), metallic=.2, emission=.35),
              "RIGHT": material("Right amber", (1, .35, .04), metallic=.2, emission=.35)}
    cube("WORKSPACE_FLOOR", (0, .02, -.205), (.62, .55, .012), dark)
    cube("WORKSPACE_BACK", (0, .295, -.03), (.62, .012, .36), dark)
    for x in (-.31, .31):
        cube("WORKSPACE_SIDE", (x, .02, -.03), (.012, .55, .36), dark)
    for index in range(-5, 6):
        cube(f"GRID_X_{index}", (index * .05, .02, -.1985), (.0007, .5, .0005), grid)
        cube(f"GRID_Y_{index}", (0, .02 + index * .05, -.1985), (.55, .0007, .0005), grid)
    for side, pivot in TROCARS.items():
        mat = colors[side]
        marker = empty(f"{side}_TROCAR", location=pivot)
        marker.lock_location = marker.lock_rotation = marker.lock_scale = (True,) * 3
        ring(f"{side}_PIVOT_RING", (0, 0, 0), .014, .0025, mat, marker)
        # Crosshair stays fixed while the shaft swings through its centre.
        for axis in (0, 1):
            dims = [.001, .001, .001]
            dims[axis] = .042
            cube(f"{side}_PIVOT_CROSS_{axis}", (0, 0, 0), dims, mat, marker)
        root, axial = create_rig(side)
        cylinder(f"{side}_SHAFT", (0, 0, SHAFT_LENGTH / 2), SHAFT_RADIUS,
                 SHAFT_LENGTH, metal, axial)
        # Asymmetric stripe and jaws make axial roll visible.
        cube(f"{side}_ROLL_STRIPE", (SHAFT_RADIUS, 0, SHAFT_LENGTH / 2),
             (.0012, .0018, SHAFT_LENGTH), mat, axial)
        for sign in (-1, 1):
            jaw = cube(f"{side}_JAW_{sign}", (sign * .004, 0, -JAW_LENGTH / 2),
                       (.003, .004, JAW_LENGTH), mat if sign == 1 else metal, axial)
            jaw.rotation_euler[1] = sign * math.radians(-8)
        cylinder(f"{side}_HANDLE", (0, 0, SHAFT_LENGTH + .013), .009, .026, mat, axial)
        ring(f"{side}_HANDLE_REFERENCE", (.013, 0, SHAFT_LENGTH + .025), .013, .0025, mat, axial)
        empty(f"{side}_TIP_REFERENCE", axial)
        empty(f"{side}_HANDLE_REFERENCE_POINT", axial, (0, 0, SHAFT_LENGTH))
    bpy.ops.object.camera_add(location=CAMERA_POSITION)
    camera = bpy.context.object
    camera.name = "LAPAROSCOPIC_CAMERA"
    camera.data.type = "PERSP"
    camera.data.lens = CAMERA_LENS_MM
    camera.data.sensor_width = CAMERA_SENSOR_MM
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.clip_start = .005
    camera.data.clip_end = 10
    aim(camera, CAMERA_TARGET)
    scene.camera = camera
    for name, pos, energy, size in LIGHTS:
        bpy.ops.object.light_add(type="AREA", location=pos)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        aim(light, (0, .03, -.08))
    scene["prototype"] = "LapSim-AI Phase 1A | original primitives | unvalidated engineering demo"
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.type = "MATERIAL"
    bpy.ops.object.select_all(action="DESELECT")
    root = bpy.data.objects["LEFT_INSTRUMENT"]
    root.select_set(True)
    bpy.context.view_layer.objects.active = root
    return scene
