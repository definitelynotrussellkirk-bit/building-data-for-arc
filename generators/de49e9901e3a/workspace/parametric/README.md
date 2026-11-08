# Proposed parametric extension for `de49e9901e3a`

This task-local prototype does **not** modify the production generator or its
selected canonical Racket authority. It tests one bounded episode-level rule
parameter:

| Parameter | Allowed values | Original/default |
|---|---|---|
| `eligible_objects` | `all`, `cross_only` | `all` |

`all` is the canonical behavior: replace every monochrome 4-connected object
with its same-color row×column closure (equivalently, its filled bounding box).
`cross_only` closes only objects that are exactly one complete occupied row
union one complete occupied column; all other objects are copied unchanged.

The setting is selected once from the episode seed and reused for all three
demonstrations and the query. Every retained episode includes non-cross objects
in both the demonstrations and query, making the two settings observably
different. The `public/` challenge files contain only labeled demonstrations
and unlabeled query inputs; they omit the hidden setting, Racket source, and
query answer.

From the outer packet extraction directory, run:

```bash
python3 review.py run python3 \
  generators/de49e9901e3a/workspace/parametric/verify.py \
  --out ../checks/parametric/verification.json
```

The verifier executes the exact Racket program for both settings through the
included offline Racket bridge, compares every result with the Python authoring
mirror, checks that training pairs refute the alternative setting, checks that
the query depends on the setting, writes opaque public challenges, and records
source/program hashes plus complete bounded evidence.

Limitations: only the declared two settings and retained seeds are tested. This
is a **proposed prototype**, not catalog approval, a production API, or evidence
for arbitrary seeds.

Retained reviewer-run evidence is available at [evidence/manifest.json](evidence/manifest.json).
The manifest maps original `checks/parametric/` members to task-local files and
records their hashes and source identity. Results remain reviewer-reported;
retention does not approve the proposed variants or add a production API.
