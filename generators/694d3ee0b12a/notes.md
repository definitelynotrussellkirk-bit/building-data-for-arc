# Working notes: 694d3ee0b12a

## Review diagnosis — 2026-10-02

The imported generator modeled one arbitrary-size frame, while all six canonical inputs contain two or three separate 7×7 frames. Its `self_check` therefore rejected every canonical input. It also omitted `RULE_HASH`, exposed dead/singleton axes, accepted unknown overrides, never reached the canonical palette/profile, and had no executable shortcut curriculum.

The strongest canonical ambiguity is a **fixed local bottom-right key**: every canonical frame places its fill key at local interior coordinate `(5, 5)`. A learner can copy that cell instead of finding the frame-local non-marker color. The new generator always moves the first frame's key away from that location and declares the rival explicitly.

## Selected design

- Preserve the selected Racket rule unchanged and pin `RULE_HASH = "c13ecc4348dc"`.
- Generate exactly two or three nonoverlapping 7×7 frame workspaces.
- Use six deterministic canonical-scale scene profiles across easy/medium/hard.
- Vary one to three local row markers and one to three local column markers.
- Give each frame a distinct key color and ensure each later frame has an observable changed intersection.
- Keep only one honest public override axis, `scene_profile`; reject unknown axes.
- Add strict parsing, a Python rule mirror, three semantic rivals, three always-firing witnesses, lesson-identifiability checks, and deterministic mutation fixtures.
- Add focused task tests covering all six canonical pairs, schedule coverage, Racket-rule hash parity, shortcut refutation, override observability, mutation rejection, and two-demo identifiability.

## Verification

Baseline official status: 5 green, 1 advisory, 6 failed. Failures were `lint`, `selfcheck`, `defect_lint`, `dist_gate`, `profile_floor`, and `override`.

Revised official status: **12/12 green**. Highlights:

- canonical inputs accepted: 6/6;
- destructive mutations rejected: 45/45;
- Racket applications: 120, crashes: 0, Python mirror parity: 120/120;
- canonical profile: exact 55/60 and envelope 55/60;
- semantic strictness: 600/600;
- all three witnesses fired 600/600;
- all three rival claims verified;
- lessons identifiable: 12/12;
- override contract: 630/630 accepted with unknown keys rejected.

The fresh visible-only solve passed 3/3 demonstrations on revision 1. Earlier rule exposure is recorded honestly; masked-query correctness remains unknown by design.

## Remaining limitations

The generator does not yet explore frame sizes other than 7×7, more than three frames, repeated key colors across frames, multiple key cells, or distractor objects outside frame workspaces. These are intentionally excluded because they are not established by the canonical grammar. Any expansion should be added only with authoritative parity and new shortcut tests.
## Current reviewer considerations

Source SHA-256: `89c1d7b7cbc7ce45db5ba9c72040350c9ef1c3e329e4a507b8498eaa46401ddb`.

# Decision record: 694d3ee0b12a

## D1 — Keep the selected Racket rule; repair the generator around it

**Original rationale:** unknown. The baseline generator and its comments attempted the same broad frame/intersection idea but diverged sharply from the canonical scene grammar.

**Decision:** do not edit the canonical or bank rule. Pin the generator to `RULE_HASH = "c13ecc4348dc"` and require Python-mirror parity.

**Alternatives considered:** rewrite the rule to accept the baseline's arbitrary one-frame scenes; or weaken validation until those scenes passed. Both would redefine the task rather than fix the curriculum.

**Probe:** the revised mirror matched all six canonical pairs and 120/120 generated Racket executions.

**Failure mode/limit:** archival rule text remains stylistically divergent, though the selected active authorities are synchronized and execution parity passes.

## D2 — Model multiple independent frames

**Original rationale:** the baseline appears to have reduced the task to one frame, perhaps to simplify generation.

**Decision:** emit exactly two or three independent frames, matching canonical object count and requiring every nonzero cell to belong to one frame workspace.

**Alternatives considered:** one frame with more markers; an arbitrary number of frames; or a global parser with no frame count restriction. One frame teaches a first/only-frame shortcut. Arbitrary counts exceed evidence and complicate profile matching.

**Probe:** all six canonical inputs pass `self_check`; the `first_frame_only` witness fires 600/600.

**Failure mode/limit:** four-or-more-frame generalization is not taught.

## D3 — Use exact 7×7 frames

**Original rationale:** the baseline varied frame height and width even though the canonical demonstrations do not.

**Decision:** retain the demonstrated 7×7 local geometry and vary layout, markers, colors, and key position instead.

**Alternatives considered:** arbitrary rectangular frames or a mixed 5×5–10×10 curriculum. These may be valid extrapolations, but the selected rule's intended domain is not demonstrated strongly enough to justify them in training data.

**Probe:** canonical profile rose from 0/60 exact and envelope to 55/60 for each.

**Failure mode/limit:** a learner may still bind to 7×7 geometry. This is an explicit evidence boundary, not an accidental dead axis.

## D4 — Vary one to three marker rows and columns

**Original rationale:** the baseline required at least two of each, causing one canonical example to fail validation.

**Decision:** allow one to three row markers and one to three column markers per frame. Resolve the shared local `(1,1)` marker cell so it cannot be assigned both colors.

**Alternatives considered:** allow all one-to-five combinations; permit overwritten marker ambiguity; or force at least two markers. The selected range covers canonical low counts while keeping lessons readable.

**Probe:** all canonical inputs pass; 20/20 linter validation instances and 600/600 semantic draws are lawful.

**Failure mode/limit:** four- and five-marker axes are not generated.

## D5 — Make key discovery local and observable

**Original rationale:** all canonical keys happen to occupy local `(5,5)`, and the baseline did not explicitly challenge that coincidence.

**Decision:** choose each key from the interior, always move the first frame's key away from `(5,5)`, use distinct key colors across frames, and ensure the key does not erase the only selected intersection.

**Alternatives considered:** retain canonical key placement; move keys only occasionally; share one key color globally. The first option preserves the strongest shortcut, the second creates avoidable ambiguous lessons, and the third fails to test frame locality.

**Probe:** the fixed-bottom-right, global-first-key, and first-frame-only rivals are all refuted on every one of 600 semantic draws. The exact Racket replay is in `checks/shortcut-counterexample.json`.

**Failure mode/limit:** repeated key colors across frames and multiple key cells of the same color are not represented.

## D6 — Use six deterministic scene profiles

**Original rationale:** the baseline exposed many axes whose advertised values were dead, singleton, or invalid across difficulty bands.

**Decision:** use six explicit canonical-scale layouts and deterministic schedules per difficulty. Content remains seeded, while profile selection is observable and replayable.

**Alternatives considered:** random free placement; a large set of low-frequency layouts; or a single layout. Free placement increases overlap/validation complexity, a large set weakens coverage guarantees, and one layout teaches position shortcuts.

**Probe:** pooled 600-draw profile coverage included all six profiles; each medium/hard profile appeared and the easy schedule covered its four declared profiles.

**Failure mode/limit:** the six finite layouts remain learnable as templates, though frame-local positions, markers, keys, and colors vary.

## D7 — Collapse overrides to one honest axis

**Original rationale:** the baseline's numerous axes were partly cosmetic, partly inconsistent with band-specific ranges, and unknown names were silently swallowed.

**Decision:** expose only `scene_profile`, implement `observe_overrides`, and reject every unknown key.

**Alternatives considered:** repair every old axis; preserve aliases for compatibility; or remove all overrides. Repairing unsupported geometry would add invented behavior; silent aliases would keep the contract ambiguous; no override would lose deterministic profile targeting.

**Probe:** override contract passed 630/630 across 7 cases and 3 bands; unknown keys are rejected.

**Failure mode/limit:** fine-grained marker/key controls are intentionally internal rather than public axes.

## D8 — Make semantics executable

**Original rationale:** the baseline relied on prose and structural validation only.

**Decision:** add `rule_mirror`, `strict_canonical_like`, `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, `lesson_identifiable`, and `mutation_fixtures`.

**Alternatives considered:** prose-only notes or tests that inspect implementation details. Executable contracts are replayable by the official gates and directly measure curriculum ambiguity.

**Probe:** semantic gate passed with 3/3 witnesses firing, 3/3 rival claims verified, and 12/12 lessons identifiable.

**Failure mode/limit:** only three named rivals are encoded; future audits may find additional shortcuts.

## D9 — Add focused task tests

**Original rationale:** no task-local tests existed.

**Decision:** add seven behavior-level tests. Tests were written red-first for canonical acceptance, frame-count schedule, authority pin/parity, shortcut refutation, override observability, mutation rejection, and lesson identifiability.

**Alternatives considered:** rely only on the large battery or test private helper details. Focused tests give fast regression feedback, while the official battery supplies integration evidence.

**Probe:** the focused test file passes; the full after battery is 12/12 green.

**Failure mode/limit:** tests do not certify masked solve correctness or future authority changes.

## D10 — Stop at the demonstrated grammar

**Decision:** do not add variable frame sizes, four-plus frames, repeated local key colors, distractor objects, or multiple key cells in this return.

**Reason:** these may improve abstraction, but they are not compelled by the canonical examples. The highest-value verified repair was eliminating the actual one-frame and fixed-key shortcuts without inventing a new task.
