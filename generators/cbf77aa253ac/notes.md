# Current working notes: cbf77aa253ac

## Canonical rule and identity

Production v3.0.0 is unchanged, SHA-256
`147666965eb8730c3ceffd84b18a6765255815eb05ad11ea0bf36ae37c9101fb`,
normalized rule hash `356b20c90964`. Each guided 8-connected component chooses
its modal-payload denser side, with above/left tie preference, then clears,
restores and reflects cells using the guide-span/rounded-mean axis.

## Proposed parameter prototype

`workspace/parametric/prototype.py` adds episode-level
`side_policy = denser | sparser`. Default is exact canonical Racket text;
sparser changes only the two side comparisons. Each lesson fixes one policy.
Four required demonstrations cover both orientations and both density sides;
the default export has four distinct queries. Demo/query counts are separately
configurable in ranges 4..12 and 1..8. Secondary colors make total occupancy
favor the opposite side from the modal color, teaching the actual count rule.

All labels and ten declared candidates execute in Racket. Only demonstration
labels eliminate candidates; each emitted query has agreement among survivors.
The two retained default-count episodes eliminate all nine alternatives.
Public filenames hash exact visible bytes using reviewer_support; hidden
metadata and query answers cannot change identity. An independently found
duplicate-export sorting bug has a failing reproducer and a passing regression.
See workspace/parametric/README.md for commands, design and bounds.

Evidence in this return: checks/parametric/final-tests (16/16),
checks/parametric/episodes-final (two complete 4-demo/4-query episodes and six
canonical occurrences matching three unique inputs), and checks/adversarial
(1,220 sampled scenes, two maximum-count Racket episodes, final resolution).
The sampler is deliberately one straight guide/component, unique modal color,
nonempty unequal sides and in-bounds reflections. Irregular guides, mode/count
ties, clipping and component interactions are not sampled teaching coverage.
Finite rivals do not establish uniqueness against all possible rules.

## Test portability and unresolved production findings

The existing eight-test file now uses reviewer_support root discovery,
generator loading and canonical-pair normalization in the library and a fresh
runtime. Frozen fixtures, shared authorities and all assertions are unchanged.
Seven original tests pass; the exact-text authority synchronization test still
fails because archived and canonical Racket differ in whitespace. All four
base fields have the same normalized rule hash. The relocated combined suite
runs 24 tests: 23 pass, that one fails, no errors/skips. The normal pytest
aggregate was blocked by absent pytest; unittest receipts do not claim it passed.

The retained production audit remains needs_triage: ordinary lesson sampling
can leave a vertical query unidentified after horizontal-only demonstrations,
and production seed/sample_index scalar validation remains unresolved.
Prototype evidence does not repair the production scheduler, clear its audit,
approve the alternate rule, or admit training data. Next useful work is the
production lesson schedule/declared-rival repair and strict scalar validation;
authority formatting should be handled explicitly in its shared scope.

Current retained check limits: `generators/cbf77aa253ac/evidence/reported-check-limits-eb6777d8142a596c/manifest.json`. Relocated unittest remains23/24 with one exact-format assertion failure; pytest aggregate remains blocked by missing pytest. Production findings and prior audit resolutions are unchanged; prototype/test intake is not a clean aggregate pass.

<!-- arcpuzzles-current-storage-feedback:start -->
## Current storage feedback

Source-bound follow-up evidence: `generators/cbf77aa253ac/evidence/storage-feedback-current/manifest.json`. Reported byte/inode exhaustion explains this session only; no model-specific quota difference is established. Capacity preflight remains optional and no automatic gate was adopted. Prior23/24 unittest assertion failure, missing-pytest aggregate blocker and unresolved production findings remain unchanged.
<!-- arcpuzzles-current-storage-feedback:end -->
