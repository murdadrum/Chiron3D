"""
Lightweight lesson JSON validator.

This module provides minimal structural checks for lesson packs. For
production use, replace with a robust JSON Schema validator and strict
type checking.
"""
from typing import Dict, Any


def validate_lesson(lesson: Dict[str, Any]) -> bool:
    if not isinstance(lesson, dict):
        raise ValueError("Lesson must be an object/dictionary")

    required_top = ["lesson_id", "title", "steps"]
    for k in required_top:
        if k not in lesson:
            raise ValueError(f"Missing required top-level field: {k}")

    steps = lesson.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Lesson.steps must be an array/list")

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"Step at index {idx} must be an object")
        for fk in ["step_id", "instruction_text", "command"]:
            if fk not in step:
                raise ValueError(f"Step {idx} missing required field: {fk}")

    return True
