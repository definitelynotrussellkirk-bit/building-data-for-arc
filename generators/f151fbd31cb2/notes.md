# Working notes: f151fbd31cb2

Review `review-08296b5f63a5e390` replaced baseline version 2.1.0 with source-bound
version 3.0.0. Prior return `review-f488e46623fb0139:v0001` was used only as a
lead; the selected baseline battery was rerun.

Key decisions and limitations are recorded in packet-root `DECISIONS.md`.
Reusable probes are in `workspace/reference_probe.py` and
`workspace/shortcut_probe.py`; focused regression tests are under `tests/`.

Final checked generator SHA-256:
`92adf9c50a8f7c0346751867e759b5fbb4ca6f7742e71ac64b21a2d50cf8751e`.
The Racket authority was not changed.
## Current reviewer considerations

Source SHA-256: `92adf9c50a8f7c0346751867e759b5fbb4ca6f7742e71ac64b21a2d50cf8751e`.

# Decisions — f151fbd31cb2

## D1 — Pin the selected authority and leave Racket unchanged

**Choice.** Set `RULE_HASH = "33294c3c6e8b"` and test a readable Python mirror
against the real packet Racket implementation.

**Rationale.** Canonical outputs and generated samples agreed with the stated
dual-key rule. The defects were in input generation and contract metadata, not
in authority semantics.

**Alternatives.** Rewriting or simplifying the Racket rule was rejected because
there was no demonstrated semantic fault and it would enlarge the review surface.

**Probe / failure mode.** Task-local parity covers 4 canonical and 36 generated
inputs. Authority sync passed, while the battery still reports an archival raw
source variant as divergent; the selected execution source is synchronized.

## D2 — Remove dead axes instead of pretending they are useful controls

**Choice.** Replace the ten-axis baseline with six exact axes:
`grid_h`, `grid_w`, `shape_key`, `color_key`, `n_l`, `n_plus`.

**Rationale.** `palette_kind`, `palette_size`, `position_bias`,
`n_distinct_colors`, `density`, and `texture` either did nothing, duplicated
another declaration, or mixed negative fixtures into the ordinary domain. They
multiplied the override matrix without adding an observable degree of freedom.

**Alternatives.** Implementing actual palette/texture branches was rejected as
unnecessary and potentially canonical-distant. Keeping singleton diagnostic axes
was rejected because callers reasonably interpret `AXES` as exact controls.

**Probe / failure mode.** The final override stage covered 342 cases and 30,780
draws with zero findings. Unknown or mistyped controls now raise `ValueError`.

## D3 — Use a capacity-proven four-zone constructor

**Choice.** Split every grid into four quadrants with a blank separator row and
column; place one object per used quadrant.

**Rationale.** The maximum lawful scene has four objects. The minimum 9×11 grid
still gives four zones large enough for a plus. This makes every count override
constructive rather than probabilistic and prevents silent fallback to an invalid
or underfilled grid.

**Alternatives.** The baseline's global rejection sampler was rejected because
bounded retries can make exact controls nondeterministic or underfilled. A fully
general packing solver was unnecessary for only four small objects.

**Probe / failure mode.** All boundary combinations—minimum/maximum dimensions,
both keys, and 1/2 counts—are tested in all four difficulty settings. The cost is
a documented spatial regularity: generated objects do not touch and occupy at
most one per quadrant.

## D4 — Teach the key, not the canonical majority correlation

**Choice.** Cycle through `canonical_majority`, `selected_minority`, and
`balanced` profiles by `sample_index mod 3`.

**Rationale.** Every canonical pair selects the family that is both more numerous
and larger in total area. Random independent counts could still produce complete
lessons where those rivals survive. A fixed three-slot schedule guarantees a
selected-minority counterexample in every consecutive three samples.

**Alternatives.** Uniform random counts were rejected because witness frequency
alone does not guarantee lesson-level coverage. Always making the selected
family a minority was rejected because it would simply create an opposite
shortcut and move away from canonical examples.

**Probe / failure mode.** Task tests cover all three cyclic starts in every band.
The 300-lesson census refuted both declared rivals in every lesson. Solvers may
still form undeclared hypotheses; this finite result is not universal induction.

## D5 — Preserve canonical profile support in every difficulty band

**Choice.** The majority and minority slots use one of three canonical sizes in
all bands; the balanced slot uses broader difficulty-aware dimensions.

**Rationale.** The baseline's medium/hard ranges excluded canonical sizes, giving
zero per-band profile support. Keeping two canonical-sized slots out of three
maintains source similarity without discarding broader hard examples.

**Alternatives.** Making every sample canonical-sized was rejected because it
would remove useful size diversity. Making size depend only on difficulty was
rejected because hard would again have no canonical support.

**Probe / failure mode.** Final profile floor reports exact-profile 37/60 and
envelope 41/60, with at least one hit in each 20-draw band.

## D6 — Validate structure and expose exact observations

**Choice.** Add `self_check`, `strict_canonical_like`, and `observe_overrides`.
The validator rejects malformed grids, unsupported colors, duplicate/missing
keys, unknown green shapes, and out-of-range family counts.

**Rationale.** Construction success is not evidence that downstream or overridden
inputs remain lawful. The override gate also needs a semantic observer, not only
draw provenance.

**Alternatives.** A permissive check for “some keys and some green” was rejected
because merged or malformed components could silently change the rule domain.

**Probe / failure mode.** Canonical inputs pass 4/4; malformed test fixtures return
diagnostics rather than raising. The validator intentionally accepts only one or
two objects per family, so it is a distribution validator rather than a universal
oracle-domain recognizer.

## D7 — Retain reusable source-bound reviewer tools

**Choice.** Add `workspace/reference_probe.py` and
`workspace/shortcut_probe.py`, plus 50 task-local tests.

**Rationale.** Future reviewers can replay canonical pairs, independently parse
objects, compare declared rivals, and check the packet Racket authority without
copying claims from this report.

**Alternatives.** Embedding all evidence in prose was rejected because it is easy
to stale and hard to rerun.

**Probe / failure mode.** The direct source packet relocates tools and authority
relative to the runtime layout, so `reference_probe.py` contains a small import
shim. Feedback F1 requests a shared public helper to remove that task-local code.

## D8 — Prior evidence was a lead, not a measurement

**Choice.** Record `review-f488e46623fb0139:v0001` as the prior lead and rerun
the selected baseline.

**Rationale.** Its source hash matched this assignment's selected baseline and
its inert-key observation was useful, but review-index text can be stale or
unintegrated.

**Probe / failure mode.** The completed before battery independently reproduced
the contract failures. All after claims are tied to final hash
`92adf9c50a8f7c0346751867e759b5fbb4ca6f7742e71ac64b21a2d50cf8751e`.
