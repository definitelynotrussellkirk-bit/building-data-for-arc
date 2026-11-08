# Largest-rectangle rendering modes — proposed prototype

This task-local extension is **proposed and unapproved**. It preserves the
original 16×16 generator, unique largest same-color solid rectangle selection,
attached-tab rejection, original coordinates, and clearing of distractors.
Only rendering of the selected rectangle varies. No production generator,
canonical rule, approval hash, or training admission is changed.

`Parameters(shape_mode="solid", paint_color=None)` is the original setting and
returns the exact preserved canonical Racket source. `shape_mode` is `solid` or
`outline`; `paint_color` is source color (`None`) or an exact integer 1–9.
These form 20 settings. The outline clears strictly interior cells. Two-row
rectangles have equal solid and outline outputs, so the first two demonstrations
always use `3x3_tab` and `3x4_tab` and distinct source winner colors. This
distinguishes both shape and source-color behavior from all fixed-color rivals.
Each episode fixes its parameters across all demonstrations and queries.

From the outer packet directory, run the complete twenty-setting, four-query
batch (choose a fresh output directory on each run):

```sh
python3 review.py run python3 generators/061566027b67/workspace/parametric/rectangle_modes.py --seed 42 --train 3 --test 4 --all-settings --out ../checks/parametric/rectangle-modes
```

A single alternative setting is runnable as:

```sh
python3 review.py run python3 generators/061566027b67/workspace/parametric/rectangle_modes.py --seed 42 --train 3 --test 4 --shape-mode outline --paint-color 8 --out ../checks/parametric/rectangle-outline8-seed42
```

The CLI uses one persistent protected Racket bridge. Every authored label is
executed through its materialized Racket program and compared to a strict Python
mirror. Runtime errors and disagreements are fatal. `build_episode` provides the
same check for one episode. Parameters are selected explicitly; the CLI's
`--all-settings` enumerates the complete finite domain with shared source draws.

Demonstration counts are exact integers 2–16; query counts are 1–16, default 4.
The remaining demonstrations and queries cycle the four original profiles.
Every input in an episode is distinct. The existing source has a bounded 120
layout attempts per draw; this prototype additionally permits at most 64 draws
per requested distinct input and raises on exhaustion. It never clones pairs or
silently reduces counts. Grids must be lists of 16 lists of 16 exact integer ARC
colors and satisfy all selected generator constraints. Booleans are rejected.

The certificate enumerates all 20 hypotheses and eliminates them using only
demonstration input/output pairs. For each query input it checks whether the
survivors disagree about the output; it never reads a query answer to eliminate
a hypothesis. This is bounded finite-domain identifiability, not evidence
against every possible ARC rule or a measured difficulty/calibration claim.

`write_batch` requires a new output directory and rejects duplicate visible
payloads before writing. `public/<sha256>.json` contains exactly the canonical
bytes from shared `reviewer_support.public_challenge_bytes`; each identifier is
the shared visible-content hash. The manifest orders these identifiers
lexicographically. Public files expose demonstration labels and query inputs
only. All hidden settings, seeds, query answers, materialized program text and
hashes, source hashes, runtime identity and certificates remain under `private/`.
Changing private metadata or query labels cannot change a public identifier.

This prototype depends on the selected packet's generator, preserved canonical
solution JSON, shared reviewer helpers, and included Racket runtime. It does not
provide a new production parametric-rule interface. The full protected runtime
must be available; Python-only label fallback is deliberately unsupported.
