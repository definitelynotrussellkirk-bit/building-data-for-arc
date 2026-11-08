# Disagreement-Action Prototype and Canonical Contract Repair

## Native implementation plan (current)

Goal: qualify the existing mark/restore family plus restore-then-component-mark,
with the canonical generator and exact default program unchanged. The Python
adapter claims labels; protected Racket independently labels all qualified pairs.
`native_inputs.py` owns sampling/validation, `native_rule.rkt` owns the composed
rule, `adapter.py` supplies the native API, and `check_native.py` retains the
bounded teaching/export evidence. Existing `prototype.py` remains the legacy
two-setting authoring path. Specification: the current packet DUTIES.md,
PARAMETRIC-RULES.md and docs/parametric-promotion.md.

- [x] Implement and test the three-setting native adapter with 2–6 demonstrations
  and independently 1–4 queries, default 3+4. Preserve count-independent first
  query generation and strict scalar rejection.
- [x] Construct the first two common demonstrations to distinguish component,
  color, connectivity, first-tile, and size shortcuts. Add varied canonical
  samples and genuine 30×30 stress for both noncanonical rules: sixteen 6×6 tiles
  separated by two-cell bands. Canonical mark remains 29×29.
- [x] Execute bounded self-audit and public first-turn checks, build the native
  source/evidence manifest, qualify exact source, and retain a protected-Racket
  wrong-order witness. Hand off owner acceptance without self-approving.

The two-setting promotion alone leaves the required sequential dependency
unmet. Palette-only changes were rejected as cosmetic. The selected third rule
reconstructs the intact consensus first, then finds its same-color 4-neighbor
components touched by erasures and marks their complete extent. A deleted bridge
can change component membership; computing components on the anomalous tile first
is a concrete wrong-order rival. Same-color disconnected objects, diagonal
contacts, multiple touched components and untouched larger objects are retained.
The 30×30 layout is available only to noncanonical rules; common demonstrations
and first queries remain identically sampled across all settings.

Review focus: deletion of a connectivity bridge; disconnected and diagonal
same-color distractors; multiple damaged components versus largest-component
selection; minimum/maximum demonstration counts; future-query and private-answer
leakage. These are exercised in the native test and bounded audit, not a global
generator battery. Work occurs in this isolated extracted packet (no Git
metadata); the packet delta builder is the source-change authority.

## Legacy two-setting design (historical context)

The sections below describe the retained legacy prototype and its earlier canonical
contract repair. The current three-setting native design and delivery path are
specified above and in README.md.

### Intent

Preserve the original ARC family's decomposition: split the 29x29 input into twenty-five aligned 5x5 copies, compare corresponding coordinates, and combine cross-copy evidence. Keep the selected canonical rule unchanged while providing one nearby, executable rule variant and repairing concrete generator-contract defects found by the baseline battery.

## Goals

- Keep the selected canonical `mark` behavior byte-for-byte bound to the canonical Racket program.
- Add a separate prototype parameter `disagreement_action` with bounded values `mark` and `restore`, chosen once per episode.
- Execute exact Racket for all prototype labels and retain evidence proving the two settings differ on lawful inputs.
- Reject malformed call arguments, misspelled overrides, and invalid override scalar types before generation.
- Declare an executable semantic rival and lesson-identifiability hook so generated lessons explicitly distinguish marking disagreement locations from merely restoring consensus.
- Use the supported selected-only authority-sync workflow to align active `target_code` text while preserving archival `raw_code`.

## Non-goals and anti-goals

- Do not replace the production fixed-rule API with a parametric API.
- Do not change canonical labels, canonical Racket semantics, or `RULE_HASH`.
- Do not broaden the canonical teaching grammar from one erasure-corrupted copy to arbitrary substitutions.
- Do not present the proposed `restore` variant as approved or selected.
- Do not use palette-only or marker-color-only variation as the requested rule parameter.

## Constraints

- Production generation remains exactly one 29x29 input grid under the canonical rule.
- The prototype must live under `workspace/parametric/`; focused tests live in a new task-local test file, leaving the frozen fixture untouched.
- Hidden parameters, reference Racket, and query answers must be absent from public challenge JSON.
- Evidence must include exact Racket text, hashes, commands, generated inputs, Racket outputs, and a differing witness.

## Approaches considered

1. **Change marker color.** Rejected as mostly cosmetic: it changes the output palette but not the inference operation.
2. **Change corruption mode.** Rejected for this prototype because it primarily changes the input grammar and risks conflating oracle totality with the canonical erasure distribution.
3. **Change disagreement action (`mark` vs `restore`).** Chosen. Both settings require the same tile decomposition and cross-copy consensus. `mark` exposes uncertainty with color 1, exactly matching the canonical task; `restore` resolves each disagreement to the modal copy value. The output transformation genuinely changes while the family's reasoning structure remains recognizable.

## Canonical repair design

At `generate(...)` entry, validate `seed`, nonnegative `sample_index`, difficulty, public overrides, and the two legacy private fixture controls. Reject all other keys. Use exact scalar types (`bool` is not an integer). Preserve the existing domains and deterministic schedule. Add a canonical-output mirror only for contract/rival testing; Racket remains label authority.

The semantic rival is `restore_consensus`, which returns the modal 5x5 tile without marker cells. Every lawful generated input has at least one disagreement, so a witness fires in every band and the canonical Racket output differs. `lesson_identifiable` reports ambiguity only if this rival fits every demonstration but changes the query.

## Prototype episode design

`choose_parameters(seed)` deterministically chooses one action for the complete episode. `materialize_episode(...)` generates multiple lawful inputs through the selected generator, emits action-specific Racket, labels every pair by executing that Racket, and writes:

- a private manifest with parameter, exact rule, hashes, and all answers;
- a public challenge with demonstrations and a masked query;
- per-setting complete episodes;
- a cross-setting witness using the same lawful input.

The included evidence run materializes one `mark` episode and one `restore` episode and verifies that each episode's demonstrations reject the other action.

## Known limits

The prototype tests only two discrete actions and a bounded seed set; it is not production integration or universal identifiability proof. The production generator deliberately emits only erasures. Consequently, it does not distinguish the canonical total-disagreement oracle from an erasure-only marker rule on novel-color substitutions; that boundary is reported separately rather than silently broadened.
