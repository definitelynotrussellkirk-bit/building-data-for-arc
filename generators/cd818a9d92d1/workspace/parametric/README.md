# Directional blocker prototype

This is a proposed extension of `cd818a9d92d1` / ARC `d9f24cd1`.
The canonical generator and canonical rule remain unchanged.

## Run from the outer packet directory

```bash
python3 review.py setup
python3 review.py run python3 generators/cd818a9d92d1/workspace/parametric/prototype.py build --seeds 17 29 --demos 2 --queries 4 --out ../checks/parametric/new-run
python3 review.py run python3 generators/cd818a9d92d1/workspace/parametric/prototype.py verify ../checks/parametric/new-run
python3 review.py run python3 -m unittest discover -s generators/cd818a9d92d1/tests -p 'test_parametric*.py' -v
```

Use a new output directory. The packet supplies Racket 8.10; Python 3.12+,
NumPy and Pillow are required. The focused tests use standard-library unittest.
The wrapper runs payloads from `WORK/repo/`.

## Rule and shared input grammar

The single hidden setting is `bend_direction=left|right`, fixed across every
demonstration and query. `right` returns the exact selected canonical Racket
program. `left` changes the destination and its boundary guard.

Both settings repeat the bottom guide row, preserve gray cells, distinguish
on-column blockers from off-column distractors, clear a blocked red column above
the blocker, and paint its continuation through the row immediately below the
blocker. Ordinary inputs retain the canonical generator's varied dimensions,
marker counts and blocker/distractor profiles.

The prototype accepts the common domain where both directions are lawful:
interior marker columns, no red markers above the guide row, and no gray cells
in any active left/right destination column. The canonical checker alone is
insufficient for this stronger domain. The production checker is not changed.

Input sampling depends on `input_seed`, never on the hidden direction. Paired
directions with the same input seed use exactly the same inputs and ordering.
All demonstration/query inputs within an episode must be distinct.

## Counts and failure behavior

`make_episode(seed, bend_direction=None, demos=2, queries=4, ...)` supports
independent demonstration and query counts, each an exact integer in 1..8.
Omitting the direction chooses it deterministically from the seed.

`sample_inputs(input_seed, count, input_overrides=None, max_attempts=256)`
supports the canonical `grid_h`, `grid_w`, and `branch_profile` overrides.
The retry cap is explicit, bounded to 1..4096, and failure never produces a
shorter batch or clones a pair. Boolean and float counts are rejected.

A fixed 5×6 compact profile has exactly four distinct inputs. Therefore it
cannot provide even one demonstration and four distinct queries. Requests above
known finite support fail before sampling. Other bounded attempts may also fail;
the default variable dimensions supported the retained four-query episodes.

## Label and lesson verification

Every exported label comes from a real Racket bridge. A Python mirror exists
for tests and adapter claims only; there is no fallback when Racket fails.

The certificate fits nine executable candidates to demonstrations only:
the two directions, no bending, bending at all gray cells in either direction,
omitting the row below each bend in either direction, and retaining the source
column above each blocker in either direction. Surviving candidates must agree
on each query. Query labels never select surviving candidates. This is a finite
declared rival check, not uniqueness against arbitrary programs.

Certification recomputes labels and rival evidence; saved certificates are not
authority. It rejects wrong labels, duplicate inputs, mismatched settings or
programs, and forged program/source digests. Source changes require a fresh
process. Verification of an exported batch replays actual Racket execution,
including when an attacker recomputes the manifest after modifying private data.

## Public export and provenance

`write_batch` validates the whole batch before creating its destination.
Public files contain only demonstration inputs/outputs and query inputs. Their
filenames are SHA-256 hashes of the exact serialized visible bytes, computed
with the shared `public_challenge_bytes` and `public_challenge_id` helpers.
Files and manifest rows are sorted by public ID. Duplicate visible challenges
and existing output destinations are rejected.

Settings, seeds, query answers, programs, source hashes and certificates stay in
`private.jsonl`. Seed fields describe generation; they are not used as
certificate authority or public identity. Give only `public/` to a model.

## Promotion interface

`adapter.py` and `promotion.json` provide the owner-facing bounded adapter.
The adapter reuses this sampler and Python mirror to return label claims.
The owner's protected qualification worker must independently execute them.
No prototype inventory, acceptance record, approval hash or training mix was
changed. Qualification and exact-source acceptance remain owner actions.

Retained execution evidence is under `WORK/checks/parametric/run-01/`, with
four episodes: two seeds × two directions, each with two demonstrations and four
queries. The sibling `comparison.json` retains a shared-input setting witness.
