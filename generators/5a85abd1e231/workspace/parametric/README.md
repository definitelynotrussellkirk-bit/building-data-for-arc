# Proposed compass-slot rotation prototype

This task-local authoring prototype preserves the canonical object detection,
glyph decoding, and tile-copy operation.  One hidden episode parameter rotates
the **decoded destination slot** by 0, 1, 2, or 3 clockwise quarter turns.  The
zero-turn setting returns the canonical `program_solution` byte-for-byte.
Production generation and its approved rule hash are not changed.

From the outer extracted review directory, materialize the retained evidence:

```bash
python3 review.py run python3 \
  generators/5a85abd1e231/workspace/parametric/prototype.py \
  --seeds 0 1 3 14 \
  --difficulty easy \
  --out-dir ../checks/parametric/5a85abd1e231-slot-rotation-v1
```

The command executes all four exact Racket programs through the bundled bridge,
checks the canonical default against all three labeled canonical pairs, writes
one complete public/private episode per parameter setting, verifies every named
parameter rival is refuted by all three demonstrations and the query, and
retains a differing witness.  Public challenge JSON contains only demonstration
input/output pairs and query inputs; hidden settings, programs, seeds, and query
answers stay in `private/`.
