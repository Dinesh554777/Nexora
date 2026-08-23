import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Structured non-blocking analytics emitter.

    This implementation records API lifecycle events to a JSONL file so analytics
    can be verified in tests and inspected in real runs without blocking the
    request flow.
    """

    def __init__(self, sink_path: str | None = None) -> None:
        self.enabled = True
        default_path = os.getenv(
            "NEXORA_ANALYTICS_PATH",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "analytics.jsonl"),
        )
        self.sink_path = sink_path or default_path
        self._lock = threading.Lock()
        self._ensure_sink_exists()

    def _ensure_sink_exists(self) -> None:
        sink = Path(self.sink_path)
        sink.parent.mkdir(parents=True, exist_ok=True)
        if not sink.exists():
            sink.touch()

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> bool:
        if not self.enabled:
            return False

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_name,
            "payload": payload or {},
        }

        try:
            serialized = json.dumps(event, default=str, separators=(",", ":"))
            with self._lock:
                with open(self.sink_path, "a", encoding="utf-8") as handle:
                    handle.write(serialized)
                    handle.write("\n")
            logger.info("analytics_event=%s", serialized)
            return True
        except Exception:
            logger.exception("Failed to write analytics event")
            return False


analytics_service = AnalyticsService()
