# Connection clearance before or during drawing

This separate native prototype preserves the selected canonical program exactly
in `canonical.rkt`. The production generator remains version 3.0.0. Reviewer
qualification is distinct from fresh owner acceptance of the integrated source;
neither this workspace nor its private examples grant training admission.

## Rule and causal state

In both settings, read endpoint locations from the original input. Process
nonzero colors in ascending numeric order. A color is eligible only if it occurs
exactly twice and the two cells share a row or column. Its segment is inclusive;
adjacent endpoints have an empty interior and therefore pass clearance.

| `clearance_stage` | Surface used to test a segment's interior |
|---|---|
| `input` | Original input; exact canonical default |
| `painted` | Original input plus accepted earlier segments |

Output starts empty. An accepted segment paints its color into output. In the
alternative, it also updates occupancy for later clearance checks. Rejected
segments do not paint either surface. Invalid singletons, triples and unaligned
pairs remain original occupancy blockers but are not copied into output.

The new setting has a concrete evolving-state dependency: A accepts and paints
earlier paths; the intermediate is the resulting occupied grid; B tests later
paths against that grid. In an A-B-C crossing chain, A blocks B, but rejected B
does not block C. A fourth higher-color path revisits A while avoiding C, teaching
that older accepted paths remain occupied. Painting every candidate, regardless
of acceptance, produces a different result. Testing only the original input also changes the result.
This depends on which earlier paths actually succeeded, not just their presence.

The protected runtime's `grid-colors` sorts numeric color values. This matters
when paths cross: the canonical input setting draws all initially clear paths,
so higher colors overwrite lower ones at crossings. In the painted setting,
lower colors can prevent later paths from being drawn at all. The pre-existing
independent probe assumed reading order, which was invisible in the old
disjoint-path sampler. This prototype reuses reviewed segment geometry and
implements the protected numeric order explicitly.

The supplied public-evaluation focus `142ca369` motivates line interactions and
visible context influencing continuation. That is a design inspiration, not
verified ancestry or a claim that this prototype implements the focus task.

## Input grammar and count contract

The native grammar accepts exact-list rectangular integer 0..9 grids with both
axes 3..30. Color 0 is background. Multiplicities and positions are unrestricted:
all-zero inputs, non-pairs, unaligned pairs, adjacent endpoints and entirely
blocked puzzles are legal and total, including empty outputs. There are at most
nine candidate colors. The sampler constructs informative nondegenerate lessons
inside this broader grammar; it does not claim to sample every admitted grid.

`adapter.generate(seed, settings=None, demos=3, queries=4)` supports exact integer
seeds 0..2**63-1, demonstrations 3..6 and queries 1..4. An omitted setting uses seed
parity once per episode. Explicit settings share their input banks. The complete
six-demo/four-query banks use independent local random streams, then counts select
prefixes. The full query bank is shuffled before slicing. Returned lists are
fresh and global random state is preserved.

The mandatory teaching prefix covers crossing priority, original-input blockers,
empty-first output and an accepted-rejected-accepted chain. Numeric priorities
must be distinguished from spatial, orientation and length shortcuts. Optional
demonstrations and four novel queries extend the tested geometry and count range.
The minimum query is 3x3. A 30x30 nine-pair query spreads long paths across the
canvas. Pair-only input is necessarily sparse (18 endpoints for nine pairs);
report output occupancy and span separately from input occupancy.

The mandatory scenes are a four-candidate crossing chain with singleton-blocked and invalid
colors, a priority contrast with endpoint blocking and an adjacent pair, and a
clear-only canonical-role anchor. Complementary off-span triples prevent the
first/last-of-many shortcut from hiding behind a straight triple's own middle
blocker after rotation. Optional scenes include an entirely empty output, a mesh
and border paths. Query roles before D4 transformations are 3x3, 18x20, 24x26 and
30x30. At the maximum seed, protected execution measured 236 occupied output
cells for `input` and 144 for `painted` on the 30x30 query; both span the full
canvas and touch all four edges. Those measured counts describe that case,
not a universal constant across seeds.

Independent review found that the original three-candidate chain left a memory
shortcut untaught: remembering only the latest accepted path fit all three demos
at seeds 0 and 17, then disagreed on the 30x30 queries. The fourth candidate
strengthens the same demonstration; the count stays three. The original protected
failures remain under `checks/9686a12edc93/self-review-racket.json`, and the compact
4x5 reproduction under `memory-regression.json` changes exactly three output
cells. Current-source replay is kept separately from those historical reports.

## Reproduce the private evidence

Run from the packet's outer directory; payload paths resolve in `WORK/repo`.
Use fresh receipt and output names on reruns:

```sh
WORK/.venv/bin/python review.py run --receipt checks/9686a12edc93/recheck.json \
  python3 -m pytest generators/9686a12edc93/tests/test_native_family.py \
  generators/9686a12edc93/tests/test_native_sampler.py \
  generators/9686a12edc93/tests/test_native_adapter.py -q

WORK/.venv/bin/python review.py run --receipt checks/9686a12edc93/rival-recheck.json \
  python3 generators/9686a12edc93/workspace/parametric/audit.py \
  --seed 0 --seed 17 --out ../checks/9686a12edc93/rival-recheck

WORK/.venv/bin/python review.py run --receipt checks/9686a12edc93/requalify.json \
  python3 -m arcpuzzles parametric qualify 9686a12edc93 --seed 0 --seed 17 \
  --demos 3 --queries 4 --out ../checks/9686a12edc93/requalification --summary
```

The generic auditor reads the contract's demonstration count when omitted. It
fits every rival to demonstrations before inspecting query disagreements,
executes through protected Racket, caches exact program/input pairs and retains
source hashes. A finite-consistent rival is recorded as such. Execution errors
never count as teaching success. The boundary probe uses maximum request counts
and seed, records actual occupied cells, content spans and boundary contacts,
and handles empty outputs. Each probe requires a new evidence destination.

Public projection uses the packet's permutation-aware exporter. Keep its complete
bundle and directory listing controller-only: the user receives one file with
demonstrations and one query input at a time. The private manifest pairs shuffled
source indices with view IDs; settings, programs, answers, future queries, order
and presentation seed stay private. Public names hash only their visible bytes.
Stopping after one query uses the same complete-bank presentation's first turn.
The public probe checks this identity, input/answer pairing, hidden-field and
presentation-seed independence, and rejection of temporary corruptions. It does
not claim an additional Racket replay.

The native inventory binds current source and bounded evidence. Qualification
and counterfactual replay do not prove all-seed success, unique induction among
all programs, or measured learning improvement. Owner acceptance remains pending.
