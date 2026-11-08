# Review workspace: ordered matching

## Reproduce current verification

Run from the packet root; `review.py run` changes the payload cwd to `WORK/repo`:

```sh
python3 review.py task-tests 312fb4bdff00 --phase after --out ../checks/task-tests
python3 review.py run python3 -m arcpuzzles check 312fb4bdff00 \
  --stage semantic_gate --phase after --timeout 600 \
  --require-rotations-identifiable \
  --out ../checks/semantic-gate-absence-sentinel
python3 review.py run python3 ../checks/absence-sentinel-repair/scan.py \
  --seeds 64 --out ../checks/absence-sentinel-repair/scan.json
python3 review.py run python3 ../checks/absence-sentinel-repair/prepare_racket.py
python3 review.py run python3 -m arcpuzzles apply 312fb4bdff00 \
  --input ../checks/absence-sentinel-repair/inputs.json \
  --out ../checks/absence-sentinel-repair/racket.json
python3 review.py run python3 ../checks/absence-sentinel-repair/verify_racket.py
```

Use new output paths when repeating a framework command. `scan.py` is a reusable,
source-bound adversarial scanner. It generates indices 0–7 once per seed, reuses
them for starts 0–2, rotates all six query choices and evaluates every declared
lesson competitor. Increase `--seeds` only with an explicit runtime budget.

## Exact controls and migration

`generate(seed, sample_index, difficulty=..., **overrides)` accepts integer
`panel_s` 3–6, `n_cands` 1–4, `shape_k` 2–8, `match_count` 0–4, and
`target_color` 1–9. Omitted/None axes are sampled. Boolean, nonintegral,
out-of-range and unknown values are rejected. `observe_overrides(grid)` exposes
all five realized values. Dense explicit shapes are honored rather than clipped.

A side-6 panel cannot have four candidates because the width would exceed 30.
`match_count` cannot exceed `n_cands`. These joint restrictions are declared in
`INCOMPATIBLE_OVERRIDE_COMBINATIONS`; compatible unspecified dimensions are
chosen constructively. Removed palette/density/texture and transform knobs are
not silently accepted.

## Lesson policy and limits

The default phase is `(int(seed) + sample_index) % 3` over:

1. `multiple` — two matching candidates, with first-candidate precedence;
2. `absence` — no matching candidate and the canonical `[[0]]` sentinel;
3. `translated_single` — one match whose output placement differs from query copy.

Six consecutive positions contain two of every phase. Therefore any one-pair
query holdout leaves a demonstration for all three semantic branches. Five
consecutive examples also cover every phase. Exact overrides describe individual
grids and may replace the phase's default match count; they do not certify a
complete lesson.

Seven declared canonical-fitting rivals cover query copy, existence-gated copy,
last-match selection, output-position normalization, count-only copy,
unique-match copy and query-copy-on-absence. These are finite hypotheses, not a
universal identifiability proof. The semantic gate checks declared rivals; the
cached scanner additionally enumerates the three cyclic starts and all query
rotations for its stated seed range.

## Reading evidence

Current repair evidence is under `WORK/checks/absence-sentinel-repair/`, focused
test receipts under `WORK/checks/tdd-*`, and the passing semantic gate under
`WORK/checks/semantic-gate-absence-sentinel-v2/`. The 256-seed scan attempt timed
out and is not a passing measurement. `RESULTS.json` is the command ledger.

`review_probe.py`, `audit_lessons.py` and the repair scripts are authoring and
verification utilities, not tools for a visible-only solve. Racket remains the
production label authority.
