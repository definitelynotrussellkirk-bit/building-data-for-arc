# Working notes: 0a9e3d364bb3

## 2026-10-06 review-d3192d76dc7ddbba

### Baseline and prior lead

- Selected baseline generator SHA-256: `72b830df552a46ad27de60da75e75d7fd90cc1a95ddeb4afba4471ac0aac11d8` (`VERSION = 4.0.0`, `EXAMPLES_NEEDED = 4`).
- The retained associated review index was used only as a lead: it suggested that query rotation could hide the sole example refuting one of the three canonical-fitting rivals. I reproduced that against the selected source before editing.
- The ordinary before battery was 12/12 green, but `checks/lesson-census-before.json` measured 300/300 ordered lessons unambiguous and 675/1,500 rotated lessons ambiguous, with 900 rotation hook warnings. This is a curriculum/query-policy defect, not a label-authority defect.

### Repair decision

The four scheduled profiles are already individually exact, observable, and covered by the immutable baseline fixture:

1. canonical/plain anchor,
2. marker colour outside the key,
3. a later distractor colour that remains unchanged,
4. an exact midpoint marker using bottom/right.

A lesson with four demonstrations plus one query contains only one copy of three profiles. Holding one of those unique profiles out as the query can leave the matching rival consistent with every demonstration. The final repair changes only `EXAMPLES_NEEDED` from 4 to 7 and bumps the generator version to 4.1.0. Seven demonstrations plus one query span exactly two complete four-profile cycles, so every query rotation leaves at least one of every shortcut-killing profile among the demonstrations.

### Rejected iteration retained as evidence

An earlier iteration introduced a combined `complete_control` profile and kept four demonstrations. It passed a full 12-stage battery at source SHA `aa5f8596769839f47fded2ae14868c2758d7c53732198646579217f3d400e909`, but it required changing the assignment's frozen baseline test fixture and changed the established four-profile observation contract. That implementation was rejected. Its patch and hash are retained under `checks/rejected-complete-control/`; `checks/task-tests-final-red/` shows the restored immutable fixture rejecting it.

### Final measurements

Final generator SHA-256: `42cf51fb28002b7a663a6816387b5050047798392f5f79827a7204336511ed42`. The Racket rule and `RULE_HASH = debd91c13f07` are unchanged.

- Final battery: 12/12 stages green (`checks/after-final3/`).
- Selected task tests: 19 passed, including all cyclic schedule starts and all eight query positions in all three bands (`checks/task-tests-final/`).
- Strict semantic gate: passed with required rotation identifiability (`checks/required-rotations/`).
- Production census: 300/300 materialized lessons, 2,400 labelled pairs, 0 ordered ambiguities, 0/2,400 ambiguous rotations, 0 hook warnings, and 2,400 unique inputs (`checks/lesson-census-final.json`).
- Task-local exhaustive probe: 192 lessons, 1,536 rotations, 16 seeds, all cyclic starts and all three bands; 0 failures. It also verified that each declared canonical shortcut fits all six canonical pairs (`workspace/probe_rotation_curriculum.py`, `checks/rotation-probe-final.json`).

### Limits

These checks cover the generator's declared rivals and finite sampled inputs. They do not prove uniqueness against every imaginable rule. The repair increases each generated lesson from five labelled pairs to eight, a deliberate token/data-cost tradeoff chosen to preserve the established input-profile and override contracts.
## Current reviewer considerations

Source SHA-256: `42cf51fb28002b7a663a6816387b5050047798392f5f79827a7204336511ed42`.

# Decisions

## D1 — Treat prior review material as a hypothesis, then reproduce it

The associated review index suggested a query-rotation weakness. I did not treat that as a result. I reran the baseline battery and a 300-lesson rotating census against source SHA-256 `72b830df552a46ad27de60da75e75d7fd90cc1a95ddeb4afba4471ac0aac11d8`; only then did I accept the defect. Evidence: `checks/before/` and `checks/lesson-census-before.json`.

## D2 — Repair the curriculum, not the rule

Racket labels, the Python mirror, canonical compatibility, overrides, grammar, and authority sync were already green. The measured failure was that one query position could remove the sole shortcut-killing profile from four demonstrations. Therefore I left the Racket/reference rule and `RULE_HASH = debd91c13f07` unchanged.

## D3 — Preserve the four profiles and use seven demonstrations

The schedule has four semantically distinct profiles. Supporting every one-pair query holdout requires at least two copies of every profile, so the smallest complete bundle under this existing schedule has eight labelled pairs. I chose seven demonstrations plus one query. This preserves all established grid distributions and makes the arbitrary-query policy explicit.

The exact final edit is intentionally small: `VERSION = "4.1.0"`, `EXAMPLES_NEEDED = 7`, documentation, a task-local exhaustive regression test, and a reusable probe. The probe is `repo/generators/0a9e3d364bb3/workspace/probe_rotation_curriculum.py`.

## D4 — Reject the combined-control profile

An earlier design combined multiple shortcut-killing features into one scene so four demonstrations could remain. Its advantage was lower lesson length. Its disadvantages were more serious: it altered the established observation/profile contract, complicated semantic witness interpretation, and required changing a fixture explicitly frozen by the assignment. I rejected it even though an intermediate battery was green. Evidence: `checks/rejected-complete-control/` and `checks/task-tests-final-red/`.

## D5 — Keep the immutable fixture immutable

The final `repo/generators/0a9e3d364bb3/tests/test_generator_0a9e3d364bb3.py` SHA-256 is exactly the assigned baseline hash `d99475980aace46a399cfbe9eb7bbbff9bae095cfbefcdec79c01eb2702aac1e`. New behavior is covered in a separate test file, `tests/test_rotation_controls.py`.

## D6 — Test both production ordering and arbitrary query rotation

An ordered-production pass is insufficient for this defect. I retained both verdicts:

- before: 0/300 ordered ambiguities, but 675/1,500 ambiguous rotations;
- final: 0/300 ordered ambiguities and 0/2,400 ambiguous rotations.

The census holds out every labelled pair once while preserving the others' order. The separate task-local probe additionally enumerates every cyclic start of the four-profile schedule, which the generic census does not promise.

## D7 — Derive the rival probe from generator declarations

The reusable probe iterates the actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` mappings rather than maintaining a copied name list. Before using a rival as evidence, it verifies that each declared canonical shortcut fits every usable canonical pair. This prevents the test from silently drifting away from the generator contract.

## D8 — Retain the lesson-length tradeoff

The repair increases the lesson from four demos plus one query to seven demos plus one query. I accepted that data/token cost because it is the minimum under the unchanged one-profile-per-pair schedule and avoids introducing a new composite profile. This is the only intended distribution-level restriction introduced by the repair.

## D9 — Keep audit targets findings-only

The assigned audit targets `6c5bf76aa982` and `5d1263287a4f` were inspected and reproduced but not modified. Their source hashes remain exactly those in `AUDIT_ASSIGNMENT.json`. Details are in `AUDIT.md` and `checks/audits/`.

## D10 — Replay the exact delta from a pristine packet

The final patch is generated from Git's staged index so new files are included. It was checked and applied after a hard reset and clean in an isolated fresh packet root. Two earlier replay-construction errors are retained in `checks/fresh-replay/` as failed iterations rather than being discarded.

# Decision ledger — review-8ba3331bdadf00a6

## D1 — Preserve the exact canonical default and vary marker scan direction

The native parametric family adds one episode-fixed setting, `marker_scan`.
`forward` loads the selected canonical Racket program byte-for-byte; `reverse`
uses the same key, body, bbox, quadrant, and midpoint semantics but retains the
last eligible non-key/non-0/8 body color instead of the first. Production
`generator.py` and canonical authority were not changed. Generator SHA-256
remains `42cf51fb28002b7a663a6816387b5050047798392f5f79827a7204336511ed42`;
canonical program SHA-256 is
`a1e1edd49bea980e1caf7584ef8a8d0322719fd06c3b36db5fe2c8b40e9c1bdb`.

## D2 — Make the A-to-B dependency genuinely input-derived

Step A scans lawful body cells in the declared direction and selects a color.
The selected color is the intermediate. Step B cannot choose its transformed
subset until that value is known: it recolors only matching body cells via the
2x2 key and full-body-bbox quadrant. A protected-Racket witness on a qualified
reverse episode selects color 1; substituting the forward endpoint color 5
changes 17 final cells. The witness is retained at
`checks/0a9e3d364bb3/causal/witness.json` with replay receipt beside it.

## D3 — Use constructive, prefix-stable teaching scenes

The sampler supports 2–6 demonstrations and 1–4 independent query prefixes;
normal qualification uses three demonstrations and four queries. Inputs are
setting-neutral and deterministic. The first two demonstrations deliberately
reverse numeric order, frequency, and key-membership correlations between the
forward and reverse endpoints. Every active endpoint color spans all four
quadrants, midpoint witnesses exercise the canonical bottom/right convention,
and the four queries have dimensions 9x11, 16x19, 24x27, and 30x30. The 30x30
case has three substantive body colors, boundary contact, and more than 96
nonzero body cells.

## D4 — Bound learnability claims to named rivals

The reusable `workspace/parametric/audit.py` checks the declared opposite scan,
identity, recolor-all, wrong midpoint convention, key-membership gating,
numeric min/max, frequency min/max, and top-left-key-color shortcuts. The
prequalification audit passed 72 episodes over both settings, seeds 0–11, demo
counts 2/3/6, and four queries. The source-bound postqualification audit passed
all four native jobs with only the declared setting surviving demonstrations.
This is finite rival evidence, not a proof of unique induction.

## D5 — Separate reviewer readiness from owner acceptance

Native qualification passed both settings at seeds 0 and 17 with 40 protected
Racket evaluations and source-bound `qualification.json`/`execution.json`.
Input-only public exports passed structure and byte-identity checks. The staged
task suite passed 24 tests. This return is reviewer-ready only: exact live-byte
owner integration, fresh native qualification, acceptance replay, and any
training admission remain pending.
