# Working notes: 71492f8cef8f

## 2026-10-03 review repair

The pinned imported `2.0.1` sampler emitted only two fully enclosed horizontal
rooms, each with one seed of a distinct color. That distribution taught only
the positive branch and could not distinguish “exactly one seed cell” from
“one distinct seed color”; it also omitted empty, multi-seed, edge-open, and
mixed-topology chambers.

The selected `3.0.0` repair uses one observable categorical axis
(`scene_profile`) rather than advertising incidental size/color choices as
exact controls. Four scheduled profiles make the rule branches load-bearing,
including two same-color seed cells in one chamber. `self_check` remains broad
enough to accept canonical lawful inputs, while task tests inspect the stronger
curriculum guarantees on generated draws.

The canonical Racket rule was not changed. Its normalized rule hash is
`f88bd76ccafc`. The reusable `workspace/lesson_window_probe.py` rotates every
position of the deterministic schedule through a two-demo-plus-query lesson and
reads rival/witness declarations directly from `generator.py`.

Known limit: four topology families and a finite declared-rival set are strong
bounded evidence, not proof of universal identifiability. Future reviews should
continue adding low-complexity undeclared rivals and lawful adversarial inputs.
## Current reviewer considerations

Source SHA-256: `98ce27f88bbff0b754fe3a984f4380453e803de24e0c3840eeed894625481ef8`.

# Decisions — 71492f8cef8f

## Scope and source of truth

The assignment was treated as a bounded repair of the selected generator. The
canonical examples and canonical Racket program were the authority. No prior
review return supplied a usable lead; `evidence/associated_notes.jsonl` was
empty. All conclusions therefore come from the pinned baseline source and the
retained before/red evidence.

## `D1` — Fix the distribution, not the Racket rule

**Choice.** Keep the canonical Racket rule unchanged and replace the generator's
input distribution and executable contracts.

**Reason.** The Racket authority already implements the canonical chamber rule
and reproduces all three canonical pairs. The failure was that the baseline
generator sampled only a narrow positive subset. Changing the rule would have
altered correct semantics to accommodate bad data.

**Alternative rejected.** Add special cases to the Racket program for generated
layouts. That would mask the generator defect and risk divergence from the
canonical task.

**Evidence.** Rule hash `f88bd76ccafc`; final rule-smoke, grammar, Racket-lint,
and authority-sync stages are green in
`checks/after-rerun/checks/71492f8cef8f_after_battery_summary.json`.

## `D2` — Define a chamber by connectivity, not by rectangles

**Choice.** Analyze every four-connected component of cells whose value is not
`5`; walls may form closed rooms or regions open to a grid edge.

**Reason.** This is the invariant shared by canonical examples and handles
partial walls without inventing geometric room types. It also makes edge-open
regions a normal semantic case rather than a degenerate exception.

**Alternatives rejected.** Rectangle detection, flood fill only inside an outer
frame, or splitting exclusively at complete wall rows/columns. Each would encode
the imported sampler's layout rather than the puzzle rule.

**Failure modes.** The generator itself still emits four bounded topology
families, so it is not a general maze sampler. `self_check` is intentionally
broader than the sampler and accepts lawful canonical layouts.

## `D3` — Make seed-cell count load-bearing

**Choice.** Every generated scene contains a chamber with at least two seed
cells of the same color, plus an empty chamber and at least two uniquely seeded
chambers of different colors.

**Reason.** A same-color conflict is the smallest witness separating “one seed
cell” from “one distinct seed color.” Different unique colors separately block
a global-first-color shortcut, and an empty room blocks unconditional filling.

**Alternatives rejected.** Multiple seeds only when their colors differ. That
would refute “fill any seeded room” but not the more plausible distinct-color
shortcut. Rare probabilistic negatives were also rejected because complete
lessons need deterministic support.

**Evidence.** `test_exactly_one_seed_cell_not_one_distinct_seed_color` and the
profile tests in
`repo/generators/71492f8cef8f/tests/test_generator_71492f8cef8f.py`;
`checks/lesson-window-probe.json` records every witness in `192/192` demo windows.

## `D4` — Advertise one exact, pixel-observable axis

**Choice.** Expose only `scene_profile` with four string values:
`cross_closed`, `cross_open`, `offset_closed`, and `grid_open`.

**Reason.** These values change visible topology and can be recovered from the
returned grid. Size, seed coordinates, seed colors, and similar incidental draws
are useful diversity but were not promoted to exact controls.

**Alternatives rejected.** A large axis table copied from RNG decisions. Such
metadata is easy to misreport, creates illegal joint combinations, and can pass
only by trusting provenance rather than pixels. Unknown controls now fail loudly.

**Probe.** `observe_overrides` infers the profile from complete wall rows,
complete wall columns, and border openings. The override battery is green, and
portable task tests cover every profile in every band.

## `D5` — Use a four-position teaching schedule

**Choice.** Map `sample_index % 4` to the four profiles, alternating closed and
open layouts. A lesson uses two demonstrations and one query.

**Reason.** Every cyclic two-demo window contains an open profile while still
showing multiple closed/offset structures over a short period. This is stronger
than relying on aggregate witness frequency.

**Alternatives rejected.** Independent random profile draws could produce a
complete lesson with no edge-open witness. A longer schedule would add
complexity without a new semantic branch.

**Limitation.** The period is predictable. That is acceptable because sample
index is not part of the model input, but the finite schedule is not a universal
coverage proof.

## `D6` — Retain a canonical-profile anchor without collapsing diversity

**Choice.** `cross_closed` is exactly `7x9` and four colors in every difficulty
band; other profiles scale by band.

**Reason.** The profile-floor check requires a canonical-size/palette hit in
each band. One scheduled anchor preserves that support while other draws broaden
size and topology.

**Alternative rejected.** Force every scene to canonical dimensions. That would
satisfy the floor but unnecessarily narrow the training distribution.

## `D7` — Encode semantic rivals and witnesses in source

**Choice.** Declare five rivals, five witnesses, their mapping, two
canonical-fitting shortcuts, and `lesson_identifiable`:

- `fill_any_seeded` ↔ `multi_seed_room`;
- `unique_seed_color` ↔ `same_color_multi_seed`;
- `fill_empty_from_first_seed` ↔ `empty_room`;
- `global_first_seed` ↔ `multiple_unique_colors`;
- `closed_rooms_only` ↔ `edge_unique_room`.

**Reason.** This turns teaching claims into executable contracts used by shared
checks and task-local probes. The canonical-fitting declarations force the
review to show why generated data adds information beyond the official pairs.

**Limitation.** Declared rivals are finite. The audit of `70c33a3391ac` found an
undeclared D4 shortcut despite a strong generator, motivating the additional
gate proposed in `QUESTION_ANSWER.md`.

## `D8` — Add a reusable cyclic-window tool

**Choice.** Add `workspace/lesson_window_probe.py`, reading all schedule, rival,
and witness declarations from the live generator.

**Reason.** The shared lesson census materializes many production lessons but
does not rotate every pair into the query position. The task-local probe covers
all cyclic starts cheaply and is portable to the task-test runtime.

**TDD history.** The first red run failed because the script did not exist
(`checks/tool-tdd-red/`). The next run exposed that portable child processes did
not inherit an import path for `puzzle_generators`; the tool now locates either
the repository's `shared/runtime` or the portable runtime root. The final stage
passes `8/8` tests in `checks/task-tests/result.json`.

## `D9` — Keep validation broad; test curriculum guarantees separately

**Choice.** `self_check` verifies lawful task inputs and canonical support, while
task tests inspect stronger generated-distribution guarantees.

**Reason.** Requiring every lawful input to contain all teaching witnesses would
reject canonical pairs and conflate domain validity with curriculum quality—the
same defect reproduced in audit target `ea45d5e1d11c`.

**Alternative rejected.** Put all branch-frequency requirements into
`self_check`. That makes canonical support difficulty-dependent and causes valid
hand-made inputs to be rejected.
