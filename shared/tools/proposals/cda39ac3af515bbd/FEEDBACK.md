Summarize override-contract root causes before raw finding volume

**Symptom.** The baseline override stage reported 35,249 findings, dominated by repeated height/width mismatches. The useful diagnosis was simpler: declared exact axes bypassed keyed context, `observe_overrides` was missing, and the unknown-key probe was accepted. Evidence: `checks/before/checks/70c9dccdcc4d_before_override_results.json`.

**Suggested shared change.** Keep the full report, but put a compact root-cause block first in the stage log: “N axes bypass context,” “observer missing,” “unknown-key policy,” and one minimized witness per axis. The final battery summary already moves in this direction; printing the same block during the stage would reduce review time.
