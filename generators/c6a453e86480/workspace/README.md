# Reusable rank-distribution probe

From the outer review packet, run:

```sh
python3 review.py run python3 generators/c6a453e86480/workspace/probe_rank_distribution.py \
  --seed 20261007 --samples 120 --out ../checks/authoring-probe.json
```

The payload runs from `WORK/repo`. Choose a new output file. In a normal checkout,
use `PYTHONPATH=src:shared/runtime python3 generators/c6a453e86480/workspace/probe_rank_distribution.py`
with the same arguments and an output under `var/`; provide Racket on PATH or
through RACKET_PATH. Requires Python 3.12+, NumPy, Pillow and the repository.
Task tests also need pytest 8+ in the exact isolated interpreter.

This tool reads the current AXES and actual CANONICAL_SHORTCUTS / LESSON_COMPETITORS
rather than duplicating their names. It checks the full dimensions × count ×
palette × band matrix at both layout parities, counts default profiles and row-2
support, verifies each canonical-compatible rival against every labeled canonical
pair, and executes 16 reference cases through public `Catalog.apply`.
The report includes all reference inputs/outputs, source hashes, generation
settings, rival outputs, and the repaired seed-12 lesson. A legal legend-color
permutation keeps fixed roles 0 and 1 unchanged and is checked against Racket.

Exit 0 means the retained finite checks passed; it is not universal
identifiability or training approval. A forced five-row lesson is outside the
full eleven-rival production guarantee. For production lesson measurements, use
the shared `arcpuzzles lesson-census` command with three demos, one query,
100 lessons per band, and query rotations.

The accompanying return also retains `checks/exhaustive_geometry_review.py`
and its original execution receipt for all 24,696 constructive configurations.
