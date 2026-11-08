# Working notes: d4171e13daca

## Review revision 3.1.0 — query-rotation curriculum repair

Assignment `review-da69620e635ad07a` used retained note `GNOTE-003250`
(`canonical_shortcut_rebuttals`) as a lead, then remeasured the pinned 3.0.0
source. The canonical Racket authority and `RULE_HASH = 17513141906a` were not
changed.

### Defect

The four-profile schedule made its ordinary ordered four-demonstration window
identifiable, but five-pair lesson assembly can hold out any one pair as the
query. Holding out the only inset profile let `canvas_distance` survive; other
rotations could remove the only shallow, non-square, or off-center witness.
The baseline 12-stage battery was green because its rotation check was a small
non-exhaustive diagnostic. A new every-position regression reproduced the
failure before source changes (`checks/task-tests-red/`: 2 failed, 20 passed).

### Repair

The ordinary schedule is now a five-profile cycle:

1. `2 / canonical / edge`
2. `3 / offset / inset`
3. `4 / canonical / edge`
4. `5 / offset / edge`
5. `2 / offset / inset`

Profiles 1 and 4 (zero-based) are redundant shortcut guards. On the ordinary
scheduled path they are deterministically non-square and off-center when a
random draw would otherwise lose those witnesses. Explicit overrides remain on
the general constructive path and retain the advertised Cartesian controls.
`EXAMPLES_NEEDED` remains four: every set of four demonstrations obtained by
holding out one of the five labeled pairs still contains a shallow case, a deep
case, an inset case, and evidence against frame recentering.

### Retained TDD failures

- Initial rotation regression: `checks/task-tests-red/` — the canvas-distance
  rival survived when the sole inset pair was the query.
- Broadened seed regression: `checks/task-tests-red-nonsquare/` — some rotations
  lacked a non-square outer frame.
- Second broadened regression: `checks/task-tests-red-recenter/` — a non-square
  frame could still be centered, so `recenter_frames` survived.

Each failure was retained before the corresponding minimal schedule guard was
added. The selected tests also stopped importing the repository-only
`scripts.*` helper and now use portable `reviewer_support` discovery.

### Final finite evidence

Final generator SHA-256:
`3641b1ed24f6b0a0c3c2c98a458520d66206593b803e079a0b92e28720848978`.

- Full battery: 12/12 green.
- Portable task tests: 22/22 passed.
- Source-bound census: 300 lessons (100 per band), 1,500 labeled pairs,
  1,500 single-pair query rotations, 1,007 unique inputs, zero declared-rival
  ambiguity, materialization errors, hook warnings, or scoring errors.
- Exhaustive schedule probe: seeds 0..49, starts 0..9, all three bands;
  1,500 production windows and 7,500 held-out-query rotations over 1,306 unique
  generated inputs, with zero failures against the five declared competitors.
- Fresh visible-only solve: 4/4 demonstrations passed; earlier generator exposure
  was disclosed and no reference/private label was consulted during that solve.

These finite checks distinguish the declared rivals over the tested sampler and
schedule. They do not prove universal induction against undeclared hypotheses.
The extra non-square/off-center guard narrows two teaching profiles deliberately,
but canonical, square, centered, edge, inset, shallow, and deep support remains
elsewhere in the cycle, and exact overrides remain observable.
## Current reviewer considerations

Source SHA-256: `3641b1ed24f6b0a0c3c2c98a458520d66206593b803e079a0b92e28720848978`.

# Decisions and rationale

## D1 — Treat arbitrary single-pair query rotation as the assembly contract

The selected task uses four demonstrations and one query. Retained note
`GNOTE-003250` warned that inset and off-center examples are needed to refute
canonical-fitting shortcuts, but the pinned 3.0.0 source only guaranteed those
witnesses in its ordinary ordered four-profile window. I treated any of the five
labeled pairs as a possible query because the shared census supports
`--rotate-query` and the task's lesson hook is evaluated for each labeled query.

Alternative: document an ordered-only curriculum. Rejected because the existing
assembly and assignment explicitly exercise query rotation, and because the
small finite profile cycle makes complete coverage cheap.

## D2 — Add one redundant profile instead of increasing demonstration count

The root defect was witness cardinality: a four-profile cycle had exactly one
inset example and could lose it to the query. I changed the cycle to five
profiles while keeping `EXAMPLES_NEEDED = 4`, adding a second
`2 / offset / inset` profile. Thus every four-of-five demonstration set retains
both a shallow case and an inset canvas-distance rebuttal.

Alternatives considered:

- Increase the number of demonstrations to five. Rejected as unnecessary lesson
  length and because it would avoid rather than repair the five-pair holdout.
- Resample only when a chosen query removes a witness. Rejected because it makes
  teaching quality dependent on downstream assembly order and obscures
  determinism.
- Keep four profiles and rely on random geometry. Rejected by the exact retained
  failure in `checks/task-tests-red/`.

## D3 — Guard non-square and off-center evidence independently

After the first minimal schedule repair, broader TDD seeds exposed two distinct
facts: a rotation could lack any non-square outer frame
(`checks/task-tests-red-nonsquare/`), and a non-square frame can still be centered,
allowing `recenter_frames` to survive
(`checks/task-tests-red-recenter/`). Profiles 1 and 4 therefore receive two
ordinary-path guards: force the outer box non-square only when necessary, and
adjust a margin only when the whole placement would otherwise be centered.

The guards are deliberately limited to unoverridden scheduled examples. Exact
caller overrides continue through the general constructive path, so the repair
does not silently alter requested `frame_count`, `layout_style`, or
`outer_margin`.

## D4 — Preserve the canonical authority

The selected Racket rule already correctly ranks blue components by bounding-box
area; on the lawful nested-frame grammar this is containment depth. All observed
failures were lesson-distribution failures. I therefore kept
`RULE_HASH = 17513141906a` and changed no canonical or Racket file. Authority
sync and rule smoke stayed green in both before and after batteries.

## D5 — Add portable regression and reusable schedule probe

The selected test now holds out every one of five labeled pairs across all three
bands, seeds `(0, 4, 5, 20, 44, 914)`, and starts 0..9. It imports portable
canonical helpers from `reviewer_support`, not `scripts.*`.

`workspace/query_rotation_probe.py` complements the source-bound Racket census:
it iterates the generator's actual declared competitors, every requested cyclic
start, and every query position; records the exact source/version/rule hashes,
profile counts, unique input count, and failures; and exits nonzero on ambiguity.
Its final run covered seeds 0..49, starts 0..9, all bands, 1,500 production
windows and 7,500 rotations over 1,306 unique inputs with zero failures.

## D6 — Evidence policy and limitations

The 300-lesson source-bound census is the authoritative Racket-labeled population:
100 lessons per band, 1,500 pairs, 1,500 rotations, 1,007 unique inputs, and no
ambiguity/error. The exhaustive schedule probe uses the independently parity-
checked Python mirror so it can cheaply enumerate starts. I report both and do
not treat either finite declared-rival result as universal identifiability.

Self-review for new restrictions: the repair intentionally makes two profiles
non-square and off-center, but other profiles retain canonical/edge geometry and
explicit overrides retain every advertised value. The 1,306-unique-input probe,
override battery, and profile floor show the schedule did not collapse to one
literal template; undeclared rivals remain a documented limitation.

## D7 — Solve records

The required blind task 71982ba2b59e was solved before inspecting selected
sources: revision 2 passed 3/3 visible examples and exposure/reference were
recorded `no/no`. The fresh selected-task solve was prepared from final generator
SHA-256 `3641b1ed...8978`; revision 2 passed 4/4 visible examples, earlier source
exposure was recorded `yes`, and no Racket/reference/private labels were
consulted during the solve.

## D8 — Audit disposition

Audit target 5430502683a1 was left unchanged after 449/449 tests and 72-window,
576-rotation declared-rival checks found no issue. Audit target 629ec8fd452e was
also left unchanged, but `AUDIT.md` records a reproduced size-threshold false-hole
shortcut with a lawful selected-Racket counterexample.
