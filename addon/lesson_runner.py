"""
Deterministic Lesson Runner skeleton for Chiron add-on.

This runner validates lesson JSON and executes a safe, whitelisted
subset of commands locally. Production behavior should not execute
arbitrary code; heavy actions (e.g., mutating the scene) must be
implemented as explicit, audited handlers.
"""
import time
import logging
import bpy
from typing import Dict, Any

from .validation import validate_lesson

LOGGER = logging.getLogger("chiron.lesson_runner")

# Minimal whitelist of allowed command names
ALLOWED_COMMANDS = {
    "SPEAK",
    "WAIT",
    "UI_HIGHLIGHT",
    "RUN_OPERATOR",
    "ADD_CUBE", # Shorthand
    "SELECT_OBJECT", # Shorthand
}

# Whitelist of allowed operators for RUN_OPERATOR
ALLOWED_OPERATORS = {
    "mesh.primitive_cube_add",
    "mesh.primitive_sphere_add",
    "object.select_all",
    "object.transform_apply",
}


class LessonRunner:
    def __init__(self, lesson: Dict[str, Any]):
        self.lesson = lesson

    def validate(self) -> bool:
        """Validate lesson JSON structure. Raises ValueError on failure."""
        return validate_lesson(self.lesson)

    def run(self) -> None:
        """Run the lesson deterministically by executing each step in order."""
        self.validate()
        steps = self.lesson.get("steps", [])
        for step in steps:
            try:
                self.run_step(step)
            except Exception as e:
                LOGGER.error("Step %s failed: %s", step.get("step_id"), e)
                raise

    def run_step(self, step: Dict[str, Any]) -> None:
        cmd = step.get("command")
        if not cmd:
            raise ValueError("Missing command in step")
        if cmd not in ALLOWED_COMMANDS:
            raise ValueError(f"Command not allowed: {cmd}")

        args = step.get("args") or step.get("params") or {}
        
        # Dispatch to handlers
        if cmd == "SPEAK":
            self._handle_speak(args)
        elif cmd == "WAIT":
            self._handle_wait(args)
        elif cmd == "UI_HIGHLIGHT":
            self._handle_ui_highlight(args)
        elif cmd == "RUN_OPERATOR":
            self._handle_run_operator(args)
        elif cmd == "ADD_CUBE":
            self._handle_run_operator({"operator": "mesh.primitive_cube_add"})
        elif cmd == "SELECT_OBJECT":
             # Simple shorthand for selection if target provided
             target = args.get("name")
             if target:
                 bpy.ops.object.select_all(action='DESELECT')
                 if target in bpy.data.objects:
                     bpy.data.objects[target].select_set(True)
                     bpy.context.view_layer.objects.active = bpy.data.objects[target]

    def _handle_speak(self, args: Dict[str, Any]) -> None:
        text = args.get("text") or args.get("message")
        if not text:
            return
            
        # Try to use the SPEAK handler from command_handlers if merged into globals
        # or call it directly if we can import it.
        try:
            from .command_handlers import speak_handler
            speak_handler(args)
        except Exception as e:
            LOGGER.error("SPEAK failed: %s", e)
            # Fallback to simple print
            print(f"SPEAK: {text}")

    def _handle_wait(self, args: Dict[str, Any]) -> None:
        seconds = float(args.get("seconds", args.get("duration", 0)))
        if seconds > 0:
            # Note: time.sleep freezes Blender UI. In a real addon we'd use a timer.
            # But for the runner called via timer, this is mostly fine for short waits.
            time.sleep(seconds)

    def _handle_ui_highlight(self, args: Dict[str, Any]) -> None:
        target = args.get("target")
        # Logic to highlight UI elements would go here (e.g. workspace changes)
        LOGGER.info("UI_HIGHLIGHT requested for target: %s", target)

    def _handle_run_operator(self, args: Dict[str, Any]) -> None:
        op_path = args.get("operator")
        params = args.get("params", {})
        if not op_path or not isinstance(op_path, str):
            raise ValueError("RUN_OPERATOR requires an operator string")
            
        if op_path not in ALLOWED_OPERATORS:
            LOGGER.warning("Operator %s not in whitelist, skipping", op_path)
            return

        # Dynamically call bpy.ops.folder.operator
        try:
            parts = op_path.split('.')
            op = bpy.ops
            for part in parts:
                op = getattr(op, part)
            
            # Call the operator with params as kwargs
            op(**params)
            LOGGER.info("Executed operator: %s", op_path)
        except Exception as e:
            LOGGER.error("Failed to execute operator %s: %s", op_path, e)
