# Current review notes: 18bd3cd2985e

Version 3.1.0; review assignment `review-15a8b14353eb3e0a`.
Generator SHA-256: `c90ed220b7bad99f254f4c1bf96336105b1298ee902eff503e1398d99c1c07a5`.
Canonical rule hash remains `70c5793d0c5a`; no canonical execution change.

## Intended transformation and domain

Count same-color singleton components using four-neighbor connectivity. Erase
those singletons. A hollow frame receives a scatter color only when the count
equals the number of local even-parity interior positions, starting at its
top-left interior cell. Unmatched counts and frames are legitimate. The actual
Racket rule chooses the first matching frame and permits competing colors;
generation deliberately avoids those ties using distinct frame capacities and
distinct singleton counts. All multi-cell objects are complete hollow rectangular
frames with empty interiors. Zero is background; foreground colors are sampled
without assigning a fixed numerical role. Diagonal same-color singletons are valid.

## Current choices and reversals

The imported generator silently ignored controls, accepted malformed objects,
could return a partially constructed scene, omitted RULE_HASH, and generated
only exact pairings. Rank matching and both count inequalities fit all eight
canonical records (four unique inputs). The replacement uses bounded construction
with explicit failure, strict observable controls, geometric validation, and
executable semantic rivals. New tests are under `tests/`; the frozen fixture and
shared implementation remain unchanged.

The default six-step mode sequence is all / partial / all / partial / all / none.
Any four consecutive draws contain two all scenes and two nonall scenes. With
three demonstrations and one query, every holdout keeps both kinds. Fully matched
scenes use at least two distinct capacities and opposite frame-origin parities, teaching
local checkerboards. Every nonall scene refutes rank and both inequality rivals.
Partial scenes replace a nonmaximum exact count by a missing positive count
below the maximum; none scenes include both an undersized and an oversized group.
The largest frame therefore always remains matched in partial scenes. This is a
deliberate curriculum restriction; none scenes still teach leaving it unfilled.

Two review iterations were reversed with retained failures. Oversized-only
partial counts let a smallest-fitting-frame rival survive; gap counts replaced
them. Randomly replacing the largest count let the opposite sufficient-count
rival survive; partial replacement now targets a nonmaximum capacity. A former
`sample_index % 4` shape branch also revealed the mode; canonical-profile versus
broad-profile choice now uses an independent keyed draw. Increasing the packing
area allowance from grid area / (3 * frames) to / (2 * frames) restores support
for the canonical 8 by 11 frame with capacity 27.

Canonical profile anchors receive a 75% prior probability; other draws vary
height and width independently over 12..30 and use two or three frames. Actual
strict profile-gate results were 43/60 exact and 51/60 envelope hits, with exact
support in every band. Difficulty changes maximum side/capacity: easy 6/6,
medium 9/16, hard 11/27. These are input-distribution choices, not new rules.

Exact controls are grid_h, grid_w, n_frames and match_mode. One frame with
partial matching is incompatible. Retired frame_size, palette_size,
position_bias and texture controls, plus unknown keys, now raise an error.
The default lesson guarantee does not extend to arbitrary forced overrides;
one-frame scenes cannot teach the two-origin-parity distinction by construction.

## Evidence and status

The final strict twelve-stage battery and 46 portable tests pass. The production
census covers 100 lessons per band: 300 lessons, 1,200 distinct inputs and 1,200
query rotations, with no ambiguity against seven distinct declared rivals.
Fixed-seed enumeration covers all six starts in all three bands: 18 lessons,
72 pair presentations and 72 rotations, containing 27 distinct inputs. The
independent joint-axis probe passes 1,152 cases and rejects 16 invalid probes.
These finite checks do not prove identifiability against every possible rule.

See this return's `checks/release-summary.json`, `checks/after-release/`,
`checks/task-tests-release/`, `checks/code-review-final/`, and the minimal
`counterexamples/count-equality-12x12.json`. Failed intermediate runs remain
separate. No pre-existing current `evidence/review_index.json` was present;
this review does not resolve unrelated historical audits.

Selected base authority target text was synchronized to canonical text using
the supported propose/apply mechanism. Only comments/trailing newline differed;
restricted-reader tokens and archival raw_code were preserved. The canonical
ledger and catalog authority bytes are unchanged.

## Separate proposed extension

`workspace/parametric/prototype.py` implements an episode-level
checkerboard_phase in {0,1}. Phase 0 reproduces the exact canonical text; phase 1
selects the opposite local parity and its corresponding floor-area capacity.
Two retained episodes contain three demonstrations and one query each, with
actual Racket labels and demonstrations that distinguish the phases. This is a
proposed, unapproved prototype; production generate() still uses the fixed rule.
## Current reviewer considerations

Source SHA-256: `c90ed220b7bad99f254f4c1bf96336105b1298ee902eff503e1398d99c1c07a5`.

# Design decisions and reversals

Task `18bd3cd2985e`; assignment `review-15a8b14353eb3e0a`.
Final generator: `c90ed220b7bad99f254f4c1bf96336105b1298ee902eff503e1398d99c1c07a5`.

## Authority and interpretation

The canonical Racket rule remains the label authority. In the generated domain,
it counts four-connected singleton components by color, erases them, and fills
the local even checkerboard in a frame when the selected-cell capacity equals
the singleton count. The eight canonical labeled records contain four unique
inputs; all eight remain accepted by both the ordinary and strict validators.
The frame capacity is ceil((height - 2) * (width - 2) / 2).

The actual authority has behavior beyond that domain: any multi-cell component
contributes its bounding box, matching uses the first matching frame, and
equal-count colors can overwrite each other. Those are facts about execution,
not invitations to introduce arbitrary filled objects or iteration-order labels.
The prototype's real-Racket witnesses record first-frame and overwrite behavior
in `checks/parametric/phase-v2/semantic-witnesses.json`; both ambiguous tie types
remain excluded from generation. We did not change canonical semantics to match
a simpler Python model. Python rival functions are hypotheses and never label
production training pairs.

The baseline authority-sync failure came from comments and a trailing newline
in two selected base target-code fields. The supported proposal and application
changed only `/racket_target/target_code`, after token-equivalence checks. The
canonical ledger, catalog authority and archival raw_code were preserved. The
proposal, application and recovery bundle are retained under
`checks/authority-sync/`. This is a textual authority repair, with no rule change.

## Distribution choices

| Choice | Prior rationale | Decision and evidence | Limitation or alternative |
| --- | --- | --- | --- |
| Exact matching | Baseline implicitly paired every frame and scatter group; a stated reason was absent. | Include all, partial and absent matches. Three count rivals fit all eight canonical records, but final nonall examples refute them. | Keeping only fully matched examples would perpetuate the strongest observed shortcuts. |
| Frame geometry | Hollow frames are supported by canonical inputs. The weak validator did not enforce them. | Validate the complete component boundary, positive interior and empty interior. Reject malformed/ragged/color-invalid grids. | This deliberately excludes the authority's broader arbitrary-bounding-box behavior. |
| Connectivity | Baseline scattering imposed eight-neighbor spacing without a documented reason. | Same-color edge adjacency is forbidden for singles; diagonal neighbors are allowed, matching actual four-connectivity. | No promise to generate every possible diagonal configuration. A real-Racket discriminator is retained. |
| Distinct capacities/counts | Avoiding ties makes the intended correspondence determinate. | Use distinct positive capacities and distinct singleton counts; sample separate foreground colors for frame and scatter roles. | Duplicate-capacity and equal-count overwrite cases are validator-excluded, even though Racket executes them. |
| Frame count and colors | Canonical inputs have two or three frames and five or seven total colors. | Default K is 2 or 3, with 2K distinct foreground roles plus zero. n_frames explicitly supports 1..3. | Four or more frames, shared role colors and arbitrary palette counts are outside this distribution. |
| Shape/profile support | Canonical dimensions give a defensible support floor. | Use four linked canonical H/W/K anchors with 75% prior probability, and an independent keyed 25% broad branch over dimensions 12..30. Final gate: exact 43/60, envelope 51/60. | Anchors are a prior, not proof of coverage of every canonical geometric arrangement. |
| Position and orientation | Baseline already varied placements. | Randomly pack separated frames; permit either rectangle orientation; fully matched scenes place the first two frame origins at opposite global parities. | The opposite-parity condition is intentional teaching support, not a universal property of lawful inputs. |
| Difficulty | Increasing size/count complexity is a reasonable input-level distinction. | Easy maximum side/capacity 6/6, medium 9/16, hard 11/27; retain linked profile support in every band. | Difficulty changes are not a measured human-difficulty scale. |
| Finite construction | The old retry/fallback path could return incomplete input. | At most 80 whole-scene attempts; bounded placement; reject unsuccessful attempts and raise if exhausted. | Finite probes cannot prove no future seed exhausts the bound. No exhaustion occurred in final tested populations. |
| Controls | Several old axes were advertised but ignored. | Honor exact grid_h/grid_w/n_frames/match_mode, observe them from the returned grid, and reject invalid values and unknown keys. | Retired frame_size/palette_size/position_bias/texture calls now fail loudly. This is an intentional compatibility change. |

The exact profile counts by difficulty are easy 13/20, medium 15/20 and hard
15/20; envelope counts are 19/20, 16/20 and 16/20. All 60 draws succeeded and all
eight canonical inputs were accepted. The morphology gate is only a marginal
diagnostic; its pass is not used as evidence that the lesson teaches equality.

## Lesson construction and why three demonstrations suffice for these rivals

The default mode sequence repeats all / partial / all / partial / all / none.
Every length-four window, including wraparound, contains two all scenes and two
nonall scenes. Holding out any one pair therefore leaves at least one of each.
The policy is three demonstrations plus one query, with any of the four pairs
eligible to be held out. Arbitrary reshuffling of unrelated draws or arbitrary
forced override sequences is not included in this contract.

An all scene contains two distinct frame capacities, so at least one interior
has more than one cell. It refutes erase-only and solid-fill. Its first two frame
origins have opposite global parities, so it also refutes each fixed global
checkerboard phase. A nonall scene refutes rank pairing and both natural count
inequalities. These seven executable alternatives are declared by the generator.
The required Racket-backed census checks their predictions and the independent
lesson hook; it does not rely on this explanation alone.

In partial scenes a nonmaximum capacity is replaced by a positive count missing
from the capacity set and below its maximum. The largest exact pair remains.
The <= rival must eventually place the unmatched small group. The >= rival
must incorrectly consume some remaining adequate group at the missing smaller
frame. Both disagree with exact equality. None scenes contain a below-maximum
gap count and, with the default two or three frames, an above-maximum count;
both threshold rivals then predict a fill where Racket leaves every frame empty.

This choice restricts partial scenes: their largest frame is always matched.
It makes both threshold directions visible in the bounded four-pair curriculum;
none scenes still demonstrate that the largest frame can remain empty. A future
longer or differently assembled curriculum could include largest-only mismatch
partials, but would need new teaching and rotation evidence. One-frame overrides
also do not inherit the default parity/rotation guarantee. The current hooks are
used as finite diagnostics for the default sampler, not universal certificates
for arbitrary user-constructed inputs.

## Reversals found during this review

1. **Initial repair: oversized-only partial mismatches.** That refuted rank
   pairing but allowed a smallest-fitting-frame rival to survive demonstrations
   at seed 0, indices 2/3/4, and disagree on the none query at index 5. The old
   source was reconstructed byte-for-byte and hash-checked; actual Racket labels
   show 22 differing query cells. See `checks/code-review/smallest-fit-witness.json`
   and the exact `source-snapshot-c1fe.py`. The final partial/none modes include
   undersized missing counts.
2. **Index-coupled profile branch.** A broad shape was previously permitted only
   at sample_index % 4 == 3, while all scenes occupied even indices. The shape
   leaked the matching mode. An independent keyed branch replaced it. The new
   red probes reproduced this for all, partial and none representative indices;
   the independent final 96-scene probe sees canonical and broad profiles in
   every mode.
3. **Packing area limit.** Grid area / (3 * frames) capped the canonical 22 by 26,
   three-frame scene at area 63, excluding the canonical 8 by 11 frame of area
   88 and capacity 27. The allowance is now / (2 * frames), giving 95 there.
   Capacity 27 is observed in the final hard sample; the joint boundary matrix
   still passes 1,152 cases.
4. **Second repair: replacing any partial capacity.** Replacing the largest
   count could leave a smallest-sufficient-group (>=) rival consistent with the
   demonstrations. Six new red regressions failed on the retained bc148 source.
   Partial replacement now chooses a nonmaximum capacity, and the seventh rival
   is executable. See `checks/regressions/surplus-red.txt` and `after-v3.txt`.

The first regression batch produced 22 failures and 3 passes on the baseline.
The next independent-review regression batch produced 7 failures and 3 passes
on the first repair. The final generator's 41 regression cases pass, and the
official portable task-test stage passes all 46 cases including five prototype
tests. All actual failed iterations remain in the evidence; there are no invented
negative solve attempts.

## Parametric extension: proposed, not production

The runnable `workspace/parametric/prototype.py` chooses checkerboard_phase once
per episode. Literal integer 0 uses the canonical local-even pattern and
ceil(area/2) capacity; literal integer 1 uses local-odd and floor(area/2).
The default phase-0 program is the exact 2,849-byte canonical text, including
its newline. Phase 1 excludes zero-capacity one-cell interiors. Unknown values,
booleans and invalid grids are rejected.

Seeds 0 and 1 select the two different settings. Each retained episode contains
three demonstrations and one query, using actual Racket labels for an even-area
match, odd-area distinction and unmatched case. Every retained demonstration
distinguishes the alternate parameter setting. Public challenge files contain
only train input/output pairs and test inputs; selected parameters, rule text,
seeds and query answers remain in the separate private evidence. Source and
boundary hashes are verified in `checks/parametric/verification.json`.

This tests two episodes and two explicit parameter hypotheses. It does not prove
arbitrary episode identifiability, training value or approval. The production
generator signature and fixed canonical rule were not replaced by this prototype.

## Completion evidence and practical limits

Final source-bound evidence consists of the twelve-stage strict battery,
46 portable tests, 300 production lessons / 1,200 distinct inputs / 1,200 query
rotations, and a fixed-seed enumeration of 18 starts / 72 rotations / 27 distinct
inputs. Counts from the fixed-seed enumeration include repeated inputs and are
not presented as independent sample counts. The earlier 203-lesson census failed
with ENOSPC while writing a checkpoint (worker exit 1, timed_out=false); it is
explicitly incomplete and is not part of the final passing claim.

Both solve lanes are retained. The blind task was completed before main-source
inspection; the post-repair solve explicitly declares earlier exposure and is
bound to the final generator. Each had one genuine attempt matching all three
visible examples. Both masked queries in each lane have unknown correctness.

The original extraction exhausted filesystem inodes. We preserved the original
ZIP and one immutable assignment draw, verified every archive member against
the pinned manifest, and moved to a full extraction on a separate filesystem.
The original verifier then passed without modification. A fresh replay streams
and verifies every original member again; unchanged reference bytes can share
verified hardlinks, but every patchable path and installed environment is
independent. Detailed replay receipts explain this storage adaptation and check
every changed path after applying the exact builder-produced patch.

No current explicit review index was present for the main task. This repair
does not close unrelated historical audits, approve training admission, establish
model mastery, or establish universal identifiability. The two assigned audits
are findings-only and are reported separately in `AUDIT.md`.
