# Global-complement curriculum repair

**Goal:** Generate both outcomes of the unchanged canonical Racket rule, and
make shortcuts detectable in the lessons actually exported for training.

**Scope:** Only generator 27080597d778, its tests, summary, notes and workspace.
The assignment, canonical/base rules, approval metadata, shared tools and both
later audit targets remain unchanged. Python emits inputs, never training labels.

## Design

Use four observable profiles: exact complement, overlap without gaps, gap
without overlaps, and equal-count overlap-plus-gap. A seed-permuted four-slot
schedule covers all profiles in every four consecutive draws. Corrupt only the
right panel of a shared complementary construction, preserving a clean row with
a right-only cell; this makes the rule's global fallback observable rather than
an accidental local no-op. Vary masks, colors, heights and fault counts without
using an output oracle to accept inputs. Keep canonical-height/color anchors.

The exported-lesson tool must check the actual final demonstrations against
every query, independently re-execute the unchanged Racket rule, reject missing
contracts/labels, and shuffle demonstrations before export so the regular
schedule is not exposed as a positional shortcut. It must keep query labels and
source programs out of public challenge rows.

## Work and acceptance

- [x] Write failing tests for canonical rejection, missing fallback branches,
  ineffective/invalid overrides, malformed grids and rule hash; retain RED log.
- [x] Repair the generator and define semantic witnesses plus named wrong rules;
  test four-slot coverage, counterfactual edits, deterministic replay and palette
  and spatial equivariance against independent predicates.
- [x] Write then implement tests for a fail-closed JSONL lesson gate and a small
  research exporter; verify all queries after slicing/shuffling/filtering.
- [x] Run before/after 12-stage batteries, authoritative canonical/generated
  parity, task tests, public-interface tests and fresh-extraction replay.
- [x] Draw two audit targets once after generator work; retain findings only.
- [x] Write required documents, package through package_return.py, validate
  archive contracts, CRCs, hashes and patch replay; return one compact ZIP.

## Review focus

Three demonstrations can teach the wrong rule on a balanced-defect query;
a first good query must not hide a later bad one; same-color palettes must not
silently ignore color pins; malformed rows must return errors rather than
crash; changing only the requested branch must preserve the left panel.

No claim about Qwen training gains follows from generator checks alone.

## Execution record

The initial canonical/branch regressions failed 71/86 tests on the frozen source.
The first generator repair passed 86, then final-lesson tests and mixed-override
contracts brought coverage to 112. A packaged-runner resolution test brought it
to 113. Final code review found that malformed rival predictions could be mistaken
for falsifications; five additional red/green regressions bring the final task
suite to 118. No shared source or rule was edited to make checks pass.

The first after-battery passed eight stages then found six conditional inert-axis
cases. After explicit applicability contracts, all twelve stages passed. The
root evidence preserves both runs. Real three-demo exports were rejected, while
four-demo research exports and their final per-query rechecks passed. Two random
audits were completed without editing either target. Fresh-extraction patch
replay and final package validation are recorded in root checks/ and RESULTS.json.

The repository-wide run returned 130 passed and two two-second timeout failures;
both failed tests passed an isolated rerun. That full run is not relabeled green.
This is a source-local completion with an explicitly recorded suite limitation,
not a claim of a clean uninterrupted repository-wide test run or model gains.
