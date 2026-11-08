# Working notes: 06b4c496c6cf

## Intended rule

The unique connected color-2 object is normalized to the top-left of its
bounding box and used as a template. Starting from a blank grid of the same
shape, stamp those offsets at every marker cell of colors 3 through 9, using
the marker's color. Process marker colors in ascending numeric order, so the
higher color wins cross-color overlap, and silently clip cells outside the
grid. The source template does not remain in the output.

The selected Racket authority is unchanged and pinned by
`RULE_HASH = "7bb33c62cc2e"`.

## Reversed curriculum decision

The imported version 3.0.0 used five demonstrations plus one query and placed
each shortcut-breaking texture exactly once. Its normal ordered lesson passed,
but the required arbitrary-query rotation gate failed 38 of 72 held-out
positions: holding out a unique witness could leave a canonical-compatible
rival unrefuted. The retained exact example is
`counterexamples/rotation_ambiguity_before.json`.

Version 3.2.0 instead uses a nine-pair cycle and eight demonstrations:

`plain, hollow_corner, overlap_pair, pair_markers, clip, hollow_corner, overlap_pair, pair_markers, clip`

Every special witness occurs twice, so removing any one pair leaves the four
special relations in the demonstrations. `plain` remains grounding evidence
but is not required by `lesson_identifiable` because it has no declared rival
of its own.

## Added hypotheses and distribution choices

Two canonical-compatible rivals were missing:

- `canonical_colors_only`: process marker colors 3 through 5 only. Every
  canonical pair uses only those marker colors.
- `first_occupied_cell_anchor`: anchor the template at its lexicographically
  first occupied cell rather than its bounding-box top-left. Canonical
  templates occupy `(0, 0)`, so the distinction requires a hollow-corner
  witness.

Both are executable, verified against all three usable canonical pairs, and
included in `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`. Every generated
scene includes at least one marker color 6 through 9, and the duplicated
hollow-corner profiles distinguish occupied-cell anchoring. Existing witnesses
cover forced marker cells, lower-color overlap precedence, one-marker-per-color,
dropped clipped stamps, and retained source templates.

Advertised exact controls remain `grid_h`, `grid_w`, `marker_count`, and
`texture`. `overlap_pair` and `pair_markers` with one marker are the only
declared incompatible combinations. Unknown controls, booleans masquerading
as integers, and out-of-range values are rejected.

## Verification and reusable probe

Final generator SHA-256:
`c10bd8df02f25dc16d2d40bbc4b12080b089830c3b7564b74a167b78e81e286b`.

- Required-rotation battery: 12/12 green.
- Semantic gate: 63/600 strict hits (10.5%, floor 5%); 12/12 lessons
  identifiable; 108/108 held-out rotations unambiguous.
- Production census: 300/300 lessons, 2,700 unique pairs, 0 production
  ambiguities, and 0/2,700 rotated-query ambiguities.
- Exact override gate: 34,290 accepted draws across 383 cases and three bands;
  180 expected explicit incompatibility rejections; zero findings.
- Portable focused tests: 12/12 passed.
- `workspace/probe_curriculum.py`: 81 cyclic lesson windows, 729 query
  rotations, 104 legal boundary cases, 16 declared incompatible cases, and 18
  canonical-rival checks, with zero failures.

## Known limits and open findings

Identifiability is finite evidence against the six declared competitors, not a
proof against every possible program. Eight demonstrations are a deliberate
cost increase. Requiring an extended marker color in every generated scene is
stronger than the canonical distribution; it prevents the color-3..5 shortcut
but may be relaxed later to duplicated lesson-level witnesses if lower-palette
scene diversity is worth the added schedule logic. Grid, template, and marker
ranges are intentionally compact and do not claim to enumerate every lawful
Racket input.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.
## Current reviewer considerations

Source SHA-256: `c10bd8df02f25dc16d2d40bbc4b12080b089830c3b7564b74a167b78e81e286b`.

# Decisions: 06b4c496c6cf

## D1 — Treat arbitrary held-out-query rotation as supported

The downstream task explicitly requested a rotation check, and the lesson
contract exposes deterministic rivals. The imported five-demo schedule was
therefore not accepted merely because its fixed final query passed. A required
rotation run reproduced 38 ambiguous positions out of 72; one exact failure is
retained in `checks/rotation_ambiguity_before.json`.

Alternative rejected: declare the curriculum ordered and keep five demos. That
would be cheaper, but it would make query position semantically privileged and
would not satisfy the selected required-rotation policy.

## D2 — Duplicate witnesses rather than resample ambiguous lessons

The selected nine-pair cycle is:

`plain, hollow_corner, overlap_pair, pair_markers, clip, hollow_corner, overlap_pair, pair_markers, clip`.

With eight demonstrations, any one held-out pair leaves each special relation at
least once. This is deterministic, inspectable, and covers every cyclic start.

Alternatives rejected:

- Randomly resample until `lesson_identifiable` passes: correct on accepted
  lessons but obscures coverage and can bias accepted sample indices.
- Add one combined “all-specials” scene: smaller schedule, but entangles four
  concepts and weakens causal teaching evidence.
- Duplicate `plain`: it has no declared canonical-compatible rival to refute.

Failure mode: the lesson is longer. That is an explicit training-cost trade-off.

## D3 — Add two undeclared canonical-compatible hypotheses

`canonical_colors_only` fits canonical pairs because they use marker colors
3–5. `first_occupied_cell_anchor` fits because canonical templates contain
bounding-box cell `(0, 0)`. Both are executable rivals, not prose-only guesses.
The palette witness uses marker colors 6–9; the occupied-cell distinction uses
hollow-corner templates.

Alternative rejected: rely on humans to notice these shortcuts during intake.
Executable rivals let the semantic gate, census, and task-local probe test them
continuously.

## D4 — Guarantee extended palette support in every generated scene

This is the simplest deterministic way to prevent a color-3..5-only learner.
It also makes the witness independent of marker count and random palette draw.

Alternative considered: place high colors only in two duplicated schedule slots.
That would preserve more all-low scenes, but introduces another schedule-level
condition and would require regenerating the already-frozen solve episode. The
current restriction is documented as a limit; a later revision can relax it if
palette-diversity value outweighs complexity.

## D5 — Preserve isolated scene semantics

Each ordinary scene has at most one of hollow anchoring, overlap, repeated
marker color, or clipping. This makes each witness interpretable and prevents a
single complex example from doing all teaching work. The source-removal and
extended-palette witnesses are global properties and do not change geometry.

## D6 — Keep four exact controls and two explicit incompatibilities

The controls `grid_h`, `grid_w`, `marker_count`, and `texture` are observable
from pixels and constructively supported across legal boundaries. One-marker
`overlap_pair` and `pair_markers` requests are impossible by definition and are
rejected explicitly. No new diagnostic or inert axes were added.

## D7 — Make tests portable

The original task test guessed canonical paths from `__file__.parents`, which
failed in the isolated runtime. It now uses the supported `reviewer_support`
helpers. The regression fixture remains a sibling of the selected task and is
loaded by a relative sibling path, while canonical and base authority use the
portable root.

## D8 — Build a reusable exhaustive probe

`workspace/probe_curriculum.py` iterates the generator's actual declared rival
maps rather than copying a rival-name list. It verifies canonical compatibility,
all nine cyclic starts across three seeds and three bands, every one of the nine
held-out positions, legal override boundaries, and declared incompatibilities.
It is supplementary to—not a replacement for—the shared Racket-backed battery
and production census.

## Domain and inference limits

The generator samples 10–18 by 12–22 grids, compact 2–3-cell bounding-box
templates with 3–6 cells, and 1–6 markers. These are reviewed training ranges,
not the entire mathematical input domain. Passing six named rivals does not
establish unique induction over all programs. Counts in this return are tied to
generator SHA-256 `c10bd8df02f25dc16d2d40bbc4b12080b089830c3b7564b74a167b78e81e286b`.

## 2026-10-24 parametric-main review — assignment `review-50eae8a5737c04c8`

Built a native two-setting family under `workspace/parametric/` without changing
selected `generator.py` or the canonical ledger:

- `marker_selection=all` uses the canonical Racket program byte-for-byte.
- `marker_selection=template_width` measures the unique color-2 template's
  bounding-box width, derives marker color `width + 5` (6–9), and stamps only
  markers of that derived color.

The setting-independent sampler supports 2–6 demonstrations and one to four
prefix-stable queries. Qualification uses three demonstrations and four queries;
the fourth query is 30×30. The finite authored rival set is rejected by the
minimum two-demo curriculum in both settings.

Two defects were found through failing regressions before repair. Seed 4 could
clip every selected teaching stamp to one cell, preserving the
`selected_marker_cells_only` shortcut; the sampler now guarantees one full-fit
target marker. Python claim labels also applied overlapping canonical stamps in
row order, while the authoritative program applies colors 3 through 9 so higher
colors win; seed 17 now pins that precedence and protected-Racket parity.

Evidence is under `checks/06b4c496c6cf/`: 320 audited episodes / 2,560 pairs,
45 staged task tests, four native qualification jobs / 40 protected-Racket
evaluations, a reviewer-replayed causal counterfactual, two saved four-query
public challenges, and eight sequential one-query projections. The source-bound
manifest is `workspace/parametric/evidence/manifest.json`.

The sequential dependency is genuine: measure template width (A), map it to
marker color `width + 5` (intermediate), then choose the stamp anchors of that
color (B). Replacing the intermediate with fixed color 7 changes the retained
query output. This return is reviewer-ready only: exact owner-byte acceptance,
training admission, and measured training benefit remain pending.
