# Native path-policy parameter for `db63430eeffa`

**Reviewer status:** ready for owner admission; not accepted and not training-admitted.

## Contract

One hidden episode setting is fixed across every example:

| `path_policy` | Protected-Racket transformation |
|---|---|
| `both` | Exact canonical rule: paint both diagonal-first and straight-first paths. |
| `diagonal_first` | Paint only the diagonal-then-straight path. |
| `straight_first` | Paint only the straight-then-diagonal path. |

`both` is byte-for-byte canonical Racket, SHA-256 `738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46`. The alternatives delete one uniquely guarded sibling loop while preserving endpoint detection and displacement decomposition.

Native files:

- `adapter.py`: exact source-bound `program(settings)` and `generate(seed, settings, demos, queries)` entry points;
- `promotion.json`: one setting, 2–6 demonstrations, exactly four queries;
- `evidence/manifest.json`: current source/evidence inventory used by qualification;
- `prototype.py`: deterministic authoring, verification, shortcut certificates, and causal witness helpers;
- `verify.py`: retained protected-Racket replay and public/private evidence writer.

## Lesson construction

Demo and query streams are independent and prefix-stable. Every input has exactly two color-8 endpoints on a zero background, unequal row/column gaps of at least two, and dimensions drawn from profiles spanning 7×7 through 30×30. Exactly four queries are emitted.

The first two demonstrations oppose both values of four visible features—left-to-right orientation, row-vs-column major axis, border contact, and large-grid status. For each selected policy, eight conditional fallback rivals are checked. A lesson is rejected unless every rival is disproved by demonstrations and would change at least one query.

## Sequential dependency

Step A reads the ordered endpoints and derives signed row/column deltas, step signs, diagonal length, straight length, and the major axis. Step B uses that intermediate to draw the selected segment order. The retained source-bound counterfactual flips only `major_is_row`; protected Racket changes 73 final cells. The detailed evidence is in `evidence/current/sequential-dependency.json`; packaging projects it into the exact source-bound replay contract at `checks/db63430eeffa/sequential-dependency.json`.

## Verification

- Focused suite: 39 tests plus 62 generated subtests passed.
- Retained verifier: 128 protected-Racket evaluations across all three settings; no declared or feature-conditional rival survived.
- Native qualification: six jobs (three settings × seeds 0 and 17), each with three demonstrations and four queries; the selected setting was the sole demonstration-only survivor.
- Public exports: three files passed exact visible-byte/ID, masking, integer-grid, and duplicate-input checks.

These are finite checks. Owner-side fresh qualification, witness replay, acceptance, and training admission remain separate mandatory steps.
