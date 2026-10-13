"""Read an OTLP/JSON trace export into the inspector's span representation."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _value(value: Any) -> Any:
    if not isinstance(value, dict):
        raise ValueError("attribute value must be an OTLP AnyValue object")
    for key in ("stringValue", "boolValue", "doubleValue", "intValue", "bytesValue"):
        if key in value:
            return int(value[key]) if key == "intValue" else value[key]
    if "arrayValue" in value:
        return [_value(item) for item in value["arrayValue"].get("values", [])]
    if "kvlistValue" in value:
        return _attributes(value["kvlistValue"].get("values", []))
    return None


def _attributes(items: Any) -> dict[str, Any]:
    if not isinstance(items, list):
        raise ValueError("attributes must be an OTLP KeyValue array")
    return {item["key"]: _value(item["value"]) for item in items}


def _id(value: Any, length: int, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-fA-F]{{{length}}}", value) or not int(value, 16):
        raise ValueError(f"{field} must be a nonzero {length}-character hex ID")
    return value.lower()


def _span(raw: dict[str, Any], resource: dict[str, Any], path: Path) -> dict[str, Any]:
    trace_id = _id(raw.get("traceId"), 32, "traceId")
    span_id = _id(raw.get("spanId"), 16, "spanId")
    parent = raw.get("parentSpanId")
    parent_id = _id(parent, 16, "parentSpanId") if parent else None
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a nonempty string")
    try:
        start = int(raw["startTimeUnixNano"])
        end = int(raw["endTimeUnixNano"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("startTimeUnixNano and endTimeUnixNano must be integers") from exc
    if start < 0 or end < start:
        raise ValueError("span timestamps must be nonnegative and end after start")
    attrs = _attributes(raw.get("attributes", []))
    for key, value in resource.items():
        attrs.setdefault(key, value)
    events = []
    for event in raw.get("events", []):
        events.append({
            "name": event["name"],
            "attributes": _attributes(event.get("attributes", [])),
            "time_unix_nano": int(event.get("timeUnixNano", 0)),
        })
    return {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_id,
        "name": name,
        "start_unix_nano": start,
        "end_unix_nano": end,
        "status": raw.get("status", {}),
        "attributes": attrs,
        "events": events,
        "_source_file": str(path),
    }


def parse_otlp_json(data: Any, source: str | Path) -> list[dict[str, Any]]:
    """Validate a decoded OTLP/JSON trace request and return queryable spans."""
    path = Path(source)
    if not isinstance(data, dict) or not isinstance(data.get("resourceSpans"), list):
        raise ValueError(f"{path}: expected OTLP JSON with a resourceSpans array")
    spans = []
    for resource_index, group in enumerate(data["resourceSpans"]):
        try:
            resource = _attributes(group.get("resource", {}).get("attributes", []))
            for scope in group.get("scopeSpans", []):
                for raw in scope.get("spans", []):
                    try:
                        spans.append(_span(raw, resource, path))
                    except (AttributeError, KeyError, TypeError, ValueError) as exc:
                        raise ValueError(f"span {len(spans) + 1}: {exc}") from exc
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path}: resourceSpans[{resource_index}]: {exc}") from exc
    return spans


def load_otlp_json(path: str | Path) -> list[dict[str, Any]]:
    """Load a protobuf JSON ExportTraceServiceRequest or TracesData object."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid OTLP JSON: {exc}") from exc
    return parse_otlp_json(data, path)
