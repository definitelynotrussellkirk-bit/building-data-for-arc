# Handoff for the next review

## Starting point

Selected generator version: `3.0.0`.
Generator SHA-256: `6ac6a1032c153b6a8f7b4dbe1edb39ae423ce4397908a3c88f74b61bca4d62f7`.
Canonical rule hash: `e0b73d0c2fd9`; no canonical or archival authority changed.
Lesson probe SHA-256: `a054b196f9cff75f174fe12e959b776949a3dc0089642dc3f6bae68cf0f3b03b`.

The final source passed 50 focused tests, all 12 battery stages, and a Racket-backed
400-lesson probe against seven named rivals. The same probe and evaluator scored
the baseline at 0/400 identifiable lessons. This comparison has 2,000 distinct
inputs per sampler, not 2,000 independent lessons. Complete evidence is retained
in return assignment `review-133862fbfa7d5f89`.

## Reuse the built tools

`lesson_probe.py` samples actual episodes, evaluates every declared rival, and
emits source-bound JSON. Use the commands in `README.md`; inspect semantic fields
rather than treating process exit zero as a learning result. `--generator` can
compare another source version using the current evaluator, with both hashes
recorded. `--seed`, `--sample-index`, and `--lessons-per-band` support
reproducing and extending the recorded sampler.

The regression suite has independent literal/reference fixtures, exact axis
endpoints and aliases, malformed-grid and role-removal mutations, final-pixel
observations, witness claims, deterministic RNG checks, and real Racket execution.
The exact previously missing singleton lesson is covered; avoid replacing it
with a test that merely repeats the implementation's construction algorithm.

## Preserve distinctions in future claims

1. `_grid_errors` covers physical ARC grids. `self_check` covers the mixed
   curriculum. `strict_canonical_like` additionally requires a horizontal keeper.
   Lawful all-zero or all-erased outputs still belong in reference regression tests.
2. Ordinary controls use at least three colors and two keepers. Exact overrides
   permit two colors or one keeper. The complete seven-rival lesson promise is
   measured for ordinary lessons, not every exact override combination.
3. The ordinary family forces a repeated-row distractor spanning at least three
   rows. A new row-span or count heuristic is an open candidate until it has an
   executable rival, an actual canonical-fitting check, and a separating example.
4. Width 7 is a deliberate capacity bound. Changing it requires rechecking minimum
   canvas, palette 9, keeper 1, background preservation, and exact override behavior.
5. Reference execution, curriculum admission, finite-rival lesson identifiability,
   and private solve correctness are separate facts. The review changes no catalog
   approval or training-admission flag.

## Retained failures are useful evidence

`checks/lesson-initial-100.json` records the initial 397/400 result, despite a
40/40 smoke pass. Easy seed/start pairs `(1002716,75)`, `(1002772,355)`, and
`(1002781,400)` lacked singleton demonstrations while both queries had them.
`checks/iterations/initial_generator.py` preserves that exact source. The final
probe now explicitly separates successful computation from semantic success.

`checks/after/` retains the intermediate full-battery failures for alias
declarations, curriculum validation, and keyed alias provenance.
`checks/iterations/gate_failure_generator.py` binds those failures to their source.
If a large evidence JSON is stored as gzip, `checks/COMPRESSED_EVIDENCE.json` and
`checks/RESTORE_EVIDENCE.md` describe lossless restoration and hashes.

## Findings-only audit leads

The separately drawn audits were not edited. `AUDIT.md` in the return records
accepted handbuilt counterexamples and actual Racket evidence for:

- `9c5259babb4b`: four-neighbor asymmetric-shape growth leaves a connectivity
  shortcut unchallenged; a diagonally connected asymmetric object separates it.
- `902d22dfd388`: every outside-frame distractor lies on the canvas perimeter;
  moving one inward while keeping it outside the frame defeats perimeter filtering.

These are support gaps, not wrong generated labels. Use the included probes as
reproduction leads if an authorized future assignment selects either target.

## Return discipline

The reviewed generator was frozen before the exposed post-repair solve. Preserve
the finished solve snapshots and their declared exposure; do not relabel that
solve as blind or claim a masked score. Any generator change after preparation
requires a new source-bound solve under the review workflow.

Before returning another change, apply the exact `repo/`-prefixed source patch at
a fresh packet root with its own `git init -q`, rerun focused tests there, and
compare source hashes with the checked generator and solve record. Keep the fresh
repository outside `checks/`; only its concise verification receipts belong in
the small return ZIP.
