# Working notes: 1c2f874f3e82

## Baseline

Selected baseline: version `2.1.1`, SHA-256
`da460b1589c41a14a71ab96fd95c8211dad1ffac0bbf491b0edf9986d5bd8fd5`.
The associated-notes file was empty. A byte-for-byte baseline copy is retained in
`workspace/baseline_generator.py`.

The completed before battery had 3 failures (`lint`, `defect_lint`, `override`),
2 advisories (`profile_floor`, `semantic_gate`), and 7 green stages. Principal
issues were a missing `RULE_HASH`, generic/dead palette and texture axes, silent
unknown overrides, values rejected inside difficulty bands, unobserved source
size, and no executable shortcut/lesson contract.

## Repair

Version `3.0.0` is a deterministic constructive generator pinned to canonical rule
hash `bb27569b9c6f`. It exposes four exact axes only:

- `grid_h`: 10..14
- `grid_w`: 16..20
- `source_cells`: 3..7
- `n_markers`: 3..5

The source is connected and asymmetric. Marker colors 3/4/5 request identity,
clockwise-quarter-turn, and vertical-mirror copies. Backtracking places all stamps
fully in bounds, disjoint from input symbols, and pairwise disjoint.

A seven-slot schedule makes four-demonstration lessons teach the two strongest
canonical ambiguities: source truncation (fixed four/cap five) and first-marker-only.
Executable witnesses, rivals, canonical shortcuts, and `lesson_identifiable` are
part of the generator contract.

## Tests and tooling

`workspace/reference_probe.py` is an independent geometry oracle with optional
real-Racket parity. `tests/test_generator.py` covers canonical pairs, exact and
invalid overrides, deterministic difficulty behavior, semantic witnesses/rivals,
validator mutations, Python hash-seed independence, and Racket parity.

TDD evidence is retained in `checks/tdd/tests_red.log`, `checks/tdd/tests_dead_band_red.log`,
`checks/tdd/tests_dead_band_green.log`, and `checks/tdd/tests_green_final_candidate.log`.

## Final evidence

Final generator SHA-256:
`8889627d4db57759caf31c94e7d6ed2091456147393f8d91e20193c915136473`.

- full battery: 12/12 green;
- selected task tests: 33/33 passed;
- override matrix: 12,690/12,690 accepted, zero findings;
- semantic gate: 600/600 strict-valid, all three witnesses/rival claims verified;
- lesson census: 300 lessons and 1,500 query rotations, zero ambiguity;
- independent audit: 1,000 samples, zero validation/determinism failures;
- real-Racket parity: 35/35;
- post-repair visible solve: 4/4 on revision 1.

No Racket authority or canonical row changed.

## Known limits

The generator intentionally excludes clipping and stamp overlap so every semantic
feature remains visible. It fixes the role colors and uses a finite source-template
family (two bases per cardinality, eight orientations). Declared-rival evidence is
finite and does not rule out every possible template memorizer.
## Current reviewer considerations

Source SHA-256: `8889627d4db57759caf31c94e7d6ed2091456147393f8d91e20193c915136473`.

# Design decisions for `1c2f874f3e82`

## D1 — Preserve the Racket authority

**Choice.** Keep the canonical Racket program byte-identical and pin its normalized
rule hash as `bb27569b9c6f`.

**Rationale.** Independent reading, canonical examples, the task-local Python
oracle, and real-Racket execution all agree on the signed-offset transforms. The
measured defects were in generation, validation, control semantics, and teaching,
not in the reference rule.

**Alternative rejected.** Rewriting the rule to make clipping, overlap, or input
symbol retention easier to generate. That would change the task rather than repair
the sampler.

**Probe/failure mode.** `checks/final-probes/independent_audit.json` compares 35
canonical/generated inputs against real Racket with zero mismatch. Authority sync
and Racket lint are green in the final battery.

## D2 — Remove pseudo-axes instead of pretending they vary

**Choice.** Replace `palette_kind`, singleton `density`, and mixed helpful/degenerate
`texture` declarations with four rule-relevant exact axes: `grid_h`, `grid_w`,
`source_cells`, and `n_markers`.

**Original rationale.** Unknown. The imported code appeared to inherit generic
palette/texture boilerplate; the rule assigns fixed semantic roles to colors 1–5
and 8, so palette variation was not actually implemented.

**Alternative rejected.** Permuting role colors. The Racket authority treats the
numeric colors as fixed operators, so this would generate mislabeled inputs unless
the rule also changed.

**Probe/failure mode.** The before linter and defect linter identify the dead and
degenerate declarations. The final lint/defect-lint stages are green.

## D3 — Make every public override exact in every band

**Choice.** Legal domains are `grid_h=10..14`, `grid_w=16..20`,
`source_cells=3..7`, and `n_markers=3..5`. Difficulty changes the scheduled
default, not whether an override is legal. Unknown keys and non-integer values
fail loudly.

**Rationale.** A public exact axis must be observable and must not silently clamp
inside easy/medium/hard branches. The selected ranges include all canonical input
profiles while remaining constructively feasible for complete stamps.

**Alternatives rejected.** Keeping broader baseline dimensions (`7..16`, `9..18`)
would make some dense combinations hard or impossible without clipping. Declaring
many incompatibilities would preserve a nominal domain while making it misleading.

**Probe/failure mode.** The full Cartesian/single-axis matrix made 12,690 accepted
draws across 141 cases and 3 bands with zero findings. Invalid/unknown controls are
covered in `tests/test_generator.py`.

## D4 — Use connected asymmetric templates with complete visible stamps

**Choice.** For each source size 3–7, use two connected asymmetric base templates,
apply one of eight dihedral orientations, and place the anchor/source plus markers
with deterministic backtracking. Require every transformed stamp to be in bounds,
disjoint from all input symbols, and disjoint from every other stamp.

**Rationale.** Asymmetry makes identity, clockwise rotation, and vertical mirror
observably different. Complete disjoint stamps ensure every source cell and marker
contributes evidence rather than being erased by clipping or collision.

**Alternatives rejected.** Random-walk motifs plus rejection sampling reproduced
the baseline's weak guarantees and made exact joint controls hard to honor.
Allowing clipping would teach a second issue—boundary truncation—while concealing
the primary transform mapping.

**Probe/failure mode.** `self_check` reconstructs all stamps and rejects clipping,
input overlap, output overlap, disconnected sources, and transform-symmetric
sources. The independent audit found 0 errors in 1,000 samples.

## D5 — Schedule semantic witnesses rather than hope random sampling supplies them

**Choice.** Use a seven-slot schedule. Every four consecutive generated pairs
contain at least one 6/7-cell source and at least one repeated marker color.
`EXAMPLES_NEEDED = 4`, so each production lesson has four demonstrations followed
by one query.

**Rationale.** The canonical training demonstrations support a fixed-four-cell
shortcut; all canonical labeled pairs support a cap-at-five shortcut and a
first-marker-only shortcut. Purely random coverage is not enough if a specific
lesson can still leave one rival alive.

**Alternatives rejected.** Three demonstrations were insufficient to guarantee all
needed witnesses across every cyclic start while retaining control diversity.
Unscheduled random draws could pass aggregate distribution checks but fail an
individual lesson.

**Probe/failure mode.** `lesson_identifiable` evaluates the named rivals directly.
The required-rotation semantic gate and the 300-lesson/1,500-rotation census report
zero ambiguity.

## D6 — Declare executable rivals and witnesses

**Choice.** Declare:

- `fixed_four_source_cells` paired with `source_more_than_four`;
- `at_most_five_source_cells` paired with `source_more_than_five`;
- `first_marker_only` paired with `repeated_marker_color`.

The last two fit every canonical labeled pair and are listed in
`CANONICAL_SHORTCUTS`; all three are lesson competitors.

**Rationale.** Named prose claims are easy to overstate. Executable rivals let the
public gate verify both that the shortcut really fits the claimed evidence and
that the generated witness actually changes its output.

**Alternative rejected.** Treating generic geometric flips/identity as sufficient
shortcut coverage. Those are already ruled out by the canonical labels and miss
the task-specific ambiguity.

**Probe/failure mode.** The final semantic gate checks 60 firing examples per
witness/rival claim; the exact question witness is under
`checks/question-generator-shortcuts/`.

## D7 — Keep `strict_canonical_like` equal to the lawful generated manifold

**Choice.** Reuse the full `self_check` result for `strict_canonical_like`.

**Rationale.** The repaired generator intentionally emits only examples on which
all source cells and marker instances have visible, unambiguous effects. Canonical
inputs satisfy the same geometric contract.

**Alternative rejected.** A looser “correct colors and counts only” strict profile
would report examples as canonical-like even when stamps clip, overlap, or the
source fails to distinguish transforms.

**Probe/failure mode.** The semantic gate measured 600/600 strict hits and accepted
all 3 canonical inputs. The profile-floor stage is green in every band.

## D8 — Add an independent oracle and portable focused tests

**Choice.** Put independent geometry in `workspace/reference_probe.py`, separate
from production helpers, and use it in `tests/test_generator.py`. Include a
real-Racket parity test rather than trusting only the Python mirror.

**Rationale.** Reusing production `_transform` or `_stamp` logic in tests would
allow the same mistake to agree with itself. Portable root discovery and canonical
helpers avoid fixed-depth path assumptions in intake replay.

**Alternative rejected.** Testing only `self_check(generate(...)) == []`; that
proves internal consistency, not agreement with the immutable rule.

**Probe/failure mode.** 33 focused tests pass in the isolated task-test runtime;
35 independent cases match real Racket.

## D9 — Accept explicit distribution limits

**Choice.** Keep fixed role colors, complete/non-overlapping stamps, and a finite
source-template library.

**Rationale.** These restrictions make the intended transform relation visible and
falsifiable. They are appropriate for a generator whose purpose is teaching the
rule, not exhausting every lawful Racket input.

**Known failure mode.** A contrived solver can memorize the finite template family.
The 1,369 unique-input census and dihedral/placement variation reduce superficial
memorization but do not prove immunity to it. Future expansion should add more
constructive asymmetric source families without weakening stamp visibility.


## D10 — Replay the packaged delta in an isolated fresh extraction

**Choice.** Build an interim return, extract the original packet into a new directory,
initialize Git there, apply the exact packaged `patches/source.patch`, and rerun the
selected-task stage through the packet's Racket wrapper.

**Rationale.** In-place success does not detect an incomplete patch, an accidental
parent worktree, a nonportable test path, or a solve generated from different source
bytes. The fresh replay tests the artifact the maintainer will actually receive.

**Alternative rejected.** Treating the working-tree battery as sufficient. It verifies
the code but not the handoff transformation.

**Probe/failure mode.** `checks/fresh-handoff/replay.json` records isolated Git-root
confirmation, successful `git apply --check` and apply, 33/33 fresh tests, and equality
of the fresh source, isolated runtime, and frozen-solve generator hashes.
