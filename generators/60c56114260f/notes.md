# Working notes: 60c56114260f

## Current rule and support

Sort isolated monochrome nonzero objects by their top row, then left column;
compare their normalized shapes under all rotations and reflections. Emit 8 for
equivalent pairs and 0 otherwise. Generated general lessons contain three to six
distinct-colored objects of equal size; the five public profiles retain the
canonical inputs. The production generator and canonical Racket rule are unchanged.

## Portable test repair

The inherited audit against generator SHA-256
`08e7159a23d9ae5c51e06e82e467e634d10acd954e48d7daa849f78ffed3401a`
was reproduced: official `task_tests` stopped before pytest with exit 2 because
fixed `parents[1]` resolved canonical data beneath the generator directory.
The tests now bind their own tree with `reviewer_support.find_root`, load the
selected source explicitly, and use the portable canonical path/pair helpers.
Base-rule lookup derives from that same canonical data root.

Verification evidence is in `WORK/checks/60c56114260f/`: before/after official
task-test results record the failing preflight and then 9 passing tests. Direct
repository execution also passes all 9. `final-parity-and-portability.json`
records actual Racket execution matching all five canonical labels and one
sample from each of the eleven general profiles. A bounded adversarial check
also passes canonical/public/source-pin tests from an unrelated working
directory containing an invalid canonical ledger and a decoy generator selected
by `ARCPUZZLES_HOME`; the explicit test-tree binding wins in both cases.

Replay the focused Racket/portability evidence from the packet root:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/60c56114260f/workspace/verify_review.py --out ../checks/60c56114260f/replay.json
```

The inherited audit index remains owner-managed; this repair provides evidence
for resolving its portability finding. The Racket sample is bounded and does
not establish correctness for all possible inputs. No semantic generator defect
was established by this review.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-061f1fc9b07a6663:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `08e7159a23d9ae5c51e06e82e467e634d10acd954e48d7daa849f78ffed3401a`. At disposition, audited bytes match the current source.

### Current decision

Accepted tests/notes repair uses portable explicit root/source/canonical helpers. Reviewer reports9focused tests and16Racket comparisons; production source unchanged. This resolves the known task-test lookup defect, not a broad semantic claim.

### Assessment or prior finding

## 60c56114260f

**Reproduced defect — portable task tests are not runnable.** The official isolated `task_tests` stage exits 2 before collection because `tests/test_generator_60c56114260f.py` sets `ROOT = Path(__file__).resolve().parents[1]` and then looks for `ROOT/data/canonical/puzzles.jsonl`. In the portable layout that resolves beneath `generators/60c56114260f/`, not the runtime root. The preflight explicitly recommends `reviewer_support.find_root(__file__)`, `canonical_path`, and `canonical_pairs`. Evidence: `checks/audit/60c56114260f-task-tests/progress.log` and `checks/audit/60c56114260f-task-tests/result.json`.

**Semantic spot-check.** I checked all five canonical labeled pairs against four plausible weaker equivalence signatures: equal cell count, equal bounding-box dimensions up to rotation, exact translation-normalized shape without dihedral transforms, and equal sorted row/column occupancy histograms. None fits all canonical demonstrations, so I did not establish a semantic shortcut defect. Source-bound probe: `checks/audit/60c56114260f/shortcut_and_portability_probe.json`. No generator repair was attempted.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-061f1fc9b07a6663-v0001/audit_assets.json), manifest SHA-256 `1789c47fbb9c88f1d115456ccd5bc90aa9e1f9f2a1cf5425dec86485d37e8692`.
<!-- arcpuzzles-current-audit-assessment:end -->
