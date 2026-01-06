"""
Extra command handlers for Chiron — safe, limited TTS handler.
This file is imported by the chiron loader and merged into the main
`COMMAND_HANDLERS` mapping when present.
"""
import platform
import threading
import queue
import os
import logging
from typing import Dict, Any

LOGGER = logging.getLogger("chiron.command_handlers")

# Configuration
MAX_TTS_LENGTH = 2000


class _TTSWorker:
    def __init__(self):
        self._q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._thread.start()

    def enqueue(self, text: str, voice: str | None = None):
        self._q.put((text, voice))
        self.start()

    def _run(self):
        while self._running:
            try:
                text, voice = self._q.get()
            except Exception:
                break
            try:
                self._speak_immediate(text, voice)
            except Exception as e:
                LOGGER.exception("TTS playback failed: %s", e)
            finally:
                self._q.task_done()

    def _speak_immediate(self, text: str, voice: str | None = None):
        # Prefer pyttsx3 if available, else fall back to macOS `say` when explicitly allowed.
        try:
            import pyttsx3

            engine = pyttsx3.init()
            if voice:
                try:
                    engine.setProperty('voice', voice)
                except Exception:
                    LOGGER.debug('Failed to set voice "%s", ignoring', voice)
            engine.say(text)
            engine.runAndWait()
            return
        except Exception:
            LOGGER.debug("pyttsx3 not available or failed, checking platform fallback")

        if platform.system() == 'Darwin' and os.environ.get('CHIRON_ALLOW_SAY') == '1':
            # macOS fallback when explicitly allowed by env var
            import subprocess

            try:
                cmd = ['say']
                if voice:
                    cmd += ['-v', voice]
                cmd += [text]
                subprocess.Popen(cmd)
                return
            except Exception:
                LOGGER.exception("macOS say failed")

        LOGGER.warning("No available TTS engine for text: %s", text[:80])


# single shared worker
_tts_worker = _TTSWorker()


def _is_tts_enabled() -> bool:
    # Prefer addon preferences, then scene opt-in flag, then environment opt-in.
    try:
        import bpy
        addon_key = __package__ or __name__.split('.')[0]
        try:
            prefs = bpy.context.preferences.addons[addon_key].preferences
            if hasattr(prefs, 'chiron_tts_enabled'):
                return bool(getattr(prefs, 'chiron_tts_enabled'))
        except Exception:
            pass

        scn = bpy.context.scene
        if hasattr(scn, 'chiron_tts_enabled'):
            return bool(getattr(scn, 'chiron_tts_enabled'))
    except Exception:
        pass

    return os.environ.get('CHIRON_ALLOW_TTS', '0') == '1'


def speak_handler(params: Dict[str, Any]):
    text = (params.get('text') or params.get('message') or '').strip()
    voice = params.get('voice')
    if not text:
        LOGGER.info('SPEAK: no text provided')
        return {'status': 'no_text'}

    if len(text) > MAX_TTS_LENGTH:
        LOGGER.warning('SPEAK: text too long (%d chars)', len(text))
        return {'status': 'too_long', 'max': MAX_TTS_LENGTH}

    if not _is_tts_enabled():
        LOGGER.info('SPEAK: TTS disabled by user or environment')
        return {'status': 'disabled'}

    # enqueue for background playback
    _tts_worker.enqueue(text, voice)
    return {'status': 'queued'}


COMMAND_HANDLERS = {
    'SPEAK': speak_handler
}
