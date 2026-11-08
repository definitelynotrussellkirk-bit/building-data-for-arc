# Working notes: 4ac45a758a2e

## Current rule and authority

Count blue (1) cells to select 0/90/180/270 degrees clockwise; count red
(2) cells to select no horizontal reflection/reflection after rotation.
Normalize the connected magenta (6) template and stamp it in cyan (8) at the
orange (7) bounding-box origin. The canonical Racket rule remains authoritative
and was not changed. `RULE_HASH` remains `6259c8fd93a1`.

## Reversed distribution decision

Version 3.0.0 scheduled template area as
`4 + ((sample_index + band_shift) % 4)`. Because the blue rotation branch is
also `1 + sample_index % 4`, template area perfectly identified the rotation in
every band. On the pinned pre-repair source (`fe43f341a0c59fa6dae4c0e79e92a7c4d8d9dbbd5f081b16502979dd1b474935`),
a dictionary learned from eight demonstrations predicted the query rotation in
96/96 tested cyclic windows (32 starts × 3 bands).

Version 3.1.0 keeps the eight control pairs in every consecutive eight samples
but advances template area independently across repeated profiles. Over 32
indexes, every rotation occurs with every area in `{4,5,6,7}`. Reflection-half
collisions inside each lesson, plus an area phase change at the same-profile
query eight indexes later, prevent template area from replacing blue counting.
Final source SHA-256:
`12d111d5d8d2dc69d0a46d53e8b1e87e896405f91aa157886605711309e7be3a`.

## Guard and evidence

`lesson_identifiable` now reports when a demo-learned template-size lookup also
predicts the query rotation, making the blue control redundant. Focused tests
cover marginal support, all 32 cyclic starts per band, and an intentionally
correlated negative lesson. The reusable probe is
`workspace/probe_axis_proxy.py`; final evidence in
`checks/template-size-orthogonality.json` covers 96 windows with zero surviving
proxies.

The portable task tests also switched from a fixed `Path.parents[...]` guess to
`reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` after the
isolated task-test runtime exposed that path assumption.

## Verification and limits

- Final focused task tests: 13/13 passed.
- Final battery: 12/12 stages green.
- Production census: 300 ordered lessons (8 demos, query at +8), 0 ambiguities,
  0 hook warnings, 0 scoring/materialization errors.
- Rotated-query diagnostic: 2,700 rotations, 0 named-rival ambiguities, but
  2,100 hook warnings because moving a unique control pair from the eight demos
  violates the deliberate direct-pair-coverage contract. Arbitrary query
  rotation is therefore not claimed.

The finite rivals and proxy probe do not prove unique induction against every
possible hypothesis. No `LESSON_SCHEDULE_PERIOD` is declared: the targeted
32-index axis probe is exhaustive for the repaired area/control schedule, while
other layout schedules and keyed random shapes have different cycles.

### Owner tool correction

The returned axis-proxy CLI was observed overwriting an existing report with
`--out`. It now refuses existing files and symlinks before generation and uses
exclusive creation after generation. Five CPU controls cover regular output,
valid/broken symlinks, a fresh report and a late-created output. Generator/rule
bytes and the reviewer-reported semantic results are unchanged.
## Current reviewer considerations

Source SHA-256: `12d111d5d8d2dc69d0a46d53e8b1e87e896405f91aa157886605711309e7be3a`.

# Decisions

## D1 — Treat template area as a teaching shortcut, not harmless variety

**Original choice.** Template area used the same modulo-4 phase as the blue
rotation count, shifted only by difficulty band. The likely rationale was even
coverage of sizes 4–7.

**Probe.** The pre-repair task tests and the reusable axis-proxy probe learned a
`template_cells -> rot_count` dictionary from each eight-demo lesson. It
predicted the query in 96/96 cyclic windows (32 starts in each of three bands).
The pre-repair 12-stage battery was green, so existing generic gates did not see
this adaptive cross-axis shortcut.

**Decision.** Repair the distribution. Correct labels are insufficient when a
nonsemantic axis can replace the intended control.

## D2 — Use an orthogonal deterministic schedule rather than random area

**Chosen schedule.** Keep the existing eight-residue `(rotation, reflection)`
order. Let each repeated eight-sample cycle advance area phase, with an
additional reflection-half offset. This gives each rotation all four areas over
32 indexes and creates conflicting area/rotation examples inside ordinary
lessons.

**Why deterministic.** It gives exact support guarantees and reproducible
cyclic-start tests. Pure random sampling was rejected because a small lesson
could still accidentally correlate area with rotation and would require
resampling or probabilistic acceptance.

**Rejected alternative.** Changing the blue or red controls would alter the
teaching grammar without need. The authoritative rule and control strips were
already correct.

## D3 — Add an adaptive lesson guard

A static list of fixed semantic rivals cannot express “learn a lookup from this
lesson's nuisance axis.” `lesson_identifiable` now explicitly fits the
area-to-rotation mapping on valid demos and rejects the lesson when that mapping
also answers the query. A focused negative lesson proves this guard fires.

This guard is intentionally narrow and causal to the reproduced defect. A
shared generic axis-proxy gate is recommended separately in `F1` rather than
adding unrelated task-local heuristics.

## D4 — Keep eight ordered demonstrations and the +8 query policy

The task has eight control combinations. Every consecutive eight samples still
covers all of them; the normal query repeats a demonstrated control pair at
`start + 8` while changing template area. In a 300-lesson production census,
all 300 lessons had no declared ambiguity or hook warning.

Arbitrary query rotation is not supported by the stricter direct-coverage hook:
2,100/2,700 rotated positions removed the query's unique pair from the demo
set. This is documented as an ordered-curriculum limitation, not hidden behind
the production pass. Relaxing direct coverage was rejected because the current
downstream assembly does not require arbitrary query positions and the stronger
contract is useful.

## D5 — Do not declare a global lesson schedule period

The repaired template/control relation has a 32-index cycle, but dimensions and
canonical-layout choices have their own schedules and shapes/placements are
keyed random. Declaring `LESSON_SCHEDULE_PERIOD = 32` would overstate what
repeats. Instead, `probe_axis_proxy.py` exhausts the relevant 32 starts directly
for the two axes at issue.

## D6 — Repair portable test discovery

The existing focused tests assumed a fixed source depth with
`Path(__file__).resolve().parents[1]`. The isolated task-test runtime moved the
file and failed before executing semantic tests. The tests now use the supplied
portable canonical-data helpers. This is a test-infrastructure repair only; no
canonical data or frozen fixture changed.

## D7 — Preserve genuine solve evidence

The post-repair visible-only solve kept its first execution failure: `_normalize`
consumed a generator twice. Revision 2 materialized the iterable and matched all
8 visible examples. Earlier rule exposure is declared `yes`; no reference or
masked query label was consulted during the solve.
