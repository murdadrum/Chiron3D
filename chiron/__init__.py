bl_info = {
    "name": "Chiron Sidecar Bridge",
    "author": "Chiron",
    "version": (0, 1, 2),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Chiron",
    "description": "Functional bridge for the Chiron Sidecar UI. Enables AI-guided lessons via local MCP server.",
    "category": "3D View",
}

import importlib
import bpy

def _get_classes_from_module(mod):
    classes = []
    for name in dir(mod):
        obj = getattr(mod, name)
        try:
            if issubclass(obj, bpy.types.Operator) or issubclass(obj, bpy.types.Panel):
                classes.append(obj)
        except Exception:
            continue
    return classes

def register():
    try:
        from . import gemini_addon
    except ImportError as e:
        print(f"[chiron] gemini_addon import failed: {e}")
        return

    # If the module exposes register/unregister helpers, use them.
    if hasattr(gemini_addon, "register") and callable(gemini_addon.register):
        try:
            gemini_addon.register()
            return
        except Exception as e:
            print(f"[chiron] gemini_addon.register failed: {e}")
    
    # Fallback: register all panels/operators found in the module
    classes = _get_classes_from_module(gemini_addon)
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except RuntimeWarning:
            pass # Already registered
        except Exception as e:
            print(f"[chiron] Registration failed for {cls}: {e}")

def unregister():
    try:
        from . import gemini_addon
    except ImportError:
        return

    if hasattr(gemini_addon, "unregister") and callable(gemini_addon.unregister):
        try:
            gemini_addon.unregister()
            return
        except Exception as e:
            print(f"[chiron] gemini_addon.unregister failed: {e}")
    
    classes = _get_classes_from_module(gemini_addon)
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
