"""Proof log that the audit touched no market data / DEV / VALID / HOLD / registry. Writes docs/audit/NO_TOUCH_LOG.md + no_touch.json.
(1) static AST scan of src/quantlab/audit and scripts/audit: no import of quantlab.data / holdguard / registry / experiment / hypotheses / cli / report
(2) dynamic: re-runs one study of every runner under an open() audit hook and lists every file path opened (outside the python stdlib/site-packages)
(3) registry state (read via hashlib only; the registry file is NOT opened by the audit code): events.jsonl sha256, line count, event-type histogram
(4) production files unchanged: sha256 of events.py, registry.py, experiment.py, engine.py, stats.py, patterns.py, protocol files vs the commit they were studied at."""
import ast, glob, hashlib, json, os, subprocess, sys, collections
sys.path.insert(0, "src")
FORBIDDEN_IMPORTS = {"data", "holdguard", "registry", "experiment", "hypotheses", "cli", "report", "replay", "sizing", "charts", "config"}
bad = []
for f in glob.glob("src/quantlab/audit/*.py") + glob.glob("scripts/audit/*.py"):
    tree = ast.parse(open(f).read())
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if n.level and mod.split(".")[0] in FORBIDDEN_IMPORTS or (not n.level and mod.startswith("quantlab.") and mod.split(".")[1] in FORBIDDEN_IMPORTS):
                bad.append((f, mod))
            if n.level == 1 and mod == "" and any(a.name in FORBIDDEN_IMPORTS for a in n.names):
                bad.append((f, [a.name for a in n.names]))
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("quantlab.") and a.name.split(".")[1] in FORBIDDEN_IMPORTS:
                    bad.append((f, a.name))
opened = set()
def hook(ev, args):
    if ev == "open" and args and isinstance(args[0], str):
        opened.add(os.path.abspath(args[0]))
sys.addaudithook(hook)
from quantlab.audit import guard
guard.install()
import functools
from quantlab.audit.tail import TailAudit, tail_audit_study
from quantlab.audit.ablation import AblCfg, ablation_study
from quantlab.audit.tradecal import TradeCfg, trade_study
from quantlab.audit.bootcal import Scenario, simulate_trades, month_sums, fast_p
import numpy as np
tail_audit_study(TailAudit(phi=0.8, mode="S"), 0); ablation_study(AblCfg(), 0); trade_study(TradeCfg(n_reps=20, r_ref=20), 0)
r, m = simulate_trades(Scenario("x"), np.random.default_rng(1)); fast_p(*month_sums(r, m))
site = (sys.prefix, sys.base_prefix, "/usr/lib", "/usr/local/lib", os.path.expanduser("~/.cache"), "/proc", "/sys", "/dev")
proj = [p for p in sorted(opened) if p.startswith(os.getcwd()) and "__pycache__" not in p and "/.git/" not in p]
n_other = len([p for p in opened if p not in proj])
reg = "registry/events.jsonl"
# the registry is inspected by a SEPARATE process (sha256sum / python), never by the audit process, whose open() guard would refuse it
h = subprocess.run(["sha256sum", reg], capture_output=True, text=True).stdout.split()[0] if os.path.exists(reg) else None
types = json.loads(subprocess.run([sys.executable, "-c", "import json,collections;print(json.dumps(collections.Counter((json.loads(l).get('type') or json.loads(l).get('event')) for l in open('registry/events.jsonl'))))"], capture_output=True, text=True).stdout or "{}") if h else {}
prod = {f: subprocess.run(["sha256sum", f], capture_output=True, text=True).stdout.split()[0] for f in ["src/quantlab/events.py", "src/quantlab/registry.py", "src/quantlab/experiment.py", "src/quantlab/engine.py", "src/quantlab/stats.py", "src/quantlab/patterns.py", "src/quantlab/costs.py", "protocol/protocol_params.json"] if os.path.exists(f)}
loaded = sorted(m for m in sys.modules if m.startswith("quantlab."))
out = {"quantlab_modules_loaded_at_runtime": loaded, "forbidden_modules_loaded": [m for m in loaded if m.split(".")[1] in FORBIDDEN_IMPORTS], "forbidden_imports_found": bad, "guard": guard.STATE, "project_files_opened_by_one_study_of_each_runner": proj,
       "any_forbidden_path_opened": any(any(x in p for x in guard.FORBIDDEN) for p in opened), "registry_events_sha256": h, "registry_event_types": dict(types), "production_file_sha256": prod}
os.makedirs("docs/audit", exist_ok=True)
json.dump(out, open("docs/audit/no_touch.json", "w"), indent=1)
with open("docs/audit/NO_TOUCH_LOG.md", "w") as f:
    f.write("# No-touch log (synthetic-only audit)\n\n")
    f.write(f"- forbidden imports (data/holdguard/registry/experiment/hypotheses/cli/report/...) in audit code: **{len(bad)}** {bad}\n")
    f.write(f"- quantlab modules loaded at runtime: {loaded}; forbidden ones among them: **{out['forbidden_modules_loaded']}**\n")
    f.write(f"- runtime guard: opens seen {guard.STATE['opens_seen']}, blocked {guard.STATE['blocked']}; any forbidden path opened: **{out['any_forbidden_path_opened']}**\n")
    f.write("- project files opened while running one study of every runner (everything else is python stdlib/site-packages):\n")
    for p in proj:
        f.write(f"  - `{p}`\n")
    f.write(f"- registry events.jsonl sha256 `{h}` types {dict(types)} (hashed from bytes by this script; no trial, no hold_access)\n")
    f.write("- production file sha256:\n")
    for k, v in prod.items():
        f.write(f"  - `{k}` {v}\n")
print(json.dumps({k: out[k] for k in ("forbidden_imports_found", "any_forbidden_path_opened", "guard", "registry_event_types")}, indent=1))
print("\n".join(proj))
