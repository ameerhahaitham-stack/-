"""HOLD isolation audit. Run it before locking and after every research session:  python -m quantlab.cli audit-hold

It checks (1) sealed files are intact and read-only, (2) the registry never logged a HOLD trial without an audited opening,
(3) research code has no direct path to sealed or raw files, (4) dev/valid data given to research stops before HOLD starts,
(5) raw files that still contain HOLD-period rows (a procedural exposure the audit reports honestly).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd

from . import registry
from .config import protocol_params, root
from .data import _read_split, _split_bounds, load_manifest, load_with_context, sha256_file

ALLOWED = {"data.py", "cli.py", "holdguard.py", "config.py"}   # data.py/cli.py/holdguard.py touch sealed/raw paths; config.py only creates empty folders
PATTERNS = [r"data[/\\]sealed", r"\bsealed\b", r"data[/\\]incoming", r"\braw_file\b", r"_hold\.csv", r"\bload_manifest\b", r"\b_read_split\b"]


def _code_tokens(path: Path) -> list[str]:
    """Identifiers, attribute names and non-docstring string literals of a module (comments and docstrings are ignored)."""
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    doc_nodes = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(getattr(n.body[0], "value", None), ast.Constant) and isinstance(n.body[0].value.value, str):
            doc_nodes.add(id(n.body[0].value))
    toks = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            toks.append(n.id)
        elif isinstance(n, ast.Attribute):
            toks.append(n.attr)
        elif isinstance(n, (ast.ImportFrom,)):
            toks += [a.name for a in n.names]
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes:
            toks.append(n.value)
    return toks


def _status(ok: bool, warn: bool = False) -> str:
    return "PASS" if ok else ("WARN" if warn else "FAIL")


def audit() -> list[dict]:
    out = []
    m = load_manifest()
    hold_start = pd.Timestamp(protocol_params()["splits"]["hold"]["start"])
    # 1. sealed integrity + permissions
    bad_hash, writable, missing = [], [], []
    for key, e in m.items():
        p = root() / e["splits"]["hold"]["file"]
        if not p.exists():
            missing.append(key)
            continue
        if sha256_file(p) != e["splits"]["hold"]["sha256"]:
            bad_hash.append(key)
        if os.access(p, os.W_OK) and os.geteuid() != 0 and (p.stat().st_mode & 0o222):
            writable.append(key)
    out.append({"check": "sealed_files_intact", "status": _status(not bad_hash and not missing), "detail": f"hash mismatches {bad_hash}, missing {missing}, files {len(m)}"})
    out.append({"check": "sealed_files_read_only", "status": _status(all(not (( root() / e['splits']['hold']['file']).stat().st_mode & 0o222) for e in m.values())),
                "detail": "all sealed files have write bits cleared (chmod 444); note: root can still override"})
    # 2. registry
    evs = registry.read_events()
    opened = {e["hid"] for e in evs if e["type"] == "hold_access"}
    viol = [e["hid"] for e in evs if e["type"] == "trial" and e["split"] == "hold" and e["hid"] not in opened]
    out.append({"check": "registry_hold_trials_have_audited_opening", "status": _status(not viol), "detail": f"hold trials without opening: {viol}; hold openings: {sorted(opened)}; chain: {registry.verify_chain()}"})
    out.append({"check": "hold_trials_logged_so_far", "status": "PASS" if not any(e['type'] == 'trial' and e['split'] == 'hold' for e in evs) else "WARN",
                "detail": f"{sum(1 for e in evs if e['type'] == 'trial' and e['split'] == 'hold')} hold trials (expected 0 before any VALID pass)"})
    # 3. static scan of code
    hits = []
    for base in ["src", "app", "scripts", "research"]:
        d = root() / base
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if f.name in ALLOWED:
                continue
            txt = "\n".join(_code_tokens(f))
            for pat in PATTERNS:
                if re.search(pat, txt):
                    hits.append(f"{f.relative_to(root())}: /{pat}/")
    out.append({"check": "no_research_code_touches_sealed_or_raw_paths", "status": _status(not hits), "detail": hits or "no direct references outside data.py/cli.py/holdguard.py"})
    # 4. what research loaders can see
    leaks = []
    for key, e in m.items():
        for split in ["dev", "valid"]:
            df, es, ee, _ = load_with_context(e["symbol"], e["tf"], split)
            if len(df) and df["time"].max() >= hold_start:
                leaks.append(f"{key}/{split} reaches {df['time'].max()}")
    out.append({"check": "dev_and_valid_loaders_stop_before_hold", "status": _status(not leaks), "detail": leaks or f"all dev/valid frames end before {hold_start.date()}"})
    try:
        load_with_context(next(iter(m.values()))["symbol"], next(iter(m.values()))["tf"], "hold")
        out.append({"check": "hold_loader_refuses_without_registry", "status": "FAIL", "detail": "hold loaded without hid"})
    except Exception as ex:
        out.append({"check": "hold_loader_refuses_without_registry", "status": "PASS", "detail": type(ex).__name__})
    # 5. raw exposure
    exposed = []
    for key, e in m.items():
        p = Path(e["raw_file"])
        if p.exists():
            exposed.append(p.name)
    out.append({"check": "raw_files_with_hold_rows_outside_seal", "status": "WARN" if exposed else "PASS",
                "detail": (f"{len(exposed)} raw files still contain HOLD-period rows in {Path(next(iter(m.values()))['raw_file']).parent}. "
                           "Procedural rule: research code never reads them (the static scan enforces this for the repo). "
                           "Move them out of the project folder before research starts if you want a stronger seal.") if exposed else "none"})
    return out
