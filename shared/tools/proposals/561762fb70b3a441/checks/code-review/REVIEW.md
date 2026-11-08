# Independent repair code review: d65b2dd82d74

## Assessment

No Critical or Important implementation defect found in the reviewed generator,
regressions, or local probe. The constructive placement and exact integer controls
meet the stated repair requirements. One Minor curriculum/domain limitation is
recorded below; it does not contradict the explicit finite-rival assurance.

Reviewed generator SHA-256:
`7f44c068d13a203ee2362260fc6a98474ac0e36f66849bc25ce06956f7fb6dcd`.
Selected executed rule: `220859949b76`. Source edits were not made. The separate
blind task and its private sources were not inspected.

## Minor finding M1: scheduled span witness permits a broader shortcut

**Location:** `generators/d65b2dd82d74/generator.py:155-160` (scheduled layouts),
with the deliberate finite assurance at `generator.py:400-407`.

The shifted exact-span witness has two singleton keys of one color, while the
fillable same-key group uses another color. The other scheduled profiles use one
span per color. Consequently, a rival that leaves *every* color unchanged whenever
that color has more than one row span, and otherwise performs sorted disjoint
pairing, fits all canonical inputs and all default scheduled profiles. It does
not learn how to retain an eligible pair when a different-span distractor has the
same color. This is a remaining curriculum limit, not an incorrect label.

**Concrete witness:** 7x9, background 0, color 4 bars at columns 0 and 3 over rows
1..3, plus column 7 over rows 4..5. Input rows:

```text
000000000
400400000
400400000
400400000
000000040
000000040
000000000
```

`self_check` returns `[]`. The selected Racket rule fills columns 0..3 on rows
1..3, and preserves the bar at column 7. The rival returns the input unchanged.
A direct Racket execution confirmed that this rival fits all 3 canonical pairs
and 18 generated inputs (seed 17, indices 0..5, easy/medium/hard), but fails this
witness. Source structure establishes why it survives the scheduled profiles
beyond that finite sample. Explicit generic overrides can expose this limitation;
they are correctly excluded from the scheduled curriculum guarantee.

**Recommendation:** retain the finite-rival qualification. If stronger span
learning is desired, add a same-color matched pair plus unmatched-span distractor
to a scheduled profile and declare this rival. This is optional expansion, not a
blocker for the stated repair.

## Evidence actually exercised

- `PYTHONPATH=src:shared/runtime python3 -m pytest -q -p no:cacheprovider generators/d65b2dd82d74/tests/test_regression.py`: **81 passed**.
- An additional read-only sweep exercised every combination of 15 heights,
  16 widths, and the 10 feasible `(n_pairs, n_colors)` tuples: **2,400 draws**,
  one deterministic draw per tuple. Every draw passed self-check and exactly
  matched all observed requested axes. This is not an exhaustive RNG census.
- **900 default scheduled draws** across 25 seeds, indices 0..11, and three
  difficulty bands passed self-check and pair-count checks. Even profiles had a
  strictly closer middle gap and shifted span witnesses; odd profiles had an
  odd key. These additional checks used generator diagnostics, not independent
  label execution.
- The mixed-span rival experiment above executed **22 input labels through
  Racket** using `WORK/run_with_racket.py` and `Catalog.apply`. No Python-generated
  output was used as an authoritative label.

## Review observations and bounds

The minimum 6x9 shelf capacity supports four pairs without retry/drop; blank rows
and columns prevent same-color components from merging. Scheduled minimum-size
calculations leave room for the shifted bar, and both input reflections preserve
the intended witnesses while leaving Racket responsible for odd-key labels.
The alias/count refusal paths are explicit, and bool/float/string integer axes
are rejected before shared-context coercion. Supplied outputs, rather than a
Python authority mirror, drive declared rival comparisons.

The probe records independent Python mirror comparisons as diagnostics, checks
actual Racket/source identities, batches by the public runtime limit, reports
rival errors, and examines every single-query holdout in local six-draw windows.
Its pass is bounded to sampled raw draws and declared rivals, as its docstring
and report limits state; runner acceptance coverage and universal identifiability
remain outside that claim. Probe execution was not independently repeated in
this review. Plain pytest without the packet Python path initially failed to
import `reviewer_support`; the documented wrapper/environment resolves it.
The already-known witness mapping issue was excluded from new findings.

## Follow-up: selected repair for M1

The coordinator chose to repair M1 after this review. The hash above is therefore
an **intermediate** source identity; its successful checks must not be attributed
to the next source revision.

Executable rival (diagnostic only; supplied Racket outputs remain the oracle):

```python
def reject_color_with_mixed_spans(grid):
    groups = GEN._groups(grid)
    by_color = {}
    for color, top, bottom in groups:
        by_color.setdefault(color, set()).add((top, bottom))
    out = [list(row) for row in grid]
    for (color, top, bottom), columns in groups.items():
        if len(by_color[color]) != 1:
            continue
        for left, right in zip(columns[::2], columns[1::2]):
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    out[row][col] = color
    return out
```

For a reflection-safe scheduled witness that rejects both this rival and
`ignore_exact_span`, use eligible outer bars and a shifted middle bar:

```text
000000000
400040000
404040000
404040000
004000000
000000000
```

Here outer color-4 bars are at columns 0,4 over rows 1..3, and the middle bar is
at column 2 over rows 2..4. Racket fills the outer rectangle on rows 1..3 and
preserves the extra middle cell on row 4. This alone is a valid self-check input;
when used as the second band in the schedule, keep the existing separate
four-bar first band. The mixed-span-refusal rival fails by leaving the pair
unfilled. The ignore-span rival pairs columns 0 and 2, leaving the gap between
columns 2 and 4 incomplete. Both horizontal and vertical input reflection
preserve those differences. One blank column between neighboring bars preserves
same-color input 4CC eligibility even with overlapping row spans.

Review of the proposed arrangement found no geometric blocker: pair rectangles
may overwrite existing cells of the same color, the unpaired shifted endpoint
survives, and input components are extracted before any fill. Height 2 at the
6x9 minimum remains feasible. Actual scheduled counts change from 2,2,3 to
2,3,3. The current `_has_mismatched_spans` diagnostic also needs adjustment:
its `all(len(cols) == 1 ...)` condition assumes only singleton keys and would
miss the new paired-key-plus-singleton witness. New final-source verification
and rival evidence are required after the source change.

## Final-source addendum: mixed-span repair verified

Reviewed final generator SHA-256:
`7a54fb01857dcbd6637c26bd114eccfe103f6ef3f910b7ce777cb6233b7b5578`.
Executed reference rule hash remains `220859949b76`; executed rule-text SHA-256:
`c393676560f1b53319e86515d29f8dad74c0101aaf830805cd36aed28e6f6d2e`.

**M1 is resolved for this source.** Inspection confirmed the matching outer bars
and shifted middle bar at `generator.py:155-161`, the actual/default pair schedule
2,3,3 at lines 32 and 186, the new refusal rival at lines 355-366, and the updated
span witness plus explicit rival mapping at lines 382-418. The module now declares
eight rivals and eight witnesses. No new Critical, Important, or Minor finding
was identified in this delta review. No further rival search was performed.

The selected Racket check passed **36 labelled cases**: six default even-profile
bases (seed 17, indices 1 and 4 in each difficulty band), plus three direct 6x9
even-profile bases (one per difficulty band). Each base was checked under all
four combinations of vertical/horizontal reflection. Every case passed
self-check, had exactly three pairs, retained the closer-middle-gap and mixed-span
features, and refuted both `reject_color_with_mixed_spans` and
`ignore_exact_span` against its executed Racket output: **36/36 refutations for
each rival**. Source/rule identity was checked on execution and source hash was
checked again at the end. The 6x9 bases intentionally invoke the scheduled-layout
helper; public explicit size overrides use generic placement and are not claimed
to retain this scheduled witness.

Actual command, executed from `WORK/repo`, exit status **0**:

```bash
python3 ../run_with_racket.py python3 ../checks/code-review/final_source_check.py
```

Retained exact command and results:

- `checks/code-review/final-source-command.txt`
- `checks/code-review/final_source_check.py`
- `checks/code-review/final-source-stdout.txt`
- `checks/code-review/final-source-stderr.txt`
- `checks/code-review/final-source-check.json` (all labelled inputs/outputs)

The coordinator reported 85 passing final-source regressions in the actual
wrapper run; this addendum does not claim an independent repeat of that run or
of the coordinator's final battery/censuses. Earlier 81-test, 2,400-draw and
900-draw results remain intermediate-source evidence only.
