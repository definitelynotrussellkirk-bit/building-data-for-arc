# Working notes: cbe60e2c4b18

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `05d9396d7fef2d18dd1317b7db4542cd8f334bb2fa14c093338b58901a98df27`.

# Decisions — cbe60e2c4b18

## Scope and prior evidence used as leads

The selected baseline was already a substantial version-2 repair. I treated its
retained notes as hypotheses, not current measurements. The useful prior lead
was return `local-random-41e8303f1347` in
`repo/generators/cbe60e2c4b18/evidence/associated_notes.jsonl`: keep same-color
and different-color panels, connected and disconnected intersections, and test
every four-residue lesson window. I independently reran the complete before
battery before editing; all 12 stages were green.

I did **not** change the transformation or its Racket authority. The selected
canonical rule remains pinned at `RULE_HASH = "cd6a6225c112"`: split two
equal-size panels at a vertical color-9 divider and paint color 8 at every
aligned coordinate occupied in both panels.

## D1 — Broaden ordinary color support without weakening the lesson schedule

### Observation

The baseline advertised five palette kinds, but its ordinary four-residue
schedule used only four of them and only input colors `{1,2,3,4,5,6}`. Colors 7
and 8 were reachable only through explicit overrides. The retained before probe
at `checks/before-distribution-probe.json` measured this over 256 ordinary
samples. This was not a rule error, but it was an unnecessary distribution
shortcut: a learner could associate the transformation with a restricted input
palette.

### Decision

Keep the existing four semantic residues, but let residues 2 and 3 alternate
between two palette variants by schedule round:

- residue 0: `canonical_23 = (2,3)`;
- residue 1: `same_gray = (5,5)`;
- residue 2: alternate `canonical_24 = (2,4)` and `varied = (4,7)`;
- residue 3: alternate `contrast = (6,1)` and new `green_azure = (3,8)`.

This uses every lawful non-divider input color 1–8 in ordinary sampling while
each consecutive four-example lesson still contains a canonical anchor, one
same-color example, different-color examples, and both overlap topologies. The
final 256-sample probe at `checks/after2-distribution-probe.json` observed all
colors 1–8 and all six palette kinds.

### Alternatives rejected

I first tried a much larger 16-name palette table. Although semantically valid,
it multiplied the exact-override Cartesian product and made the override
verifier unnecessarily expensive. I reverted it and selected the smallest
six-palette design that covers colors 1–8 while preserving the four-example
teaching contract. I also rejected random palette selection per draw because it
could remove same-color or canonical-profile evidence from a sliding lesson
window.

A first implementation computed `AXES["palette_kind"]["valid"]` dynamically.
The source linter correctly treated that as nonliteral metadata, so the final
version uses an explicit literal enum.

## D2 — Remove the fixed handed/reflection signature in disconnected overlaps

### Observation

The baseline disconnected constructor always used the northwest/southeast cells
of a 2×2 block as shared support, always gave the northeast bridge to the left
panel, and always gave the southwest bridge to the right panel. With minimal
counts, all 256 probe draws normalized to one identical support pair. A solver
could learn a reflected or left/right-handed bridge convention unrelated to the
intersection rule.

The original rationale for this exact handedness was not documented; it appears
to have been the simplest constructive proof that both full panels stay
4-connected while their intersection has two components.

### Decision

Randomize two independent binary choices inside the same constructive proof:

1. choose either diagonal of the 2×2 core as the two shared cells;
2. swap ownership of the two off-diagonal private bridge cells between panels.

The rest of the growth algorithm is unchanged. It still grows additional shared
cells onto exactly one component, prevents private-cell collisions, requires
both panel supports to be connected, and requires the shared support to have
exactly two components.

The final minimal-core probe observed all four expected normalized signatures
(76, 43, 70, and 67 occurrences in 256 draws), rather than one. A regression
test requires the exact four-signature set.

### Alternatives rejected

Unconstrained random supports were rejected because they would make connectivity
and exact component count probabilistic. Applying arbitrary whole-grid
reflections after construction was also unnecessary and would complicate
coordinate provenance and override observation. Varying the two constructive
binary choices gives the needed symmetry coverage with a local, auditable
invariant.

## D3 — Add tests and a reusable generated-input probe

Two task-local regression tests now require:

- ordinary 256-sample coverage of every panel color 1–8; and
- all four minimal disconnected bridge reflection/handedness signatures.

I wrote those tests first and retained their failure output in
`checks/red-task-tests.stdout`. Before the production change, colors 7 and 8
were absent and only one bridge signature appeared. The final portable task-test
stage reports 16/16 passing in `checks/green2-task-tests.stdout`.

The existing canonical test used a guessed path relative to the test file. That
failed in the source-bound portable runtime before reaching generator behavior.
I replaced it with the repository-supported `reviewer_support.canonical_pairs`
and `find_root` helpers; this is a portability repair to the task-local test, not
a rule change.

`workspace/distribution_probe.py` is a reusable, generated-input-only authoring
tool. It records ordinary palette/color/layout/shape counts and normalized
minimal bridge signatures as stable JSON. It deliberately does not read answer
labels or Racket source.

## D4 — Preserve identifiability and authority

The palette and geometry changes preserve the baseline four-residue teaching
logic. On the final generator SHA-256
`05d9396d7fef2d18dd1317b7db4542cd8f334bb2fa14c093338b58901a98df27`:

- all 12 battery stages are green;
- the override stage accepted 55,710/55,710 draws across 619 cases and three
  bands;
- task-local tests are 16/16 passing;
- the 300-lesson census contains 100 lessons per band, zero ambiguous lessons,
  zero warnings/errors, and refutes all 24 declared rival entries in every
  lesson;
- selected Racket authority remains unchanged and synchronized.

A direct resume of the source-bound battery initially lacked the packet's local
Racket path and produced `RACKET_MISSING`; rerunning that stage with the same
runtime snapshot and the wrapper's environment passed. This was retained as an
environmental failed iteration, not presented as a generator defect.

## Actual sampler and remaining limitations

These limits are intentional and should not be mistaken for proof over the full
executable Racket domain:

- A scene has exactly two equal-size panels separated by one full vertical
  color-9 column.
- Each panel contains one monochrome, nonempty, 4-connected object. Multicolor
  panels, multiple objects per panel, and disconnected full-panel objects are
  outside the teaching grammar.
- Ordinary dimensions are 5–9 rows by 5–9 columns per panel. Exact overrides
  expose the declared ranges.
- Ordinary shared support is 2–5 cells and ordinary private support is 1–4 cells
  per panel; exact controls permit the larger declared ranges when constructible.
- The intersection is either connected or has exactly two 4-connected
  components. More than two components are not generated.
- Ordinary palettes are six selected ordered pairs, not all 64 pairs over
  colors 1–8. They cover every color and include equal and unequal panels, but
  they do not establish palette-pair universality.
- Lessons use a deterministic four-residue schedule. The shared census samples
  production lessons but does not test every conceivable ordering or every
  undeclared rival.
- The finite declared-rival suite establishes the recorded distinctions; it is
  not a universal induction proof.

## Known failure modes for future edits

- Adding enum values can sharply increase override-verifier case count; estimate
  the cross-product before expanding an exact axis.
- Any change to disconnected support must recheck full-panel connectivity,
  private-cell disjointness, and exact shared component count.
- Any schedule change must rerun all cyclic four-example starts; aggregate
  palette frequency alone is insufficient.
- Color 9 is structural and must not enter panel palettes; color 8 may be an
  input color even though the output is rendered in color 8, because the rule
  depends on support rather than input hue.
- Portable tests must use `reviewer_support` rather than guessing canonical-data
  paths from source depth.
## D5 — Verify the packaged patch from a pristine handoff

The generated `patches/source.patch` was replayed against a fresh extraction of the
original uploaded ZIP, rather than against the working tree. `git apply --check` and
`git apply` both exited 0. The resulting generator hash exactly matched the final
battery and post-repair solve hash. Portable task tests then passed 16/16 and lint
passed from that clean packet. The complete replay record is
`checks/fresh-replay/summary.json`.
