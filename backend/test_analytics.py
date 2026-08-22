import json
import os

from services.analytics import AnalyticsService


def test_analytics_service_writes_jsonl_event(tmp_path):
    sink = tmp_path / "analytics.jsonl"
    service = AnalyticsService(sink_path=str(sink))

    emitted = service.emit("segment_request_started", {"filename": "demo.png", "content_type": "image/png"})

    assert emitted is True
    assert sink.exists()
    lines = sink.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event"] == "segment_request_started"
    assert data["payload"]["filename"] == "demo.png"
    assert "timestamp" in data
