# Working notes: dc0a7662670b

## Review-9c7099cf286f24db

No prior return was used as a repair lead: `evidence/associated_notes.jsonl` was
empty. The current packet baseline, canonical pairs, and before-battery evidence
were treated as the source of truth.

### Baseline defects

The version-1.2.0 motif gallery did not pin the canonical rule hash, advertised
axes it could not honor, swallowed unknown overrides, under-sampled canonical
6- and 7-cell components, and declared no semantic witnesses or complete-lesson
identifiability contract. Its random 3–5-cell motifs did not guarantee examples
that distinguish true perimeter from cell count, bounding-box perimeter, input
position, omitted separator rows, or descending-color tie-breaking.

The canonical pairs themselves are ambiguous under two especially plausible
rules: sorting by area and reversing the color tie-break. The canonical set has
no equal-perimeter tie, so a generator must add that evidence deliberately.

### Selected design

Use a constructive four-profile cycle instead of rejection-sampled random
motifs. Each profile occupies a distinct semantic role, while random colors,
dihedral transforms, and exact canonical dimensions retain visual diversity.
The schedule is indexed by `sample_index % 4`; therefore every four consecutive
examples—and every cyclic rotation of a four-example lesson—contains all roles.

Only three exact axes remain: `grid_h`, `grid_w`, and `shape_profile`. Unknown,
ill-typed, out-of-range, or unsupported values raise immediately. Generation is
constructive, so there is no fallback that can silently violate an override.

### Rejected alternatives

- **Pin only `RULE_HASH`:** fixes provenance but leaves shortcut-rich training data.
- **Keep fully random motifs and hope the census finds enough witnesses:** does not
  guarantee that a complete lesson, rather than the pooled dataset, refutes each
  shortcut.
- **Treat all nonzero touching cells as one object:** disagrees with the Racket
  rule, which finds same-color components; canonical examples contain cross-color
  adjacency.
- **Broaden to arbitrary polyominoes:** increases surface area without improving
  the specific ambiguities. The reviewed domain stays bounded and explicit.

### Limits

The constructive domain is intentionally narrow: 3–4 distinct-color components,
component sizes 3–7, per-component bounding boxes at most 4×4, and four linked
shape families. The semantic probes cover declared rivals, not every imaginable
program, and finite sampling cannot prove universal induction. No Racket
reference source was changed.

### Reusable probe

`workspace/semantic_probe.py` verifies declared canonical shortcuts against all
canonical pairs and rotates complete generated lessons across difficulty bands.
It consumes the generator's actual rival declarations rather than duplicating a
name list. See `workspace/README.md` for the command and scope.
## Current reviewer considerations

Source SHA-256: `795d65f89aa4b0dcdb41cec3487bdcc68f61913ab700e54b9e460dd99c42402b`.

# Decisions: dc0a7662670b

## D1 — Treat the Racket rule as unchanged authority

**Choice.** Pin `RULE_HASH = "eff15ddf94a7"` and repair only the Python
generator, tests, notes, and workspace tooling.

**Rationale.** Canonical replay and rule smoke showed that the Racket program
already implements a coherent transformation: same-color components sorted by
true edge perimeter, then color, then vertically packed. The defects were in
the training distribution and generator contract, not in authority behavior.

**Alternatives considered.** Rewriting the Racket rule or canonical examples was
rejected because no mismatch was observed. Treating all touching nonzero colors
as one component was also rejected: canonical inputs include cross-color
adjacency, while the authority groups same-color components.

**Probe.** Canonical Python mirror equality for all five canonical pairs and
120/120 Racket mirror-parity calls.

**Failure mode/limit.** The mirror is still an independent Python
reimplementation, so authority synchronization and rule smoke remain required.

## D2 — Replace random motifs with a four-profile semantic schedule

**Choice.** Use `canonical_four`, `bbox_tie`, `area_inversion`, and `color_tie`
in a period-four schedule.

**Rationale.** The canonical pairs all support sorting by area and contain no
perimeter tie. Random motif diversity does not guarantee that a complete lesson
refutes those shortcuts. Each selected profile has one load-bearing semantic
job, and every four-example lesson sees all jobs.

**Alternatives considered.** Keeping the old random generator plus more draws
was rejected because pooled witness frequency is not complete-lesson evidence.
A larger free-form polyomino grammar was rejected as unnecessary surface area.
A profile selected only by difficulty was rejected because some bands could
lack a required witness.

**Probe.** `checks/semantic-probe.json` checks 2,400 cyclic windows;
`checks/lesson-census.json` checks 300 production-sampled lessons.

**Failure mode/limit.** A finite declared rival list is not a proof of unique
induction. New plausible shortcuts should be added as executable rivals and
paired with a constructive profile.

## D3 — Make canonical support exact, not merely envelope-compatible

**Choice.** Default each profile to one of the canonical `(height, width,
palette-size)` combinations and include 6- and 7-cell components.

**Rationale.** The baseline generated only 3–5-cell motifs and hit an exact
canonical profile in 4/60 draws, with zero easy-band support. Matching exact
profiles prevents a model from learning a synthetic-only scale regime.

**Alternatives considered.** Broadening dimensions beyond canonical scale was
rejected for this repair. Weighting random dimensions toward canonical values
was rejected because exact profile support can be guaranteed constructively.

**Probe.** Final profile floor: 60/60 exact and 60/60 envelope across all bands.

**Failure mode/limit.** Exact profile matching can reduce geometric breadth;
future breadth should preserve at least one complete semantic witness set per
lesson.

## D4 — Keep only exact, observable axes

**Choice.** Advertise only `grid_h`, `grid_w`, and `shape_profile`; reject unknown
or invalid controls before generation.

**Rationale.** The prior generator declared dead singleton axes and values it
could not honor, accepted unknown keys, and could fall back after rejection.
That makes experiments irreproducible and allows misspelled controls to appear
successful.

**Alternatives considered.** Keeping diagnostic axes with special metadata was
unnecessary. Declaring incompatible combinations was also unnecessary because
the constructive layout supports the entire stated Cartesian product.

**Probe.** 8,100/8,100 override-matrix draws accepted with 90 tested cases and
zero contract failures; task tests cover every profile, both dimension bounds,
all bands, and invalid/unknown inputs.

**Failure mode/limit.** Adding a future axis requires a real draw, an observation
path, boundary tests, and joint-axis support—not metadata alone.

## D5 — Use constructive placement, not rejection with fallback

**Choice.** Build each scene in fixed layout regions with randomized transforms
and colors, guaranteeing separation and fit.

**Rationale.** Constructive generation makes exact overrides and deterministic
replay falsifiable. A fallback after failed random placement can silently return
an instance that does not match the requested controls.

**Alternatives considered.** Increasing retry count was rejected; it reduces but
does not remove fallback risk and complicates reproducibility.

**Probe.** Deterministic replay, all exact override combinations, 240 generated
instances per band in task tests, and 600/600 strict semantic-gate samples.

**Failure mode/limit.** Region structure can become visually regular. Dihedral
transforms, colors, positions within regions, and multiple exact dimensions
provide variation, but the repair prioritizes semantic reliability.

## D6 — Build a reusable cyclic semantic probe

**Choice.** Add `workspace/semantic_probe.py`, reading the generator's actual
rival declarations and canonical pairs.

**Rationale.** The shared census materializes production lessons but explicitly
does not rotate every pair into the query position. A task-local probe makes the
small deterministic cycle exhaustively checkable and prevents copied rival-name
lists from drifting.

**Alternatives considered.** Documenting a manual command sequence was rejected
because future agents need a one-command, hash-bearing result. Duplicating rival
names in the probe was rejected because it could silently go stale.

**Probe.** New test first failed because the script did not exist; after
implementation, the suite passed 54/54. A direct-source invocation then exposed
a package-import assumption; a source-checkout fallback was added and the full
2,400-window run passed.

**Failure mode/limit.** The tool is task-local and declarative; it cannot discover
unknown rivals automatically.

## D7 — Add an opt-in winner-width relay without changing production semantics

**Choice.** Keep production `generator.py` and the canonical Racket program
unchanged, and add a task-local native parametric adapter with
`mode=canonical|winner_width_relay`. Both modes draw the same inputs. The relay
first performs the canonical true-perimeter/color ranking, then uses the crop
width of the first-ranked component as a 1-based selector and recolors only that
ranked crop to color 8.

**Rationale.** The assignment requires a real sequential dependency rather than
an alternate ordered implementation. Here step B cannot be resolved before step
A: both the winning component and its width are outputs of the canonical rank.
The admitted ordinary grammar deliberately exercises selector values 1, 2 and 3,
and the retained counterfactual uses winner height instead of width.

**Alternatives considered.** A direct extra color/shape switch was rejected as
non-compositional. Selecting by raw position, area, bounding-box perimeter, or a
fixed rank was rejected because each can bypass the required intermediate. A
production-generator edit was unnecessary and would have mixed a proposed
variant with an already approved canonical family.

**Evidence.** Native qualification covers two settings, seeds 0 and 17, three
demonstrations and four queries per job with protected Racket. The task-local
authoring audit covers 14 distinct inputs, 44 protected-Racket evaluations,
1,152 finite named-rival checks, all selector values, eight leakage-checked
public turns, and a seven-component 30x30 stress query touching all four borders.
On the retained witness, width 2 and height 7 select different crops and change
20 final cells.

**Failure mode/limit.** The rival audit is finite and cannot prove unique
induction against arbitrary programs. `ready` is reviewer-reported only; exact
integrated owner replay, semantic acceptance, and any training admission remain
separate required decisions.

