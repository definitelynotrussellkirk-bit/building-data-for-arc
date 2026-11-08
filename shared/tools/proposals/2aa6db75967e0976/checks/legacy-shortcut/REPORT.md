# Legacy lesson: correct query, zero shortcut refutations

**Measured result:** one ordinary lesson from the archived original generator
contains four demonstrations and one query, with five distinct inputs and five
distinct Racket outputs. Both explicit shortcuts match all five labels.

| Shortcut | Demonstrations matched | Demonstration refutations | Query correct | Whole-lesson refutations |
|---|---:|---:|---|---:|
| First cardinal marker-neighbour in row-major order | 4/4 | 0/4 | Yes | 0/5 |
| Object immediately above the marker | 4/4 | 0/4 | Yes | 0/5 |

Both candidates crop only their chosen object's cells and recolour those cells
to 8. They ignore object size. The above-marker candidate selects the component
containing the cell directly north of the singleton marker; it is defined on
all five retained inputs. Both score `survived_all`; `query_ambiguity` is false.

This supports a **proposed shortcut-coverage diagnostic**: after a shortcut is
explicitly declared as something the curriculum should refute, report a lesson
with zero refuting demonstrations even when its query is answered correctly.
The measured lesson would trigger that diagnostic for both candidates. Five
distinct outputs alone did not establish coverage of the size-selection rule.

## Provenance and public reference execution

Inputs came from exactly five archived calls:
`generate(seed=0, sample_index=i, difficulty='easy')` for `i = 0..4`, with no
overrides. Indices 0–3 are demonstrations; index 4 is the query.

| Identity | SHA-256 / hash |
|---|---|
| **Input-origin** archived generator | `b377352acbc2c53089f29f91ddd2d5f3e79d45411ea3264a0bc5f2cd86acb224` |
| Current selected generator recorded by **public execution** | `4b188d05f3c1b39b65cc288a07b39bef527b623df6a759f6facde2cda9cab75b` |
| Executed and catalog canonical Racket rule | `5af80c67d390` |

The public `arcpuzzles apply` command labeled the saved legacy inputs. Its
selected-generator hash records the current execution environment; it is not
the inputs' sampling origin. The canonical Racket is unchanged. All five public
application rows contain valid outputs and no errors, and their input arrays
were checked against the exact saved origin arrays before scoring.

Paths below are relative to WORK:

- `checks/legacy-shortcut/report.json`: compact machine report and both shortcut definitions/results.
- `checks/legacy-shortcut/input-origin.json`: archived source identity, exact arguments, input arrays/hashes, and shortcut predictions.
- `checks/legacy-shortcut/public-apply-result.json`: actual canonical outputs and public runtime/source bindings.
- `checks/legacy-shortcut/outer-command.json` and `checks/legacy-shortcut/apply-command.json`: the two actual command argument arrays, working directories, exit 0 receipts, and stdout/stderr paths.
- `checks/legacy-shortcut/public-challenge.json`: four demonstrations and query input only.
- `checks/legacy-shortcut/private-lesson.json`: complete labeled lesson with input provenance.

The source-bound executable is `checks/legacy-shortcut/probe.py`; it imports the
hash-checked archived generator through the packet's existing dependencies and
calls the supported public CLI for labels. No private runner was copied.

**Limits:** this is one fixed ordinary legacy lesson, not an all-seed census.
No Qwen model or inference policy was run. The diagnostic remains a proposal;
this evidence measures curriculum shortcut coverage and changes no gate,
generator, approval, or training-admission policy.
