# Workspace

The selected implementation is `../generator.py`. This workspace retains the source-bound before/after diagnostic tooling:

- `generator_before.py` — byte-for-byte imported v3.1.0 source used for the reproduced baseline.
- `contact_graph_audit.py` — independent component extraction, contact-graph reconstruction, shortest-path oracle, exact-control probes, rival/witness census, and lesson-window checks. It deliberately does not call the candidate's private analyzer.

Replay from the packet `repo/` directory:

```bash
PYTHONPATH=src:shared/runtime python3 generators/ee37b0acdd32/workspace/contact_graph_audit.py \
  --generator generators/ee37b0acdd32/workspace/generator_before.py \
  --samples-per-band 120 --skip-overrides \
  --output ../checks/root-cause/before-contact-graph.json

PYTHONPATH=src:shared/runtime python3 generators/ee37b0acdd32/workspace/contact_graph_audit.py \
  --samples-per-band 300 \
  --output ../checks/final/contact-graph-audit.json
```

The first command exits nonzero by design because it reproduces baseline failures. The second must exit zero for the final source.
