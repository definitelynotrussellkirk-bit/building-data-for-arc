# Workspace

`shortcut_probe.py` is a source-bound reviewer probe for the strongest uncovered
canonical-fitting rival found in this review: fill every frame with an odd number
of marker cells. It verifies the rival on all retained canonical pairs, then
samples a fixed number of final-generator lessons in each difficulty band and
records unique-input counts, marker-count profiles, disagreements, hashes, and
one exact witness.

Run from the packet root:

```bash
python3 repo/generators/5751ed9bdf85/workspace/shortcut_probe.py \
  --samples 100 --out checks/shortcut/odd-marker-probe.json
```

This tool is evidence, not output authority. The selected implementation remains
`../generator.py`; the Racket rule remains authoritative.
