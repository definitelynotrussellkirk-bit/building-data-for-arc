# Working notes: 371eb0221101

## Selected rule and authority

The selected canonical rule is unchanged: rotate every monochrome connected
3-cell L object 90 degrees clockwise inside its tight 2×2 bounding box,
preserving its color and bounding-box anchor.  `generator.py` pins canonical
`RULE_HASH = "27c74d38508a"`; no Racket authority file was edited.

## Repair decision

The imported sampler advertised broad controls but did not honor them, could
silently place fewer objects, and its validator accepted grids outside the
stated L-triomino domain.  The selected repair replaces that contract with four
pixel-observable exact controls only: `grid_h` 7..14, `grid_w` 7..14,
`n_blobs` 2..4, and `n_colors` 1..2.  A stride-3 constructive lattice guarantees
all Cartesian combinations, including four separated objects on 7×7.  The
validator now checks rectangular integer grids, dimensions, object/color
counts, exact tight 2×2 L structure, and an eight-neighbor one-cell moat.

The previous implicit color choice was canonical-looking color 6.  That choice
was reversed because every labeled canonical example uses only color 6, making
“rotate color 6 only” the strongest plausible shortcut.  One-color generated
cases now deliberately choose a non-6 color, and two-color cases sample two
colors from 1..9.  Thus every generated input contains a non-6 object and
refutes the shortcut.  The exact retained witness is
`counterexamples/rotate_color_six_only.json`; its selected Racket output is
bound in `checks/shortcut-witness/racket.json`.

Canonical shape support is retained by weighting the observed 8×10, 9×9, and
7×11 profiles without restricting exact overrides.  Generated lessons use
three demonstrations followed by one query; declared production and all query
rotations were non-ambiguous against the color-6 rival in the retained
300-lesson census.  This is finite declared-rival evidence, not a proof against
all possible hypotheses.

## Parametric assessment

The retained `workspace/parametric/prototype.py` still implements its original
fixed `quarter_turns` 1/3 experiment. The new native `adapter.py` reuses those
exact programs and adds `rotation_rule=color_count`: count monochrome L objects
of each color, then rotate every L by its color's count modulo 4. The clockwise
default remains byte-for-byte canonical; production source and authority did
not change.

The separate native grammar supports scale 1/2 Ls, 2..36 objects, 1..4 objects per
color, and 7..30 canvases. Counts are independent: 2..6 demos and 1..4 queries, with
three/four defaults. The 30x30 query has 25 objects/300 occupied cells; 21 objects
change orientation under the count rule. All labels are protected-Racket checked
in qualification and the bounded audit.

The first two demos retain all geometry while recoloring one remote object:
counts 1,2,3,4 become 1,1,4,4. Four locally unchanged objects now rotate differently.
Mixed scales rule out pixel-count substitutes; the missing counts rule out
count-rank substitutes. The 44-hypothesis finite self-audit tests these teaching
choices before queries. It demonstrates contextual gating, not iterative
state simulation or universal uniqueness. The public projection exposes one
query input and no hidden parameters, answer, later input or total-count hint.

The first implementation allowed a column-only counting rival at seed 121.
The current sampler places the four count-4 objects in a 2x2 rectangle, making
row/column counts 2 and distinguishing them from the three intended turn counts.
The regression first failed, then passed after this constructive repair.

The runnable audit and exact commands live in `workspace/parametric/README.md`.
Current evidence is `workspace/parametric/evidence/current/self-review-summary.json`
and returned `checks/371eb0221101/`. The prior two-seed prototype receipts remain
historical. Native qualification, causal replay and exact-source owner acceptance
remain separate: this return prepares a ready artifact; the owner must requalify
and accept the integrated source. No training activation is requested.

## Known limits and open findings

- The sampler intentionally covers only isolated tight L-triominoes; arbitrary
  polyomino rotation is outside this generator contract.
- Identifiability was checked against the declared color-6 shortcut over a
  finite production census; undeclared rivals remain unknown.
- A larger eight-seed parametric evidence run was interrupted by repeated
  Racket bridge startup cost after six seeds; the complete two-seed run covers
  both parameter values and is retained separately from that interruption.
  This is historical legacy evidence, separate from the completed native audit.
- Prior associated notes were empty, so no earlier return was used as a factual
  measurement of the selected baseline.
## Current reviewer considerations

Source SHA-256: `4e2a90e07a476a026815fe0332aeee45f7481ca8bc7540419eea5ce0a91946b8`.

# Decisions: 371eb0221101

## D1 — Replace the inherited axis surface instead of patching it piecemeal

**Prior choice:** The baseline exposed dimensions, blob/color counts, palette aliases, density/position labels, and degenerate textures. The original rationale is unknown; no prior associated note supplied evidence for those choices.

**Decision:** Keep only four exact, pixel-observable axes: height, width, object count, and distinct nonzero-color count.

**Alternatives considered:**

1. Preserve every inherited name and add special handling. Rejected because several values were aliases or labels with no observable alternative, and ordinary/degenerate domains overlapped.
2. Mark ineffective axes diagnostic. Rejected because they did not contribute a needed task distinction.
3. Exact minimal surface. Selected because each value can be recovered from returned pixels and the full Cartesian product is constructively realizable.

**Probe/evidence:** Baseline lint/defect/override reports under `checks/before/`; final 15,660-draw override matrix under `checks/after/checks/371eb0221101_after_override.log`.

**Failure mode/limit:** The narrower API intentionally drops arbitrary texture knobs; future extensions should add an axis only after defining distinct legal pixel outcomes and an observer.

## D2 — Use a constructive stride-3 placement lattice

**Prior choice:** Random trial placement could exhaust attempts and return fewer objects than requested. The reason for accepting silent under-placement is unknown.

**Decision:** Draw origins from a stride-3 lattice, repair offsets that leave too few slots, and sample exactly `n_blobs` positions.

**Alternatives considered:**

- Increase rejection attempts: rejected because it remains probabilistic and weakens exact override semantics.
- Backtracking arbitrary placements: correct but unnecessary for 2×2 objects and the small domains.
- Deterministic lattice: selected for a simple capacity proof and guaranteed one-cell moat.

**Probe/evidence:** All four axis corners across `None/easy/medium/hard` in `tests/test_generator.py`; final override matrix and strict validator battery.

**Failure mode/limit:** The lattice is deliberately sparse and does not represent touching or overlapping objects; those are outside the documented rule domain.

## D3 — Weight canonical profiles without restricting exact controls

**Prior choice:** Baseline defaults produced zero exact and zero envelope profile hits in 60 draws despite accepting the four canonical inputs. The rationale is unknown.

**Decision:** Jointly weight observed dimension pairs `(8,10)`, `(9,9)`, and `(7,11)`, while keeping each exact dimension override legal throughout 7..14.

**Alternatives considered:**

- Use canonical dimensions exclusively: rejected as unnecessarily narrow.
- Independently bias height and width: rejected because it creates many cross-pairs not observed canonically and gives weaker exact-profile support.
- Joint profile anchor plus unrestricted fallback: selected.

**Probe/evidence:** Final profile floor: 30/60 exact, 33/60 envelope, with at least one exact hit in every band.

**Failure mode/limit:** Shape support is based on the current canonical ledger; it does not claim those three canvas sizes are semantically required.

## D4 — Reverse canonical-looking color-6 sampling

**Prior choice:** The baseline/canonical presentation emphasized color 6. The original intent may have been visual fidelity, but no retained rationale exists.

**Decision:** For `n_colors=1`, sample from colors excluding 6. For `n_colors=2`, sample two colors from 1..9. Every generated input therefore contains at least one non-6 object.

**Reason:** All labeled canonical demonstrations contain only color 6, so “rotate color 6 only” is a complete canonical-fitting shortcut. Repeating color 6 in ordinary lessons preserves rather than resolves that ambiguity.

**Alternatives considered:**

- Keep color 6 and merely declare the rival: rejected because generated lessons would not teach against it.
- Force a fixed non-6 color: rejected because it creates another palette shortcut and reduces diversity.
- Permit all colors with rejection until non-6 appears: workable, but direct constructive drawing is simpler.

**Probe/evidence:** `counterexamples/rotate_color_six_only.json`, Racket receipt `checks/shortcut-witness/racket.json`, semantic gate witness 600/600, and 300-lesson census.

**Failure mode/limit:** This repairs the identified palette shortcut; it does not exhaust all shape- or position-based rivals.

## D5 — Make `self_check` the exact documented domain

**Prior choice:** Baseline `self_check` rejected 0/59 destructive mutations and therefore provided acceptance-only evidence.

**Decision:** Validate grid shape/type/range, 7..14 dimensions, 2..4 monochrome 4-connected components, 1..2 colors, exact three-cell tight-2×2 L structure, and Chebyshev separation greater than one.

**Alternatives considered:**

- Check only counts and colors: rejected because malformed polyominoes would be treated as canonical-like.
- Require exact generation provenance: rejected because validators should judge lawful pixels, including canonical inputs, not only samples from one RNG path.
- Exact pixel-domain validator: selected.

**Probe/evidence:** Task-local destructive mutations, canonical acceptance, battery mutation sensitivity, and strict semantic gate 600/600.

**Failure mode/limit:** Some generic color mutations remain lawful because colors are intentionally interchangeable; rejection count alone is not the semantic objective.

## D6 — Declare one verified canonical shortcut, not a list of heuristics

**Decision:** `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and `WITNESS_RIVALS` all point to the executable `rotate_color_six_only` hypothesis, with `non_six_object` as its witness.

**Reason:** A canonical shortcut declaration must actually fit every usable canonical pair. One precise executable rival is more falsifiable than a broad list of partially fitting heuristics.

**Probe/evidence:** Canonical-pair assertions in `tests/test_generator.py`; semantic-gate canonical fit and lesson checks; full census.

**Failure mode/limit:** The contract is rivals-only and does not assert universal lesson identifiability.

## D7 — Preserve 3-demonstration/1-query production assembly and test rotations

**Decision:** Do not add a custom ordered schedule. Assess the actual assembly measured by the shared materializer: three demonstrations and one query. Require the declared rival to be refuted both in production order and when each of the four pairs is held out as query.

**Alternatives considered:**

- Rely on individual witness frequency: rejected because a witness somewhere in the corpus does not prove each lesson teaches the distinction.
- Add a deterministic schedule period: unnecessary because every generated grid itself contains the witness.
- Check production only: rejected because downstream query position may rotate.

**Probe/evidence:** 12-lesson semantic smoke test and 300-lesson `--rotate-query` census.

**Failure mode/limit:** The random census does not enumerate every seed; zero ambiguity is relative to the declared rival.

## D8 — Keep rule authority unchanged

**Decision:** Pin the current canonical hash `27c74d38508a` and make no edit to `shared/data/canonical/puzzles.jsonl`.

**Reason:** Independent Python oracle checks reproduce all four canonical pairs, Racket rule smoke passes, and the defect was in sampling/validation/teaching rather than the transformation.

**Probe/evidence:** Canonical oracle tests, rule smoke, Racket lint, and authority sync/execution parity.

**Failure mode/limit:** Authority sync reports an archival divergent historical raw-code artifact, while the selected authority is synchronized and execution parity passes. No archival artifact was edited.

## D9 — Build but isolate one small rule parameter

**Decision:** Prototype `quarter_turns ∈ {1,3}` chosen once per episode; retain canonical `1` as default and keep all prototype code under `workspace/parametric/`.

**Alternatives considered:**

- Vary arbitrary angles including 0/2: rejected because identity/180° are less aligned with the selected canonical transformation and would broaden the experiment without added value.
- Vary per object: rejected because the assignment asks for a rule parameter chosen once per episode and per-object variation creates a different compositional task.
- Clockwise versus counterclockwise: selected because every L-triomino visibly distinguishes the settings.

**Probe/evidence:** Seeds 0 and 2 cover both values; both exact Racket programs agree with independent mirrors; every retained demo and query differs. Evidence under `checks/parametric/rotation-quarter-turns-v1/`.

**Failure mode/limit:** The first eight-seed command incurred repeated bridge startup and was interrupted after partial output. The complete two-seed run is sufficient to cover both values but not all seeds. Prototype status remains `proposed`.

## D10 — Preserve failed/interrupted evidence and use hash-verified resume

**Decision:** Retain baseline failures, the 59-pass/1-fail portable test, the interrupted after-battery controller receipt, and the interrupted eight-seed prototype collection. Do not overwrite or relabel them as passes.

**Reason:** They document both the repaired defect and the provenance of the final green evidence.

**Probe/evidence:** `checks/task-tests-final/`, `checks/task-tests-final-2/`, `checks/after/result.json`, and both parametric evidence directories. The final battery result explicitly records `resumed: true` and 12/12 green.


## D11 — Replay the packaged patch on a fresh full extraction

**Decision:** Treat package construction as incomplete until its source patch applies to a fresh full extraction of the original packet and the task-local suite passes there.

**Reason:** Working-tree success can hide undeclared files, file-mode drift, or dependencies on local runtime state. The package safety checks in fact caught both an executable-bit drift and transient receipts under `repo/checks`; those were normalized or relocated before replay.

**Probe/evidence:** `checks/replay-candidate/replay.json` records a clean full-packet patch application and exact generator hash; `checks/replay-candidate-task-tests/result.json` and JUnit evidence record 60/60 passing tests in the replayed tree.

**Failure mode/limit:** The replay command verifies the source patch and focused task tests, while the complete 12-stage battery remains bound to the pre-package tree with the same generator/source hashes.
