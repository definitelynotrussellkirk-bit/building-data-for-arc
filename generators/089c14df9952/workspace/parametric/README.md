# Proposed target-policy parameter

Status: **prototype / proposed / unapproved**. This does not alter the selected
production generator, canonical Racket authority, approval hashes, or runtime
API.

The episode-level parameter is `target_policy`:

- `all` (original/default): stamp the transformed base decoration onto every
  matching target.
- `hinted_only`: stamp only targets that already carry a red-2 orientation hint.

Both settings retain the same base identification, D4 matching, hint handling,
accent copying, and boundary clipping. The four deterministic input fixtures do
not depend on the hidden setting and each separates the two policies. A setting
is selected once from the episode seed, then held fixed for all three
illustrations and the query. Every output is produced by the exact materialized
Racket program through the included protected Racket bridge.

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/089c14df9952/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/target-policy
```

Focused test:

```bash
python3 review.py run python3 -m pytest -q \
  generators/089c14df9952/tests/test_parametric_target_policy.py
```

The evidence command deliberately refuses seed sets that do not cover both
settings. Public episode JSON includes demonstration labels and an unlabeled
query only; hidden parameters, Racket text, and query answers stay under the
private evidence directory.
