# Current account: 8b320727aa72

## Intended rule and lawful input grammar

Partition the 29×29 input into twenty-five aligned 5×5 tiles separated by uniform one-cell lines. Exactly 24 tiles are identical and one tile differs only by erasing 1–5 consensus foreground cells to the modal tile background. Return the consensus 5×5 tile, replacing every coordinate where the 25 copies disagree with color 1. Canonical `RULE_HASH` remains `065574e7466b`.

The generator intentionally teaches the original 24-consensus-plus-one-erasure family, not every input on which the total Racket program can execute. Shape is fixed; diversity comes from occupancy, palette, anomaly position, erased coordinates, separator/background colors, and difficulty-linked profile weights.

## Current generator decisions

- Version `2.2.0` validates exact Python scalar types for `seed`, nonnegative `sample_index`, difficulty, all public overrides, and `anchor_position`; unknown overrides are rejected. `bool` is not accepted as an integer.
- Public `AXES` contain only exactly observable controls. Legacy fixture-only `tile_layout` and `disagreement_distribution` are validated and honored privately but not advertised.
- `strict_canonical_like`, a disagreement witness, the `restore_consensus` semantic/lesson rival, and `lesson_identifiable` provide executable teaching checks. Racket remains label authority; Python output functions are contract mirrors.
- Standard four-pair schedules retain the existing top-left-anomaly witness at `sample_index % 4 == 0` unless explicitly overridden.

## Parametric extension — current native delivery

The native path is `workspace/parametric/adapter.py` with `promotion.json`;
`prototype.py` remains the unchanged historical two-setting writer.
`disagreement_action` is fixed once per episode:

- `mark`: byte-identical canonical program; 29×29 canonical grammar.
- `restore`: recover the consensus; additionally supports 30×30 tiled inputs.
- `mark_component`: reconstruct consensus, then mark every cell in each
  same-color 4-neighbor component containing a disagreement coordinate.

This extends the earlier two-setting design because restore alone did not
provide the newly required sequential dependency. Recovering an erased bridge
changes component topology; the native wrong-order witness computes components
on the damaged tile before recovery and changes the result. The first two common
29×29 demonstrations distinguish all settings and ten nearby shortcut programs.
They retain same-color isolated/diagonal distractors, touching other colors,
multiple damaged components and an untouched largest component. Further draws
reuse the canonical sampler and transformed templates.

The API supports 2–6 demonstrations, default 3, and independently 1–4 queries,
default 4. Noncanonical fourth queries contain sixteen 6×6 tiles with width-two
separators on a full 30×30 canvas: 19 foreground cells per intact tile, three
missing cells, multiple components and occupied boundaries. Exact canonical
29×29/default behavior is preserved; no padding is presented as a size extension.
Input RNG streams are independent of requested query count and private action
except for the declared lawful final-query geometry. Both noncanonical settings
share that geometry.

The reusable `check_native.py` executes selected labels and finite rival programs
in protected Racket, writes complete private four-query episodes and one-query
public projections, and attacks serialized privacy/type/count/dedup boundaries.
The current run is `checks/8b320727aa72/native-audit/audit.json`: six episodes,
42 checked selected labels, 54 declared-program demonstration comparisons,
ten extra rivals on two component lessons, zero surviving extra rivals, six
first-turn parity checks and four expected malformed-export rejections.
This is a bounded learnability audit, not universal uniqueness or training proof.

A stale legacy writer test expected setting-named public files although the
writer already emitted content hashes. It now follows the manifest's public path
and verifies the opaque filename. The writer, canonical generator, original
canonical reference and frozen canonical test are unchanged.

Current native qualification passed for three settings on seeds 0 and 17 with
3 demonstrations and 4 queries; 29 focused tests pass. See
`checks/8b320727aa72/qualification/{qualification,execution}.json`, the current
`workspace/parametric/evidence/manifest.json`, and the two protected-Racket
wrong-order cases in `checks/8b320727aa72/causal/witness.json` with matching
`replay.json`. The cases use 29×29 and 30×30 inputs and change 5 and 10 output
cells respectively. Owner acceptance must be performed on the integrated live
bytes; no acceptance or training admission is claimed here.

## Authority

Two selected solution JSON `racket_target.target_code` fields were synchronized through the reviewed selected-only authority tool to exact canonical text. Archival `raw_code` is deliberately unchanged and remains execution-equivalent. Final authority status is selected-synchronized, archival-divergent, execution parity passing.

## Verification snapshot

Final generator SHA-256: `660a4802c3502d61eec22e3fb518a1d21c4d1f14d9318c9865ab8ec81c0a7040`.

- Strict after battery: 12/12 green.
- Focused repair/prototype/probe tests: 20/20 passed.
- Profile floor: 38/60 exact/envelope hits; easy 13/20, medium 13/20, hard 12/20.
- Lesson census: 300/300 materialized, 900 unique inputs, 0 production ambiguities and 0/900 rotation ambiguities against declared restore-consensus bindings.

The inherited frozen fixture still uses a fixed-depth canonical path and blocks portable aggregate preflight. It is frozen by assignment and was not edited; maintainer migration should use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

## Known limit and retained counterexample

The strongest canonical-fitting shortcut marks only foreground-to-background erasures. It fits all 8 stored canonical pairs. The exact retained counterexample in `counterexamples/oracle-totality-novel-color.json` changes one consensus-background coordinate of the anomalous tile to a novel color: canonical Racket marks it, while the erasure-only rival ignores it. Production does not emit this class, and `self_check` intentionally rejects it as `anomaly changes a consensus background cell`.

## Prior context used

After measuring the current baseline, notes `GNOTE-000833` (selected target versus archival raw authority roles) and `GNOTE-000838` (canonical erasure grammar versus total-oracle boundary) were used as leads. All claims above were remeasured against the final source in this return.


## Current public prototype identifiers

Public filenames now derive only from visible demonstrations and query inputs. The original source/report is retained under `workspace/parametric/evidence/reviewer-original/` and `reviewer-reported/`; the corrected Racket-backed export is in `owner-current/`. Four focused naming/writer checks passed across two tasks. This correction does not approve the prototype or rerun its full repair battery.
## Current reviewer considerations

Source SHA-256: `660a4802c3502d61eec22e3fb518a1d21c4d1f14d9318c9865ab8ec81c0a7040`.

# Decisions for 8b320727aa72

## D1 — Enforce a strict public generation contract (R1)

**Choice.** Validate `seed`, nonnegative `sample_index`, difficulty, every advertised scalar override, `anchor_position`, and unknown keys at `generate(...)` entry. Reject booleans where an integer is required.

**Rationale.** The before `defect_lint` reproduced accepted invalid calls, including a floating `corrupt_tile_index`. Exact overrides are an authoring contract; silently accepting malformed values creates unreplayable evidence and can hide caller mistakes.

**Alternatives considered.** Relying only on `gen_ctx` was rejected because it did not reject all scalar shapes or unknown keys. Coercing values was rejected because `24.75`, `True`, and misspelled keys should not silently select a different draw.

**Failure modes and limits.** This does not validate returned grids; `self_check` remains responsible for that. Validation intentionally treats exact Python types as part of the contract.

## D2 — Preserve but do not advertise two legacy private controls (R1)

**Choice.** Continue accepting validated `tile_layout` and `disagreement_distribution` overrides, but leave them out of `AXES`.

**Rationale.** The inherited frozen fixture uses them, so dropping them would break backward compatibility. They are not exactly recoverable from returned pixels, so advertising them as observable exact controls would violate the override contract.

**Alternative.** Adding them to `AXES` was rejected because multiple generation paths can yield the same visible tile or disagreement arrangement. Removing them was rejected because it would needlessly invalidate retained tests and authoring recipes.

## D3 — Add an executable restore-consensus rival and lesson hook (R2)

**Choice.** Declare `restore_consensus` in both semantic and lesson contracts, bind it to a disagreement-marker witness, and expose `lesson_identifiable`.

**Rationale.** “Return the modal tile without marking uncertainty” is a natural nearby rule. It uses the same decomposition, so it is a meaningful teaching competitor rather than a cosmetic or unrelated rule. Every lawful production pair has at least one erased coordinate and therefore separates the two outputs.

**Evidence.** `checks/after/checks/8b320727aa72_after_semantic_gate.json` and `checks/lesson-census.summary.json`.

**Limit.** Finite checks against this declared rival do not establish unique induction against all possible rules.

## D4 — Use `disagreement_action=mark|restore` for the parametric prototype (R4)

**Choice.** Keep production fixed to canonical `mark`, and build a separate episode-level prototype with `restore` as the proposed setting.

**Rationale.** Both settings preserve the original object roles and reasoning: split into 25 aligned copies, compare corresponding cells, and combine cross-copy evidence. The action changes the transformation itself, not just colors or sampling. It is chosen once per episode, and demonstrations explicitly distinguish the setting.

**Rejected alternatives.** Changing marker color was too cosmetic. Changing corruption mode primarily changes input grammar and would confound the separate oracle-totality question. A larger menu of actions was rejected as unnecessary before the two-setting concept is evaluated.

**Limit.** The prototype is bounded, proposed, and not production-approved. Evidence covers two complete episodes and one shared witness.

## D5 — Keep the production grammar erasure-only (R5)

**Choice.** Do not broaden `self_check` or ordinary generation to arbitrary insertions/substitutions merely to teach the total Racket oracle outside the canonical family.

**Rationale.** All 8 canonical labelled pairs and the retained original-family decision describe 24 consensus copies plus one erasure-corrupted copy. Broadening the sampler would change the learned task distribution. Instead, retain a precise counterexample showing where the total oracle and the strongest canonical-fitting erasure shortcut diverge.

**Alternative.** Adding a low-rate novel-color corruption was rejected because it would alter the canonical input grammar and require a separate design/approval decision.

**Evidence and limit.** The erasure-only rival fits 8/8 canonical pairs. The separating input is intentionally outside the validator domain; therefore generated lessons do not teach this aspect of oracle totality.

## D6 — Synchronize selected authority text only (R3)

**Choice.** Apply the supported selected-only proposal to two `racket_target.target_code` fields and preserve archival `raw_code`.

**Rationale.** The active selected code should be exact canonical text. The raw source is an archival, execution-equivalent spelling and should not be rewritten merely to collapse textual groups. Current evidence confirms selected equality and execution parity.

**Prior lead.** `GNOTE-000833` identified the intended role distinction; it was consulted after the before battery. It was not treated as a current measurement. `GNOTE-000838` corroborated the erasure-domain boundary. Current receipts and final checks are authoritative for this return.

## D7 — Report the frozen-fixture aggregate stage as blocked (B1)

**Choice.** Do not edit `tests/test_generator_8b320727aa72.py`; preserve its portable preflight failure and separately run every new test file.

**Rationale.** The packet explicitly freezes that fixture and assigns migration to the library maintainer. Rewriting it to manufacture an aggregate pass would violate scope and erase useful evidence.

**Result.** The portable aggregate status is `preflight_failed`; the task-local repair/prototype/probe suite passes 20/20 under the protected Racket wrapper.

## D8 — Audit targets remain unchanged (A1, A2)

The assigned adversarial reviews are source-bound findings, not repair assignments. I retained probes and authoritative outputs without modifying either generator. Their combined audit presets also report missing task-local semantic/test contracts; those generic preset findings are secondary to the concrete reproduced defects in `AUDIT.md`.
