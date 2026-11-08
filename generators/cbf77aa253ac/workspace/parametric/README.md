# Proposed denser/sparser guided reflection

Task `cbf77aa253ac`; original ARC family `training:5b692c0f`.
This is a task-local research prototype. The selected production generator,
canonical authority, approval records, and training admission are unchanged.

## Rule and design

| Rule parameter | Values | Canonical default |
| --- | --- | --- |
| `side_policy` | `denser`, `sparser` | `denser` |

For each 8-connected nonzero component with both yellow guide cells and
payload, infer orientation from the guide spans and the axis from their
half-up rounded mean coordinate. Count the modal payload color on each side.
Clear the payload, then restore and reflect all cells from the selected side,
including secondary payload colors. Out-of-bounds writes are clipped by the
original rule. Components without both roles are unchanged.

`denser` is the **exact canonical Racket text**. `sparser` changes only the two
side comparisons from `>=` to `<=`; ties still choose above/left. Substitutions
are guarded by the canonical raw-text SHA-256 and exact anchor counts. No
second parameter is added: separate tie behavior would require another set
of teaching witnesses. Cosmetic-only randomization would not change the rule.

## Run from the outer review extraction directory

```bash
python3 review.py setup
python3 review.py run python3 generators/cbf77aa253ac/workspace/parametric/prototype.py --seed 17 --all-settings --demo-count 4 --query-count 4 --out ../checks/parametric/episodes-new
python3 review.py run python3 generators/cbf77aa253ac/tests/test_parametric_cbf77aa253ac.py
```

Use a new `--out` directory each time. `--all-settings` emits a complete
episode for both settings using identical inputs, allowing direct
counterfactual comparison. `--side-policy denser` or `sparser` selects one;
omitting both options selects one policy once from a deterministic seed stream.
The input stream is separate, so hidden policy selection cannot alter inputs.
The prototype uses the packet's existing Python helpers and Racket bridge;
its focused test runner is standard-library unittest.

| Argument | Supported values |
| --- | --- |
| `--seed` | Exact integer, `0..2**64-1` |
| `--demo-count` | `4..12`, default `4` |
| `--query-count` | `1..8`, default `4` |
| `--attempt-limit` | `1..512`, default `64` attempts per input |

The Python API rejects Boolean, float, and string substitutes for integers.
Unsupported counts fail explicitly. Query and demonstration inputs must all
be distinct; exhausted attempts fail instead of returning a short episode.
Canvas dimensions stay within 30 by 30. Randomness does not alter global RNG
state.

## Teaching and bounded sampling

The four required demonstrations cover horizontal/above-dense,
horizontal/below-dense, vertical/left-dense, and vertical/right-dense cases.
Each query is generated independently with fresh connected payload geometry,
colors, placement, and generally larger canvases. The default four queries
cover those same four cases.

Each sampled scene contains one straight guide and one connected component.
Both sides contain the uniquely modal main payload color with unequal counts.
Secondary-color cells are added to the main color's sparse side so that
**total payload occupancy favors the opposite side**. Thus demonstrations
separate modal-color counting from simply counting every non-yellow cell.
Both policies' full reflection footprints fit in the canvas. Neither policy
produces an identity transformation on sampled scenes.

The prototype deliberately does not sample irregular guides, count ties,
multiple components, reflection collisions, clipped writes, or mode ties.
Their full canonical behavior is retained in the Racket program, but these
branches are not claimed as learned from this narrower sampler. Canonical
parity covers six ledger occurrences of three unique public inputs; focused
execution also checks a count tie, an unaffected decoy, and a 30-by-30 canvas.

For every emitted episode, Racket executes all labels and predictions of ten
declared candidates: the two parameter settings, identity, horizontal-only,
vertical-only, always-negative, always-positive, the two orientation-specific
fixed-side rules, and total-payload counting. Candidate elimination uses only
demonstration labels. Queries are identifiable when the remaining candidates
agree on their predictions; query labels are never used to eliminate rivals.
Authoring fails unless the selected policy is the sole survivor. This is a
finite-rival certificate, not proof against every possible puzzle rule.

## Public projection and evidence

Give a model **only `public/*.json`** from an exported batch. Each public file
contains demonstration input/output pairs and query input-only objects.
Its filename is the full SHA-256 of exactly the bytes produced by
`reviewer_support.public_challenge_bytes`. Settings, seeds, programs, and query
answers cannot affect the filename. Batch entries are sorted by public ID;
duplicate visible payloads are rejected even if their private metadata differs.

`private/` retains complete labelled episodes, each policy, seed, semantic
roles, source hashes, all executed rival predictions, certificates, and exact
Racket programs named by their raw-text hashes. `manifest.json` is also private
controller data: it records paths, exact artifact hashes, source bindings,
counts, and invocation. Do not expose it or the prototype source to a solver.

The CLI executes every canonical occurrence before export. It also checks
sampled selected-policy Racket labels against a Python prediction derived from
the existing component planner. Python predictions never supply export labels.

## Existing production findings remain separate

The retained production audit reports an ordinary four-pair lesson in which
horizontal-only demonstrations leave a vertical query unidentified, plus
invalid scalar acceptance. This prototype's schedule does not change the
production sampler or clear that audit. A separate portability-only change to
the existing task tests removes their fixed paths and legacy-only import.
Its exact-authority-text assertion still fails on pre-existing whitespace
differences between the canonical and archived Racket texts, despite matching
normalized hashes. Shared authorities and that assertion are preserved.
