# Working notes: cb3541dd8827

## Current status

Version `2.0.0` is a constructive arbitrary-colour frame generator bound to the
unchanged canonical authority `RULE_HASH = "6f461f08806c"`. Final generator
SHA-256 is `dba114b475885e0e6af4b698085622a62bf3aaf87dffc09b75d0f0b547a30fea`.
The final 12-stage battery is green, 52 task-local tests pass, the required
rotation semantic gate passes, and both the 300-lesson random census and the
fixed-seed schedule-period census report no ambiguity against the declared
rivals. See packet-root `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json`.

## Intended rule and assumptions

- Background is color 0.
- Every meaningful object is an exact monochrome rectangular outline at least
  4×4, separated from every other frame by background.
- Each frame interior contains exactly one cell whose color differs from both
  background and the frame color, plus at least three background cells.
- The output fills that frame's entire strict interior with its own seed color.
- One to three frames are supported; frame and seed colors are sampled without
  replacement within a scene so multi-frame lessons expose independent roles.
- The selected Racket rule remains the label authority; `rule_mirror` is only a
  tested Python oracle.

## Baseline findings and reversal

The imported `1.2.0` implementation described “2-rect-frames” and validated
only color-2 borders, even though the canonical task contains arbitrary frame
colors. Its before self-check rejected two of the three canonical inputs,
lint lacked `RULE_HASH`, the override checker found 12,024 concrete findings,
and the semantic gate reported `NO_CONTRACT`. The baseline also advertised nine
axes, including dead singleton controls, an unimplemented `frame_h`, ordinary
negative fixtures, and ranges that disagreed with actual sampling.

The prior choice to treat color 2 as the frame identity was therefore reversed.
The current implementation discovers exact rectangular-outline components by
geometry, not numeric color, and owns all canonical inputs. The retained minimal
counterexample is
`counterexamples/arbitrary_colour_canonical_frame.json`; the regression is
covered by `test_canonical_inputs_are_owned_and_match_both_oracles`.

## Distribution decisions

The ordinary sampler is constructive rather than retry-based. A four-position
schedule cycles through:

1. `canonical_single` — 7×9, one frame;
2. `canonical_double` — 11×9, two independent frames;
3. `broad_double` — banded broad dimensions, two frames;
4. `broad_multi` — banded broad dimensions, normally three frames (two when an
   exact small override cannot geometrically fit three).

`EXAMPLES_NEEDED = 4` and `LESSON_SCHEDULE_PERIOD = 4`, so every ordinary
four-demonstration window traverses all branches. Three scheduled branches use
multiple independently seeded frames, and colors vary, refuting first-frame,
global-seed, frame-color, and color-2-only shortcuts. Exact dimension overrides
remain lawful across every declared value, difficulty band, and joint pair.

Only two public axes remain: `grid_h` in 7..20 and `grid_w` in 9..22. These are
pixel-observable, strict integer controls. Unknown keys, booleans, non-integers,
out-of-range values, invalid difficulties, and negative sample indices fail
closed. Removed pseudo-axes are not preserved as compatibility aliases because
accepting them would make typos and obsolete controls look successful.

## Executable semantic contract

`strict_canonical_like`, `SEMANTIC_WITNESSES`, `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, and `lesson_identifiable` make the training claim
replayable. The four named competitors are:

- `color_two_frames_only`;
- `single_global_seed`;
- `first_frame_only`;
- `fill_with_frame_color`.

The required semantic check measured 600/600 strict draws, 3/3 canonical inputs,
4/4 witnesses, 4/4 rival claims, 12/12 lessons, and 0/60 ambiguous rotations.
The larger production census materialized 300 lessons (100 per band), 1,500
pairs/rotations, 1,499 unique inputs, and zero ambiguity or scoring errors. Fixed
seed 0 exhaustively covered all four declared starts in all three bands: 12/12
lessons and 60/60 rotations were identifiable.

## Tests and reusable tooling

`tests/test_generator_cb3541dd8827.py` contains 52 focused regressions covering
canonical ownership and independent oracle parity, every exact dimension
boundary and joint override in every band, strict invalid calls, every cyclic
lesson start/query rotation, distribution support, declared witnesses, malformed
grids, structural mutations, real Racket parity, and hash-seed determinism.
The pre-fix run is retained at `checks/tdd-red/pytest.log` (39 failures, 13
passes); the final isolated task-test stage reports 52 passes.

`workspace/reference_probe.py` is a dependency-light independent geometric
oracle and shortcut toolkit for future agents. It deliberately does not label
examples; canonical Racket execution remains authoritative.

## Known limits and open findings

- The semantic evidence is finite and only covers declared rivals. It does not
  prove unique induction against every conceivable hypothesis.
- The random census has one duplicate among 1,500 materialized pairs; counts are
  reported as 1,499 unique inputs rather than claiming independence.
- Exact small dimensions can force the `broad_multi` branch to two frames. This
  is intentional and observable: exact dimension honesty takes priority over a
  hidden frame-count promise, and no `n_frames` axis is advertised.
- Some destructive color swaps remain lawful because the task is intentionally
  color-blind; mutation rejection is therefore not expected to be 100%.
- No canonical Racket row changed. Authority sync notes an unrelated archival
  representation divergence while selected execution parity passes.
- Audit-only target `0bd65c18b34c` has a reproduced tie-break teaching gap; it
  was not edited because audit targets are findings-only.
## Current reviewer considerations

Source SHA-256: `dba114b475885e0e6af4b698085622a62bf3aaf87dffc09b75d0f0b547a30fea`.

# Decisions — cb3541dd8827

## D1 — Keep the canonical Racket authority unchanged

**Original rationale:** unknown beyond the imported summary and code comments.
The canonical examples and Racket behavior consistently implement a color-blind
operation: an exact rectangular border encloses one differently colored seed,
and the seed fills that frame's interior.

**Decision:** pin `RULE_HASH = "6f461f08806c"` and repair the Python generator,
validator, and curriculum around that authority. Do not edit canonical data.

**Alternatives rejected:** narrowing the rule to color-2 borders would contradict
canonical inputs; changing the Racket row merely to fit the old generator would
turn a generator defect into an authority regression.

**Probe/evidence:** before self-check rejected two canonical inputs; final real-
Racket task tests, rule smoke, and authority sync pass. Failure mode if wrong:
Python labels could drift from selected execution. The independent oracle and
real Racket parity test guard that boundary.

## D2 — Replace the retry sampler with constructive frame slots

**Original rationale:** the baseline randomly attempted 1–3 color-2 frames and
could silently return fewer than requested after 80 retries. Its stated axes did
not match the actual geometry.

**Decision:** partition each canvas into one, two, or three separated slots and
construct one exact frame in each selected slot. Draw the frame within the slot,
then place exactly one seed in an interior with at least four cells.

**Alternatives rejected:** increasing the retry count would preserve silent under-
placement and make exact controls probabilistic. Letting frames touch would merge
same-color components and obscure frame ownership.

**Probe/evidence:** 600/600 strict semantic draws, 20,250 override draws, default
distribution tests, and structural mutation tests. Failure mode: a future change
to slot arithmetic can make a frame too small or merge frames; `self_check` and
focused tests reject that immediately.

## D3 — Expose only honest, observable dimension axes

**Original rationale:** the baseline advertised nine controls, including singleton
pseudo-axes, negative fixtures in the normal texture domain, and `frame_h` even
though geometry sampled it directly from an unrelated RNG.

**Decision:** retain only exact integer `grid_h` (7..20) and `grid_w` (9..22).
Require strict integers, reject booleans and unknown keys, and make every legal
single and joint override constructive across all bands.

**Alternatives rejected:** compatibility aliases would make obsolete names and
typos appear to work. An `n_frames` axis was not added because exact small shapes
cannot honestly promise three frames without changing the minimum dimensions or
allowing touching objects.

**Probe/evidence:** before override report had 12,024 findings; final override
stage accepts 20,250/20,250 draws over 225 cases and rejects the unknown-key probe.
Failure mode: future metadata/range drift; the exhaustive boundary matrix and
`observe_overrides` make it falsifiable.

## D4 — Anchor canonical profiles while retaining broad support

**Original rationale:** the baseline did not guarantee canonical-size support in
each band and failed the canonical profile floor.

**Decision:** use a deterministic four-residue schedule with 7×9 single-frame and
11×9 double-frame anchors plus broad two- and multi-frame branches. Broad shape
ranges increase with difficulty, while exact overrides always take precedence.

**Alternatives rejected:** sampling only canonical shapes would overfit a tiny
surface; unconstrained broad sampling would allow a band to miss canonical
profiles and weaken task identity.

**Probe/evidence:** final profile floor accepts 3/3 canonical inputs and records
33/60 exact hits: easy 10/20, medium 12/20, hard 11/20. Failure mode: deterministic
anchors reduce some dimension entropy; the two broad residues and random frame
geometry/colors retain substantial support.

## D5 — Use arbitrary distinct colors for role separation

**Original rationale:** the old implementation always painted frame borders color
2, accidentally permitting a color-specific shortcut despite a color-blind rule.

**Decision:** sample `2 × n_frames` colors without replacement from 1..9, assigning
independent border and seed colors. This guarantees each seed differs from every
frame color in the scene and multi-frame seeds differ from each other.

**Alternatives rejected:** allowing repeated seeds would be lawful but would weaken
routine lessons against a global-seed shortcut. Fixing a palette by difficulty
would invite numeric-rank heuristics.

**Probe/evidence:** the required semantic gate fires the non-2-frame witness in
586/600 draws, independent-seed witness in 446/600, and seed-vs-frame witness in
600/600. Failure mode: sampling without replacement caps practical frame count;
the task only needs one to three frames, so nine ARC colors are sufficient.

## D6 — Make four demonstrations the explicit lesson contract

**Original rationale:** baseline comments asserted four demos would refute rivals,
but there was no executable schedule or lesson hook.

**Decision:** set `EXAMPLES_NEEDED = 4`, `LESSON_SCHEDULE_PERIOD = 4`, and make
all four consecutive starts traverse the same four semantic branches cyclically.
Declare executable competitors for color-2-only, global seed, first frame only,
and filling with frame color; test every query rotation.

**Alternatives rejected:** three demonstrations can omit one scheduled branch and
need not jointly expose all roles. Pure witness frequency does not prove that a
complete lesson teaches the rule.

**Probe/evidence:** required smoke gate 12/12 lessons and 0/60 ambiguous rotations;
random census 300/300 lessons, 1,500 rotations, zero ambiguity; fixed-seed period
census 12/12 starts and 60/60 rotations. Failure mode: undeclared hypotheses can
still survive; the claim is explicitly finite rather than universal.

## D7 — Validate geometry independently of generation metadata

**Original rationale:** baseline `self_check` searched only color-2 components and
trusted too much of the generation path.

**Decision:** parse grids from pixels, find monochrome exact rectangular-outline
components, enforce separation/minimum size/one seed/at least three fill targets,
and ensure every nonzero non-border cell belongs to exactly one frame. Observe
axes from the returned grid, not RNG metadata.

**Alternatives rejected:** checking only generated metadata would not protect
replayed, mutated, canonical, or externally supplied inputs. Treating any bounding
box as a frame would accept incomplete borders.

**Probe/evidence:** canonical counterexample fixture, mutation tests, malformed-
grid diagnostics, canonical profile gate, and final self-check. Failure mode:
color permutations can remain lawful and therefore some mutation classes are not
rejected; this is correct for a color-blind task.

## D8 — Add an independent oracle and portable task tests

**Original rationale:** no selected task tests existed. The baseline root fixture
is frozen and was not an allowed patch target.

**Decision:** add 52 tests under the task's `tests/` directory and a reusable
`workspace/reference_probe.py` that independently recognizes frame geometry and
implements the intended rule plus shortcut outputs. Use `reviewer_support` root
and canonical helpers for portable layouts.

**Alternatives rejected:** importing private runner functions would couple tests
to implementation internals. Duplicating the generator parser verbatim would not
provide an independent check.

**Probe/evidence:** retained red run 39 failed/13 passed; green local run 52/52;
official isolated task-test stage 52/52; real Racket parity on 12 generated grids;
hash-seed determinism. Failure mode: both Python implementations could share a
conceptual mistake, which is why real Racket and canonical-pair checks remain.

## D9 — Preserve failures and report finite limits

**Decision:** retain the interrupted before aggregate, focused before failures,
red TDD output, final battery, task tests, semantic/census reports, audit probes,
and both solve episodes. Report 1,499 unique inputs rather than treating all 1,500
random-census pairs as independent.

**Alternatives rejected:** deleting failed evidence would obscure why the rewrite
was justified; claiming universal identifiability from four named rivals would
overstate the measurement.

**Limitations:** the broad-multi residue falls back to two frames when an exact
small override cannot fit three; no frame-count axis is promised. The schedule is
fully enumerated only at fixed seed 0, with wider random support sampled at 100
lessons per band. Canonical authority is unchanged, but an unrelated archival
copy remains divergent as reported by authority sync.

## D10 — Stop after a source-bound visible solve and fresh replay gate

**Decision:** prepare the post-repair solve only after final generator bytes were
fixed. One geometric frame-fill solver matched all four visible examples; record
earlier exposure `yes` and reference consultation `no`. Generate the source patch,
apply it from a fresh packet's `WORK/` directory after initializing that exact
directory as the isolated Git root, compare the generator hash, and rerun focused
tests before routine acceptance.

**Probe/evidence:** patch SHA-256
`9660db89362bd1146eaa317bb00873978d400e9e53711e62ed4f0f740bc57b84` passes
`git apply --check` and `git apply`, reproduces generator SHA-256
`dba114b475885e0e6af4b698085622a62bf3aaf87dffc09b75d0f0b547a30fea`, and
passes 52/52 portable tests (`checks/fresh-replay/summary.json`). The retained
first attempt initialized Git above `WORK/`; apply exited 0 while skipping the
intended paths, so it is preserved as a failed path-root diagnostic rather than
a pass.

**Failure mode:** editing selected task files after the solve or replay would break
the source chain. Any such edit requires regenerating the solve/replay evidence;
top-level report-only edits do not alter `patches/source.patch`.
