# 997c17fd6870 review implementation plan

## Production repair (valid behavior unchanged)

1. Add portable tests that reproduce the public-call scalar defect, missing
   semantic contract, and selected authority exact-text drift.
2. Reject non-literal `seed`/`sample_index` and negative `sample_index` before
   constructing `gen_ctx`.
3. Declare a three-demo semantic contract. Every lawful scene must refute both
   identity and whole-row reflection; lesson validation must also reject bad
   labels and surviving competitors.
4. Use the repository's hash-bound `authority-sync --selected-only` proposal and
   explicit apply flow. Preserve archival `raw_code` byte-for-byte.
5. Prove outputs for valid calls are unchanged against the retained baseline
   source copy, then rerun focused tests and the full battery.

## Isolated parametric prototype

1. Add tests for a hidden episode-level `tile_width` in `{2, 3}` with default 2.
2. Materialize exact Racket callables for both settings; labels must be produced
   by live Racket execution, with Python used only as an independent mirror.
3. Build complete episodes (three demonstrations plus one query) from 12x12
   two-color motif scenes. Each scene must pass the selected generator grammar,
   and demonstrations must distinguish the chosen setting from the alternative.
4. Emit redacted public challenges, private answers/programs/hashes, canonical
   default parity, and a compact summary under `WORK/checks/parametric/`.

## Final review evidence

Run task tests, the strict after-battery, a post-repair visible-only solve, two
random no-edit audits, answer the data-quality question, write review reports,
and package only the bounded return ZIP.
