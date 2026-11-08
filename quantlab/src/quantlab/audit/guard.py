"""File-access guard for the audit runners: proves that no market data / registry / DEV / VALID / HOLD file is opened."""
from __future__ import annotations

import sys

FORBIDDEN = ("/quantlab/data/", "/quantlab/registry/", "/quantlab/results/", "quantlab_raw_vault", "/sealed/", "events.jsonl", "PROTOCOL.lock")
STATE = {"installed": False, "blocked": 0, "opens_seen": 0}


def _hook(event, args):
    if event == "open":
        STATE["opens_seen"] += 1
        path = str(args[0]) if args and args[0] is not None else ""
        if any(f in path for f in FORBIDDEN):
            STATE["blocked"] += 1
            raise PermissionError(f"AUDIT GUARD: opening {path!r} is forbidden in the synthetic-only audit")


def install() -> dict:
    if not STATE["installed"]:
        sys.addaudithook(_hook)
        STATE["installed"] = True
    return STATE
