# No-touch log (synthetic-only audit)

- forbidden imports (data/holdguard/registry/experiment/hypotheses/cli/report/...) in audit code: **0** []
- quantlab modules loaded at runtime: ['quantlab.audit', 'quantlab.audit.ablation', 'quantlab.audit.bootcal', 'quantlab.audit.events_null', 'quantlab.audit.guard', 'quantlab.audit.sampler', 'quantlab.audit.synth', 'quantlab.audit.tail', 'quantlab.audit.tradecal', 'quantlab.calibration', 'quantlab.costs', 'quantlab.engine', 'quantlab.events', 'quantlab.patterns', 'quantlab.stats']; forbidden ones among them: **[]**
- runtime guard: opens seen 959, blocked 0; any forbidden path opened: **False**
- project files opened while running one study of every runner (everything else is python stdlib/site-packages):
- registry events.jsonl sha256 `a34e39fb5f1464ba1c7ef320c7aa8a0393f512c2639de407592568bc9cac42de` types {'protocol_locked': 1, 'hypothesis_registered': 15, 'code_update': 4} (hashed from bytes by this script; no trial, no hold_access)
- production file sha256:
  - `src/quantlab/events.py` 96e1214bc8975a439da868d532d02045b99a4028b90ec697cd9ab611f7632a71
  - `src/quantlab/registry.py` e4d3484b85fe371931eaae32ae92e7a86a1285e8d5963f9a9b667be580a8a542
  - `src/quantlab/experiment.py` d3353b321abf060faa8bd7dfc51875f7b4ac974e87ad602c6630fe350b188df1
  - `src/quantlab/engine.py` 0711db226c3d81593ea7458ea3fbd1e234d56ab6a05e442ebc69461064c85b40
  - `src/quantlab/stats.py` 5d14932fe927b2ad5887a07321a50a3789d44942aa202e778fd0ad0d9a1d3df7
  - `src/quantlab/patterns.py` 6ac2801a55af687d26e8e48961e6cc836f0285a069efc9b5faac324da20fc4db
  - `src/quantlab/costs.py` 5185c210dbb8e70a8eaaaddb425ad1395661f33d826cc80971dd61a3e046bc58
  - `protocol/protocol_params.json` 36f714ce4e5bd7f1f625a8842c4f251aec0b6eda3d1db6429993e3a7a5684fbe
