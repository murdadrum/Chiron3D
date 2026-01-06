"""
Loader wrapper: if the upstream `third_party/blender-mcp/gemini_addon.py`
exists (e.g., added as a submodule), load and execute it so the real addon
is active. Otherwise, provide a small safe fallback (test connection) so the
addon can be enabled while development continues.

This avoids copying large upstream files into `chiron/` and makes it easy to
vendor the upstream repo under `third_party/blender-mcp`.
"""

import os
import importlib.util
import sys

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
THIRD_PARTY_ADDON = os.path.normpath(os.path.join(THIS_DIR, "..", "third_party", "blender-mcp", "gemini_addon.py"))

# In production builds we must NOT execute arbitrary upstream code.
# Allow dynamic loading only in explicit development mode (CHIRON_DEV_MODE=1).
if os.path.exists(THIRD_PARTY_ADDON) and os.environ.get("CHIRON_DEV_MODE") == "1":
    # Dev-only: load upstream addon file dynamically for local testing.
    spec = importlib.util.spec_from_file_location("chiron.upstream_gemini", THIRD_PARTY_ADDON)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # Do not blindly inject all globals; expose only a safe, minimal surface if required.
    try:
        if hasattr(module, "register") and hasattr(module, "unregister"):
            register = module.register
            unregister = module.unregister
    except Exception:
        pass
elif os.path.exists(THIRD_PARTY_ADDON):
    # Upstream addon is present but we're not in dev mode — refuse to execute it.
    print("[chiron] Upstream gemini_addon found but CHIRON_DEV_MODE!=1; skipping execution for safety.")
else:
    # Fallback minimal safe implementation
    import bpy
    import urllib.request
    import urllib.error
    import json
    import threading
    import http.server
    from bpy.props import StringProperty, BoolProperty
    from .lesson_runner import LessonRunner

    bl_info = {
        "name": "Chiron Sidecar Bridge",
        "author": "Chiron",
        "version": (0, 1, 1),
        "blender": (5, 0, 0),
        "location": "View3D > Sidebar > Chiron",
        "description": "Functional bridge for the Chiron Sidecar UI. Enables AI-guided lessons via local MCP server.",
        "category": "3D View",
    }

    class CHIRON_AddonPreferences(bpy.types.AddonPreferences):
        bl_idname = __package__ or __name__.split('.')[0]

        chiron_tts_enabled: BoolProperty(
            name="Enable TTS",
            description="Allow Chiron to play TTS audio locally (opt-in)",
            default=False,
        )

        chiron_tts_voice: StringProperty(
            name="TTS Voice",
            description="Preferred TTS voice name (optional)",
            default="",
        )

        def draw(self, context):
            layout = self.layout
            layout.label(text="Chiron Preferences")
            layout.prop(self, "chiron_tts_enabled")
            layout.prop(self, "chiron_tts_voice")

    class CHIRON_MCP_RequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "server": "chiron"}).encode())
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path == "/lesson":
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                try:
                    payload = json.loads(post_data.decode('utf-8'))
                    lesson = payload.get("lesson")
                    if not lesson:
                        self.send_error(400, "Missing lesson payload")
                        return
                    
                    # Wrap single step in a list if needed (though bridge usually sends list)
                    if isinstance(lesson, dict):
                        lesson = {"lesson_id": "remote", "title": "Remote Step", "steps": [lesson]}
                    elif isinstance(lesson, list):
                        lesson = {"lesson_id": "remote", "title": "Remote Steps", "steps": lesson}

                    # Execute lesson on main thread using a timer or queue if needed,
                    # but for now we'll try direct execution if safe.
                    # BPY is not thread-safe. We must use a timer to run on main thread.
                    self.server.cmd_queue.append(lesson)
                    
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode())
                except Exception as e:
                    self.send_error(500, str(e))
            else:
                self.send_error(404)

    class CHIRON_MCP_Server(http.server.HTTPServer):
        def __init__(self, server_address, RequestHandlerClass):
            super().__init__(server_address, RequestHandlerClass)
            self.cmd_queue = []
            self.is_running = True

    _mcp_server_thread = None
    _mcp_server = None

    def _run_mcp_server(host, port):
        global _mcp_server
        try:
            _mcp_server = CHIRON_MCP_Server((host, int(port)), CHIRON_MCP_RequestHandler)
            print(f"[chiron] MCP Server started on {host}:{port}")
            _mcp_server.serve_forever()
        except Exception as e:
            print(f"[chiron] MCP Server failed: {e}")

    def _process_mcp_queue():
        global _mcp_server
        if _mcp_server and _mcp_server.cmd_queue:
            while _mcp_server.cmd_queue:
                lesson = _mcp_server.cmd_queue.pop(0)
                try:
                    runner = LessonRunner(lesson)
                    runner.run()
                except Exception as e:
                    print(f"[chiron] Failed to run remote lesson: {e}")
        return 0.1 # Run every 100ms

    class CHIRON_OT_mcp_test_connection(bpy.types.Operator):
        bl_idname = "chiron.mcp_test_connection"
        bl_label = "Test MCP Connection"
        bl_description = "Ping the MCP server health endpoint"

        def execute(self, context):
            scn = context.scene
            host = scn.chiron_mcp_host or "localhost"
            port = scn.chiron_mcp_port or "9876"
            protocol = scn.chiron_mcp_protocol or "http"
            url = f"{protocol}://{host}:{port}/health"
            try:
                with urllib.request.urlopen(url, timeout=5) as r:
                    body = r.read().decode("utf-8")
                    self.report({"INFO"}, f"MCP health: {body}")
            except urllib.error.URLError as e:
                self.report({"ERROR"}, f"MCP ping failed: {e}")
            except Exception as e:
                self.report({"ERROR"}, f"Unexpected error: {e}")
            return {"FINISHED"}


    class CHIRON_PT_mcp_panel(bpy.types.Panel):
        bl_label = "Chiron MCP"
        bl_idname = "CHIRON_PT_mcp_panel"
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Chiron"

        def draw(self, context):
            layout = self.layout
            scn = context.scene
            layout.prop(scn, "chiron_mcp_host")
            layout.prop(scn, "chiron_mcp_port")
            layout.prop(scn, "chiron_mcp_protocol")
            # Show persisted addon preferences for TTS when available
            try:
                addon_key = __package__ or __name__.split('.')[0]
                prefs = context.preferences.addons[addon_key].preferences
                layout.prop(prefs, "chiron_tts_enabled")
                layout.prop(prefs, "chiron_tts_voice")
            except Exception:
                # Fallback to scene-level toggle if preferences unavailable
                layout.prop(scn, "chiron_tts_enabled")
            layout.operator("chiron.mcp_test_connection", icon="URL")


    def register():
        bpy.types.Scene.chiron_mcp_host = StringProperty(
            name="MCP Host",
            description="Hostname for the local MCP server",
            default="localhost",
        )
        bpy.types.Scene.chiron_mcp_port = StringProperty(
            name="MCP Port",
            description="Port for the local MCP server",
            default="9876",
        )
        bpy.types.Scene.chiron_mcp_protocol = StringProperty(
            name="Protocol",
            description="http or https",
            default="http",
        )
        # Note: persistent TTS settings are stored in AddonPreferences; keep
        # a transient scene toggle for quick tests if preferences are unavailable.

        for cls in (CHIRON_AddonPreferences, CHIRON_OT_mcp_test_connection, CHIRON_PT_mcp_panel):
            try:
                bpy.utils.register_class(cls)
            except Exception:
                pass

        # Start MCP Server Thread
        global _mcp_server_thread
        scn = bpy.context.scene
        host = scn.chiron_mcp_host or "localhost"
        port = scn.chiron_mcp_port or "9876"
        _mcp_server_thread = threading.Thread(target=_run_mcp_server, args=(host, port), daemon=True)
        _mcp_server_thread.start()
        
        # Register queue processor timer
        bpy.app.timers.register(_process_mcp_queue)


    def unregister():
        try:
            del bpy.types.Scene.chiron_mcp_host
            del bpy.types.Scene.chiron_mcp_port
            del bpy.types.Scene.chiron_mcp_protocol
        except Exception:
            pass
        try:
            bpy.utils.unregister_class(CHIRON_PT_mcp_panel)
        except Exception:
            pass
        try:
            bpy.utils.unregister_class(CHIRON_OT_mcp_test_connection)
        except Exception:
            pass
        try:
            bpy.utils.unregister_class(CHIRON_AddonPreferences)
        except Exception:
            pass

        # Stop MCP Server
        global _mcp_server, _mcp_server_thread
        if _mcp_server:
            _mcp_server.shutdown()
            _mcp_server.server_close()
            _mcp_server = None
        
        # Unregister timer
        if bpy.app.timers.is_registered(_process_mcp_queue):
            bpy.app.timers.unregister(_process_mcp_queue)


    if __name__ == "__main__":
        register()

# Merge in any extra command handlers (e.g., SPEAK) provided by `chiron/command_handlers.py`
try:
    from .command_handlers import COMMAND_HANDLERS as EXTRA_COMMAND_HANDLERS
except Exception:
    EXTRA_COMMAND_HANDLERS = {}

if EXTRA_COMMAND_HANDLERS:
    try:
        if 'COMMAND_HANDLERS' in globals():
            COMMAND_HANDLERS.update(EXTRA_COMMAND_HANDLERS)
        else:
            COMMAND_HANDLERS = EXTRA_COMMAND_HANDLERS
    except Exception as e:
        print('[chiron] Failed to merge EXTRA_COMMAND_HANDLERS:', e)
