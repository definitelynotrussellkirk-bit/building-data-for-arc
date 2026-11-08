# Working notes: 7e826540d45d

## Current decision — 2026-10-26

Repaired the retained control-surface and observability gaps in generator
`1.4.0`. Exact height and width pins take precedence over difficulty ranges;
`n_objects`, `n_distinct_colors`, and `palette_kind` constrain the realized
sample; `palette_size` remains an explicit diagnostic latent-pool control;
unknown overrides are rejected; singleton count controls are compatible on
their own; legacy `texture` aliases are checked for conflicts; and
`observe_overrides` reports realized dimensions, object count, and distinct
nonzero colors. The task-local override-contract sweep completes 5,085 draws
across 565 cases and three difficulty bands with zero findings.

Added the proposed native family `halo_mode={one_ring, selected_two_step}`. The
default program is the exact catalog source. The alternate first replaces every
object by its canonical one-cell orthogonal halo (A), then chooses the most
frequent nonzero color in that intermediate and expands only that halo one more
orthogonal step (B). The grammar deliberately includes a compact 3×3 object and
a six-cell line: the compact object wins by original-cell count, while the line
wins after halo extraction, making the A→B dependency visible under a skip-A
ablation. Inputs are setting-independent, support 3–6 demonstrations and 1–4
queries, and include a substantive 30×30 fourth query. Focused pytest, a
protected-Racket four-job study, authoring preflight, a protected skip-A witness,
and public projection checks are retained as source-bound reviewer evidence.
Owner source review, native qualification/acceptance, and any training admission
remain separate.

## Second reviewer pass — 2026-10-26

Removed residual fixed-shape and fixed-position teaching shortcuts. The
selected six-cell line now alternates horizontal/vertical orientation and
appears in both top and bottom halves/opposite corners. New regression tests
prove that widest-object and bottommost-object selectors each fail. Base
`self_check` was also tightened to enforce the generator's own pairwise
separation contract, preventing overlapping halo zones from being accepted.
The protected-Racket probe now embeds a 200-seed / 600-demonstration shortcut
audit; the focused suite now has 24 tests and the protected study still passes
40 Racket evaluations.

## Third reviewer pass — 2026-10-26

Removed two deeper lesson artifacts: the selected object had always been a
six-cell straight line, and three-example lessons could retain one dominant
orientation, allowing a widest-object rule to survive for half the seeds. The
grammar now rotates among six-cell lines, bent six-cell L shapes, and
eight-cell lines against compact 3×3/4×4 competitors; the first and third
demonstrations use opposite orientations. New regression tests require both
straight and bent selectors, source sizes 6 and 8, both orientations, and
rejection of longest-straight and widest-object rules in the minimum
three-demonstration lesson. A second compact competitor in the bent-L lesson
also varies the selected object's raw source-size rank between second and third,
rejecting both fixed-rank rules. The permanent probe confirms these properties
over 200 seeds / 600 demonstrations plus 40 protected-Racket evaluations. The
focused suite now has 26 tests.
