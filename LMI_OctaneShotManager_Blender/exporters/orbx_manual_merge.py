import os
import bpy
from bpy.types import Operator

from ..utils import ensure_directory, resolve_octane_executable
from ..Workflows.manual_merge.utils import build_manual_merge_tasks
from ..Workflows.TAGs.utils import make_orbx_merge_manager


class LMB_OT_manual_orbx_merge(Operator):
    bl_idname = "lmb.manual_orbx_merge"
    bl_label = "Manual ORBX Merge"
    bl_description = "Merge selected ORBX files using Octane Standalone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props

        dest = bpy.path.abspath(props.manual_merge_destination)
        sources = [bpy.path.abspath(item.path) for item in props.manual_merge_sources]
        save_dir = bpy.path.abspath(props.manual_merge_save_dir)
        base_name = props.manual_merge_scene_name

        ensure_directory(save_dir)

        try:
            tasks = build_manual_merge_tasks(dest, sources, save_dir, base_name)
        except (FileNotFoundError, ValueError) as exc:
            self.report({'ERROR'}, f"[ShotManager] {exc}")
            return {'CANCELLED'}

        if not props.manual_merge_overwrite:
            tasks = [t for t in tasks if not os.path.exists(t[0])]
            if not tasks:
                self.report({'INFO'}, "[ShotManager] All merged files exist. Enable Overwrite to replace.")
                return {'CANCELLED'}

        octane_exec = resolve_octane_executable(props.octane_standalone_path)
        if not octane_exec:
            self.report({'ERROR'}, "[ShotManager] Invalid Octane Standalone path")
            return {'CANCELLED'}

        addon_dir = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(addon_dir, 'standalone_scripts', 'ORBXmerger.lua')

        manager = make_orbx_merge_manager(tasks, octane_exec, script_path, poll_interval=3.0)
        bpy.app.timers.register(manager, first_interval=0.0)

        self.report({'INFO'}, "[ShotManager] ORBX merging started.")
        return {'FINISHED'}


classes = (
    LMB_OT_manual_orbx_merge,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
