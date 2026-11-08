# Current generator notes: c3052979ff96

## Intended rule and authority

The unique connected color-8 source object is transformed around the unique color-9 pivot. The unique control value maps `1 → identity`, `2 → 90° clockwise`, `3 → 180°`, and `4 → 90° counter-clockwise`. Transformed cells are stamped color 2 over a copy of the input; unrelated cells are preserved unless a red target lands on them. The pinned canonical rule hash is `a9dc0b2876d4`; the selected Racket source remains the label authority.

Version 2.0.0 constructs only lawful in-bounds intended transformations on the four canonical dimension/palette profiles: `11×13/p6`, `12×14/p7`, `13×13/p6`, and `14×14/p6`. Exact controls are available for profile, code, connected source shape, strict source quadrant, and distractor count. Inputs and controls fail closed on unknown, coercive, or out-of-range values.

## Reversed decisions

The prior generator omitted unrelated color-5/6/7 objects from every ordinary sample. That made the wrong rule “delete everything unrelated, then rotate” agree with 59/59 sampled generated labels while failing all 5 canonical pairs. The new default emits 3 or 4 unrelated components and matches canonical palette cardinality; an exact count of 5 remains available only as a non-strict override probe. The executable `strip_unrelated_objects` rival now disagrees on every sampled generated scene (100/100 in `checks/reference-probe.json`).

The prior generator also lacked a pinned rule hash, had dead/singleton metadata axes, and rejected a lawful canonical two-cell source. These were replaced with observable exact controls, canonical acceptance, and strict type/range checks. Geometry generation now retains a deterministic reservoir of at most 64 placements per exact geometry key; this reverses an initial exhaustive cache that was semantically correct but caused override-matrix memory thrashing.

## Teaching schedule and rivals

Canonical pairs use codes 2, 3, and 4 only. Therefore the strongest canonical-fitting rival treats the unseen code 1 as another clockwise turn. A five-pair cyclic lesson schedule emits codes `{1, 1, 2, 3, 4}`. With four demonstrations and one query, every query rotation retains at least one identity demonstration and refutes that rival; every scene also contains preserved distractors, refuting the historical deletion shortcut.

The exact Racket-verified code-1 witness is retained at `counterexamples/strongest-canonical-shortcut.json`. `workspace/reference_probe.py` independently reconstructs the pixel rule, checks both rivals, audits canonical coverage, samples generated cases, and writes source-bound JSON evidence. Focused tests exhaust every declared schedule start and all 75 query rotations across the three difficulty bands.

## Distribution choices

- Source shapes: ten fixed connected polyomino orientations of size 2–4, including all canonical source forms.
- Placement: source lies wholly in one strict quadrant of the pivot; intended target is in bounds and, except for identity, disjoint from the source.
- Distractors: 3–4 ordinary components in colors 5–7, with 2–3 distractor colors selected to realize the canonical palette count. Exact override accepts 3–5.
- Default schedule period: five positions, shifted by seed and difficulty, covering every code, strict quadrant, distractor count 3/4, all four profiles, and all ten shape IDs across seeds.

## Known limits

The generator is a finite constructive grammar, not a proof of the entire natural-language task domain. It does not sample arbitrary connected color-8 shapes, source/pivot alignments outside strict quadrants, arbitrary distractor geometries, or intended source/target overlap. Lesson identifiability is measured only against the two declared executable rivals. The fixed-seed schedule census exhausts the declared five start residues and all query positions at seed 0; it does not certify every seed or every conceivable rival.
## Current reviewer considerations

Source SHA-256: `e919668b35fc70bb9c292e0efa5bf13497e7788c0388ccc7b9abf354ce5bdf55`.

# Decisions for c3052979ff96

## D1 — Preserve the authoritative rule; repair sampling and teaching

**Decision.** Keep the meaning of the selected rule unchanged: rotate the connected color-8 source around the unique color-9 pivot according to control `1..4`, then stamp transformed cells red over the input.

**Reason.** All five canonical pairs and the selected Racket implementation agree on that rule. The observed defects were distribution, lesson identifiability, validation, and metadata defects—not a semantic-rule defect.

**Authority action.** I used the official hash-bound authority-sync mechanism only to remove a nonsemantic comment from selected `racket_target.target_code`, making it exact-text synchronized with canonical `program_solution`. Archival `raw_code` was left untouched. Evidence: `checks/authority-sync-proposal.json` and `checks/authority-sync-v1/result.json`.

**Rejected alternative.** Rewriting the canonical program or broadening it to a new task. That would silently replace authority rather than repair the assigned generator.

## D2 — Use a canonical-profile constructive grammar

**Decision.** Ordinary samples use exactly the four canonical dimension/palette profiles: `11×13/p6`, `12×14/p7`, `13×13/p6`, and `14×14/p6`.

**Reason.** The prior sampler drifted away from canonical appearance and omitted unrelated objects. A constructive grammar guarantees legal in-bounds labels while restoring canonical profile support in every difficulty band.

**Rejected alternatives.**

- Arbitrary canvas sizes: lawful under a broad reading, but unsupported by canonical visual evidence and unnecessary for this repair.
- Pure rejection sampling over unconstrained random scenes: slower, harder to make every exact override observable, and more likely to create sparse or accidental teaching support.

**Probe.** Final profile-floor and distribution stages are green in `checks/after-v1/`; all five canonical inputs pass the repaired validator.

## D3 — Restore unrelated objects instead of deleting the branch

**Decision.** Every ordinary draw contains 3 or 4 unrelated components in colors 5–7; exact override supports 3–5. Distractor colors are chosen so the resulting palette cardinality matches the selected canonical profile.

**Reason.** The prior ordinary sampler made the wrong rule “delete colors 5/6/7, then rotate” agree with generated labels. Canonical examples preserve unrelated content. The repaired distribution makes that behavior visible in every ordinary sample.

**Rejected alternatives.**

- Continue sampling no distractors and rely on canonical examples: generated training lessons would still teach the shortcut.
- Always use five distractors: useful as an exact-control edge case, but outside the strict ordinary canonical-profile distribution.

**Probe.** `strip_unrelated_objects` disagrees on 100/100 generated draws in `checks/reference-probe.json` and is refuted in every lesson census.

## D4 — Teach the unseen identity branch with redundancy

**Decision.** The five-position code schedule is `(1,2,1,3,4)`, so each complete lesson has codes `{1,1,2,3,4}`. Lessons contain four demonstrations and one query.

**Reason.** Canonical pairs contain only codes 2, 3, and 4. Therefore the plausible rival `code_one_is_clockwise` fits all five canonical pairs. One code-1 pair per lesson would disappear when held out as the query; two guarantee that at least one identity demonstration remains for every query rotation.

**Rejected alternatives.**

- Schedule `(1,2,3,4,…)` with only one identity example: insufficient under arbitrary query holdout.
- Declare production order mandatory and skip query rotations: downstream assembly permits arbitrary one-pair holdout, so this would hide a real teaching defect.
- Add more than five pairs: unnecessary once the minimal redundant schedule passes every cyclic start and query position.

**Probe.** `checks/lesson-census-period-s0.json` exhausts all five declared starts at seed 0 across three bands and all 75 query rotations. `checks/lesson-census-random-100.json` adds 300 random lessons and 1,500 rotations.

## D5 — Advertise only exact, observable controls

**Decision.** Replace dead/singleton metadata with five exact axes: profile, code, source shape, strict source quadrant, and distractor count. Reject unknown keys and coercive or out-of-range values.

**Reason.** An override contract is useful only if each advertised value can be requested, observed from the generated grid, and checked. Strict types also prevent booleans from silently acting as integers.

**Rejected alternative.** Preserve legacy labels for compatibility while leaving them ignored. That would keep the checker and future authors dependent on false metadata.

**Probe.** Task-local tests cover every value and strict rejection; the final override stage is green. `observe_overrides()` recovers each requested value from pixels.

## D6 — Bound geometry caching without losing deterministic support

**Decision.** Keep at most 64 deterministic placements per exact `(height,width,shape,code,quadrant)` key.

**Reason.** The first correct implementation cached every legal placement. The full Cartesian override probe touched hundreds of keys and retained roughly a million nested tuples, causing memory thrashing and an apparent timeout. A stable reservoir preserves positional variety and deterministic replay while bounding memory.

**Rejected alternatives.**

- Disable caching entirely: repeats expensive enumeration throughout the battery.
- Keep the exhaustive cache and raise timeouts: treats a local space leak as infrastructure trouble.
- Use Python `hash()` for reservoir replacement: process-randomized and therefore not reproducible.

**Probe.** All exact-control tests and the final override stage pass under the bounded implementation.

## D7 — Keep independent semantic tooling beside the generator

**Decision.** Add `workspace/reference_probe.py`, tests for it, and a compact retained counterexample.

**Reason.** Future agents need a way to reconstruct the rule from pixels, verify canonical parity, execute declared rivals, and produce a disagreement witness without trusting the generator’s own label helper. The tool is task-local and runnable from the repository root.

**Artifacts.**

- `repo/generators/c3052979ff96/workspace/reference_probe.py`
- `repo/generators/c3052979ff96/tests/test_reference_probe.py`
- `repo/generators/c3052979ff96/counterexamples/strongest-canonical-shortcut.json`

## D8 — Shape and placement scope

**Decision.** Use ten fixed connected source orientations of size 2–4, including every canonical form. Place the source wholly within one strict quadrant of the pivot; require the transformed target to be in bounds and, except for identity, disjoint from the source.

**Reason.** This supplies controlled geometric diversity and all four rotational cases while keeping construction and exact override observation reliable.

**Rejected alternatives.** Arbitrary polyominoes, axis-aligned source/pivot cases, and source/target overlap. These may be lawful under a broader domain, but canonical evidence does not require them and they introduce extra geometric ambiguities unrelated to the assigned defect.

## D9 — Report finite evidence honestly

The retained rival checks cover the two strongest task-specific alternatives identified here, plus shared generic rivals searched by the census. They do not prove unique induction against every imaginable program. Fixed-seed schedule enumeration covers all declared starts and query positions only at seed 0; the random census expands support but does not exhaust all seeds. Approval and training admission remain unchanged.

## D10 — Add a native causal parametric relay without changing production

**Decision.** Keep `rotation_only` byte-for-byte equal to the canonical Racket authority and add one task-local `relay_hit_color` setting. Step A computes the code-controlled rotated footprint and finds the unique color-5/6/7 cue orthogonally adjacent to exactly one target cell. Step B stamps the footprint red and recolors that cue plus its same-colored separate payload red. Settings share identical inputs for each seed/count.

**Teaching choice.** The first two demonstrations both use control 1 and the same source quadrant while selecting different relay colors. This preserves the previously repaired identity branch and defeats code-1-as-clockwise, code-only, quadrant-only, fixed-color, payload-size, all-color, and first-target-cell shortcuts. Four queries cover controls 1–4; the final query is a 30×30 all-boundary stress case.

**Evidence.** `workspace/parametric/audit.py` is a reusable finite-rival audit. The retained run covers 96 episodes over seeds 0–15, demo counts 2/3/6, both settings, all control codes, all relay colors, and 30×30 stress. Focused tests execute both setting programs through protected Racket. Native qualification and the wrong-intermediate causal replay are packaged under `checks/c3052979ff96/qualification/` and `checks/c3052979ff96/causal/`; sequential public projection is checked separately.

**Limit.** This is reviewer-ready prototype work, not a production-generator replacement, universal identifiability proof, measured training gain, owner acceptance, or training admission. Exact integrated live bytes still require owner qualification, witness replay, and native acceptance.
