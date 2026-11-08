# Workspace

The selected implementation is `../generator.py`. This directory keeps reusable, source-bound diagnostics rather than alternate selected sources.

## Distribution and lesson probe

Run from the extracted packet root:

```bash
python3 review.py run python3 generators/76b6aec98a7c/workspace/probe_distribution.py \
  --per-band 40 --window-starts 16 --racket-samples 12 \
  --out ../checks/probe-final.json
```

The probe loads the selected generator by file path and records its SHA-256. It samples every difficulty band, checks `self_check`, uniqueness, real axis coverage, exact canonical-profile support, declared-rival disagreements, all four query rotations over deterministic four-pair windows, and an optional batched parity sample against the selected Racket authority. It iterates the generator's actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations; it does not carry a copied rival-name list.

A passing finite probe means no problem was found in the sampled population and declared rival set. It does not prove uniqueness against undeclared rules. Use the shared `lesson-census --rotate-query` command for a larger Racket-labelled production census.
