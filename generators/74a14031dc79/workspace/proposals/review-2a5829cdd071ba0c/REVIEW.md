Task: `74a14031dc79`; assigned production source SHA-256 `11a12a0ad29bcf2ddc4bd744b1fc34ab0e1cf6fb30bf3ae9f966eaa8ca8078a3`.
Defect → repair: pending parametric export fixed from hard-coded 3/1 seed-ordered episodes to independent 3/4 counts and public-ID-sorted content-derived exports.
Production behavior: unchanged; canonical OR source and rule hash `582367af483f` remain fixed.
Built: occupancy-rule v2 writer/verifier, count/privacy adversarial checks, and a separate four-query Python+Racket public-focus extension for `16de56c4`.
Main verification: 100 selected-task tests passed; Python compilation passed; occupancy evidence replayed 21/21 labels, including 12/12 query labels.
Retained parametric evidence: 3 episodes, 9 demonstrations, 12 distinct queries, OR/XOR/AND all exercised, zero surviving declared parameter rivals.
Public focus: all 3 demonstrations replay in matching Racket; a 4-query proposed episode is retained, with 2 public predictions explicitly unverified.
Supplementary tickets: `258e1a721c75` has an ignored advertised override finding; `66e63986855b` has a lawful six-cell shortcut witness.
Remaining limits: finite declared rivals/seeds, 16-pair prototype cap, no variant approval, no public-evaluation query labels, no production parametric API.
Disposition: main repair is routine and source-bound; peer API finding needs maintainer attention.

## Concrete repair

The inherited proposed occupancy-rule prototype already separated canonical OR
from guarded XOR/AND alternatives, but its public writer leaked private batch
order through `episode-NNN.json` and fixed every episode at three demonstrations
plus one query. `workspace/parametric/prototype.py` now:

- accepts independent positive literal `demo_count` and `query_count` values;
- defaults to three demonstrations and four distinct queries;
- bounds total episode support at 16 pairs and uses bounded duplicate retries;
- writes canonical visible bytes under `challenge-<public_id>.json`;
- sorts the batch by public ID before assigning private episode ordinals;
- rejects duplicate/colliding public payloads;
- verifies deterministic replay, counts, distinct inputs, exact public bytes,
  content-derived identifiers, and every Racket-computed label.

The current retained run at `checks/parametric/occupancy-rule-v2/` uses seeds
1/0/5 for OR/XOR/AND. Its verifier reports 3 episodes, 21 total labels, 12 query
labels, and 3 public identifiers checked with status `pass`. The adversarial pass
at `checks/parametric/adversarial-v2/result.json` retains a lawful 12-demo/4-query
maximum case, rejects 13+4, proves private/query-answer mutations do not change a
public ID, proves visible-query mutation does, and rejects tampered public bytes.

## Public-evaluation focus

`workspace/public_focus_16de56c4/solver.py` is pinned to public challenge SHA-256
`04f2c3b7aed8c16f787c41eb38d771d28bed8c54f4c649596974d8457a24edfd`.
It identifies repeated same-color anchor groups, selects the orientation with more
groups, completes each arithmetic lattice, and treats a unique external on-lattice
different-color point as a recoloring endpoint. It reproduces all three public
training outputs. `rule.rkt` is the matching proposed Racket implementation; the
retained report executes it on all three demonstrations plus four distinct
queries (the two public inputs and two clearly marked support inputs), with exact
Python/Racket parity. The two public query predictions remain at
`checks/public-focus-16de56c4/prediction.json` and are unverified against hidden
evaluation labels.

That geometry does not preserve the selected family's two aligned panels and
cellwise Boolean comparison, so it was not forced into production. The separate
probe rejects tied orientation evidence and unsupported marker configurations.
The source provides only two public queries. The extra two are proposed support
cases, not invented hidden examples; their outputs establish execution coverage
for the proposed rule but not evaluation correctness.

## Supplementary outcomes

The API-boundary ticket for `258e1a721c75` is an actual finding: valid
`palette_size=2` and invalid `palette_size=999` are both silently ignored and
produce the same three-color grid as baseline. See `AUDIT.md` and the ticket
result for exact calls and hashes.

The adversarial-witness ticket for `66e63986855b` completed without a peer defect
claim. A current default `asymmetric_front` input was accepted by the task's own
strict manifold check, labeled by canonical Racket rule `e9ecd02cbe2e`, and
separated the canonical-fitting `copy_upper_half` rival on six cells.

## Verification and limits

Commands and evidence paths are recorded structurally in `RESULTS.json`. The
selected production generator and canonical data were not modified, so no broad
production battery or unrelated peer census was run. Evidence remains finite and
reviewer-reported; packaging grants neither variant approval nor training
admission.
