from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
import json


def encode_graph_payload(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_graph_payload(graph_id: str) -> dict:
    padding = "=" * (-len(graph_id) % 4)
    raw = urlsafe_b64decode(f"{graph_id}{padding}".encode("utf-8"))
    return json.loads(raw.decode("utf-8"))
