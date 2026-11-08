# Working notes: d59da25908ca

## Baseline findings

- Baseline generator SHA-256:
  `92fe11325a91eb3270902eee0009851fcbbaff7f794dcbe5e121a5e5bb2a49c3`.
- Battery: 6 green, 1 advisory, 5 failed.
- Missing `RULE_HASH`; canonical inputs with length-1/3 negatives were rejected.
- Ordinary samples contained only exact-length-2 positives.
- Override contract produced 11,872 findings over 43,380 draws and accepted an
  unknown key.
- No semantic contract was declared.

## Hypotheses and repair sequence

1. Strongest canonical-fitting rival: recolor every even-length vertical green
   run. Canonical examples expose lengths 1, 2, and 3 but not 4.
2. First repair added a length-4 negative to every scene, truthful axes,
   canonical-compatible validation, semantic hooks, and source-bound tests.
3. Self-review found a new correlation: every generated scene had length 4, so
   “apply the rule only when length 4 is present” fit the production support.
4. Final repair uses a six-slot alternating schedule. Every four-pair lesson has
   two length-4-present and two length-4-absent scenes, all controls 1/3/5, and
   sufficient multiple-target support under every query rotation.

## Final identity and evidence

- Generator version: `2.1.0`.
- Generator SHA-256:
  `e94f4f3d003f161ebed1561b56f39a1f4a186d5270039164cadbc1c1e40f4a5b`.
- Racket authority unchanged; `RULE_HASH = ae357e8ac60c`.
- Task tests: 15/15 passed.
- Battery: 12/12 green.
- Census: 300 lessons, 1,200 rotations, zero ambiguity, 1,164 unique inputs.
- Post-repair exposed solve: revision 1, 3/3 visible examples.

See the packet-root `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json` for commands,
limitations, and exact evidence paths. Imported associated notes remain in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e94f4f3d003f161ebed1561b56f39a1f4a186d5270039164cadbc1c1e40f4a5b`.

# DECISIONS — d59da25908ca

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket rule unchanged and pin `RULE_HASH = "ae357e8ac60c"`.

**Original rationale.** Unknown; the baseline omitted the required pin.

**Reason.** Canonical outputs already implement the coherent rule “recolor each
maximal vertical green run iff its length is exactly two.” Rule smoke and
canonical execution were green before repair, so the defect was in the Python
generator and teaching distribution, not authority.

**Rejected alternative.** Changing the Racket rule to match the baseline’s
all-positive distribution. That would erase valid canonical negatives and
change task semantics to conceal a generator defect.

**Probe.** Canonical pairs are checked by `test_rule_hash_and_canonical_authority_are_pinned` and the final battery’s rule-smoke/authority-sync stages.

## D2 — Remove fake axes; advertise only exact controls

**Choice.** Replace the baseline’s overlapping, singleton, and ignored axes with:

- `grid_h`: integer 5–10
- `grid_w`: integer 7–10
- `n_targets`: integer 1–2

Unknown keys, invalid types, out-of-range values, and invalid difficulty tokens
raise `ValueError`.

**Original rationale.** The baseline offered axes such as `run_length`,
`palette_size`, `position_bias`, and `texture`; their intended rationale was not
recorded. Measured behavior showed singleton domains, dead texture values,
overlap with negative fixtures, and silent mismatch between requested and
observed dimensions.

**Reason.** These are the only independent production controls that are both
lawful and exactly observable. Width 7 is the minimum advertised production
width that can place the maximum four separated columns; `self_check` still
accepts lawful width-6 canonical inputs.

**Rejected alternative.** Retain decorative axes and special-case the override
checker. That would preserve unverifiable controls instead of a truthful API.

**Probe.** `test_all_exact_axis_boundary_combinations_are_constructive_and_observable` covers every joint boundary combination in all four difficulty modes.

## D3 — Use 1–2 exact-length-2 targets

**Choice.** Generate one or two positive target runs per scene.

**Original rationale.** The baseline varied run count but made every run a
positive; no rationale for that all-positive grammar was recorded.

**Reason.** At least one target is necessary to demonstrate the transformation.
Occasional two-target scenes refute the plausible rival “transform only the
first exact-two run” without consuming excessive width.

**Rejected alternatives.** Always one target leaves the first-only rival open;
three or more targets reduce room for contrasting negatives on canonical-sized
grids.

**Probe.** The schedule and semantic-witness tests require multiple-target support in every complete lesson after any query holdout.

## D4 — Alternate length-4 presence instead of making it universal

**Choice.** Use a six-slot pattern with length 4 present on alternating slots.
Every four consecutive pairs therefore contain exactly two scenes with length 4
and two without it.

**Original rationale.** The baseline had no length-4 negatives. The first repair
put one in every scene to defeat the strongest canonical-fitting shortcut.

**Reason.** Length 4 is the smallest unseen even-length counterexample to
“recolor every even-length run.” Alternating it preserves that witness while
also defeating the newly discovered distribution rival “apply the rule only
when length 4 is present.”

**Rejected alternatives.** A single length-4 witness per four-pair lesson fails
when that pair is held out as query. Universal length 4 creates a context
correlation. Random presence can leave witness-free windows.

**Probe.** `test_six_slot_schedule_breaks_length4_conditioning_in_every_four_pair_window` checks all cyclic starts; the census holds out every pair once.

## D5 — Rotate odd controls 1, 3, and 5 deterministically

**Choice.** The six control sequence is `1,3,5,1,3,5`.

**Original rationale.** Unknown; the baseline emitted exact-two runs only.

**Reason.** Every four-pair window contains all three odd controls. This teaches
that singleton and longer odd runs remain unchanged and refutes “all runs” and
“length at least two” rivals under every query rotation.

**Rejected alternatives.** Random controls can produce homogeneous lessons;
only one odd length overfits the boundary; adding more run lengths would widen
the grammar without evidence of teaching value.

**Probe.** Cyclic-start regression plus the 300-lesson rotated census.

## D6 — Anchor canonical profiles while retaining scale variation

**Choice.** Four of six schedule slots use 5x7 or 7x7 defaults; the two length-5
slots use difficulty-scaled broad sizes up to 10x10.

**Original rationale.** The baseline had difficulty-specific dimensions but did
not honor the full advertised override domain.

**Reason.** Canonical-size anchors guarantee profile-floor support and keep the
rule visually simple. Broad slots preserve height/width diversity and exercise
longer controls.

**Rejected alternative.** Uniformly broad random dimensions risk starving the
strict canonical envelope in small battery samples.

**Probe.** Final profile-floor, diversity, and exact override stages are green.

## D7 — Keep foreground components separated vertical runs

**Choice.** Select columns at least two apart and randomize each run’s start row.

**Original rationale.** The task’s canonical objects are vertical runs; the
baseline also used vertical placements.

**Reason.** Separation makes maximal-run boundaries unambiguous and focuses the
lesson on run length rather than component segmentation. Random rows and column
assignments prevent fixed-position shortcuts.

**Rejected alternative.** Touching runs or multi-column components would add an
orthogonal connectivity problem not supported by the authority examples.

**Failure mode.** The resulting domain does not train horizontal runs, connected
shapes, or run lengths beyond five; this is an explicit limitation, not a claim
about the full ARC universe.

## D8 — Separate lawful-input validation from production teaching guarantees

**Choice.** `self_check` accepts the public lawful grammar: rectangular 0/3
grids, separated vertical runs of lengths 1–5, 1–2 targets, and 1–2 controls.
It does not require every production schedule feature on every individual grid.

**Original rationale.** The baseline validator required all green runs to have
length two, which rejected canonical negative examples and accepted a solid 2x2
impostor.

**Reason.** Validators should accept lawful canonical negatives. Teaching
coverage belongs to schedule, semantic, and lesson-level tests rather than a
per-input requirement that would reject valid examples.

**Rejected alternative.** Requiring a length-4 run in `self_check` would reject
canonical and no-length-4 curriculum scenes.

**Probe.** Canonical parity, minimal-impostor rejection, and final self-check stage.

## D9 — Declare executable rivals and witnesses

**Choice.** Add `rule_mirror`, six witnesses, five semantic rivals,
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, and
`lesson_identifiable`.

**Original rationale.** No semantic contract existed.

**Reason.** Future agents and shared tools can execute the contract rather than
infer it from prose. The new context rival records the exact shortcut found by
self-review.

**Rejected alternative.** A prose-only note cannot be source-bound, rotated,
or checked by the census.

**Limit.** The rival set is finite. Passing it is evidence against named
shortcuts, not a proof that no other hypothesis can fit.

## D10 — Keep the repair task-local

**Choice.** Modify the selected generator, its selected tests, summary, and
working notes only. Do not patch either adversarial audit target or shared tools.

**Reason.** Assignment scope requires the audits to remain observational. Shared
process suggestions are separated in `FEEDBACK_TO_CODEX.md`.

## Reusable probes

- Focused tests: `python3 -m pytest -q generators/d59da25908ca/tests/test_generator_d59da25908ca.py` from `repo`.
- Portable selected tests: the `task_tests` command recorded in `RESULTS.json`.
- Full source-bound battery: the final `check --battery` command in `RESULTS.json`.
- Rotated production census: the final `lesson-census` command in `RESULTS.json`.
- Exact shortcut witness: `checks/question/d59da25908ca/`.
