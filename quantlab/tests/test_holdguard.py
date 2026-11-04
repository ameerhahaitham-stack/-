"""The HOLD audit must pass on a clean project and must catch real leaks."""
from quantlab import data, holdguard, registry, synth
from quantlab.config import root


def _setup():
    synth.make_all(root() / "data" / "incoming", symbols=("XAUUSD",), start="2018-01-01", end="2019-12-31", tfs=("H4",), seed=3)
    data.ingest(root() / "data" / "incoming" / "SYNTH_XAUUSD_H4.csv", "XAUUSD", "H4", "synthetic test data", synthetic=True)
    registry.lock_protocol()


def by_check(res):
    return {r["check"]: r for r in res}


def test_audit_passes_on_a_clean_project(lab):
    _setup()
    r = by_check(holdguard.audit())
    assert all(v["status"] != "FAIL" for v in r.values()), [v for v in r.values() if v["status"] == "FAIL"]
    assert r["sealed_files_read_only"]["status"] == "PASS"
    assert r["raw_files_with_hold_rows_outside_seal"]["status"] == "WARN"       # reported honestly, not hidden


def test_audit_catches_a_script_that_reads_the_sealed_file(lab):
    _setup()
    (root() / "scripts").mkdir()
    (root() / "scripts" / "peek.py").write_text("import pandas as pd\ndf = pd.read_csv('data/sealed/XAUUSD_H4_hold.csv.gz')\n")
    r = by_check(holdguard.audit())
    assert r["no_research_code_touches_sealed_or_raw_paths"]["status"] == "FAIL"


def test_audit_ignores_comments_and_docstrings(lab):
    _setup()
    (root() / "scripts").mkdir()
    (root() / "scripts" / "fine.py").write_text('"""This script never touches the sealed file."""\n# data/sealed is off limits\nx = 1\n')
    assert by_check(holdguard.audit())["no_research_code_touches_sealed_or_raw_paths"]["status"] == "PASS"


def test_audit_detects_tampered_sealed_file(lab):
    _setup()
    p = root() / "data" / "sealed" / "XAUUSD_H4_hold.csv.gz"
    p.chmod(0o644)
    p.write_bytes(p.read_bytes() + b"x")
    assert by_check(holdguard.audit())["sealed_files_intact"]["status"] == "FAIL"


def test_audit_detects_hold_trial_without_opening(lab):
    _setup()
    registry.register_hypothesis("H9", "f", "d")
    registry._append({"type": "trial", "hid": "H9", "family": "f", "symbol": "XAUUSD", "tf": "H4", "split": "hold", "cfg_hash": "x", "params": {}, "metrics": {}, "data_source": "s"})
    assert by_check(holdguard.audit())["registry_hold_trials_have_audited_opening"]["status"] == "FAIL"
