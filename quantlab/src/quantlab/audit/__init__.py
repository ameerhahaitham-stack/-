"""Independent statistical audit (round 5). SYNTHETIC DATA ONLY. Diagnostic code: nothing here is imported by the production path.

Imports of production modules are READ-ONLY (events, engine, stats, patterns, calibration). This package never imports
quantlab.data, quantlab.holdguard or quantlab.registry, and every runner installs `guard.install()` which turns any attempt to open
files under the project's data/, registry/, results/, sealed or raw-vault locations into an error (and counts the attempts)."""
