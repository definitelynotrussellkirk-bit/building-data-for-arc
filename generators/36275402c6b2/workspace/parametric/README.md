# Proposed border-policy parameter prototype

Status: **proposed and unapproved**. This task-local workspace does not alter
the selected production generator, canonical `RULE_HASH`, canonical ledger, or
approval state.

## Parameter

`border_policy` is selected once from the signed episode seed and remains fixed
for all demonstrations and queries:

- `recolour` — canonical/default. Apply every exterior `(replacement, source)`
  mapping to source-colour cells anywhere in the crop, including its border.
- `preserve` — proposed alternate. Apply the same mappings only to interior crop
  cells; source-colour cells on the crop border remain unchanged.

The largest-component crop, left-to-right legend interpretation, palette roles,
all interior substitutions, output dimensions, and input distribution remain
invariant. Inputs come from the selected production generator's odd profile,
which has exactly one noncorner border source. Episode slots deliberately cycle
through top, bottom, left, and right witnesses. Every demonstration and query
therefore distinguishes the two declared settings.

The default Racket program is byte-for-byte canonical and SHA-256 bound. The
alternate is produced by one guarded replacement of the canonical final mapping
branch. Every selected label and rival prediction is executed by the bundled
Racket runtime; there is no Python answer mirror.

Consecutive even/odd signed seeds share inputs while selecting opposite policies:
`(-2, -1)`, `(0, 1)`, `(2, 3)`, and so on. This preserves signed seed support and
isolates the rule change in paired comparisons.

## Materialize four complete episodes

From the outer packet directory:

```sh
python3 review.py run python3 \
  generators/36275402c6b2/workspace/parametric/prototype.py \
  --seeds 0 1 -2 -1 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/36275402c6b2-border-policy-v1
```

Demonstration and query counts are independently configurable from `1..8`.
The output directory must not already exist. Public challenge files are named
only by the SHA-256 of canonical visible bytes and contain demonstration
inputs/outputs plus query inputs. Seeds, policies, programs, source hashes,
rival predictions, and query answers remain under `private/` or the manifest.
Batch manifest rows are sorted by public ID, and duplicate visible payloads are
rejected.

## Focused checks

```sh
python3 review.py run python3 -m pytest -q \
  generators/36275402c6b2/tests/test_parametric_border_policy.py \
  generators/36275402c6b2/tests/test_parametric_evidence_verifier.py

python3 review.py run python3 \
  generators/36275402c6b2/workspace/parametric/verify_evidence.py \
  ../checks/parametric/36275402c6b2-border-policy-v1
```

The tests cover exact default authority, guarded variant materialization,
Racket execution on all four crop sides, canonical replay, signed/paired seeds,
strict counts, fixed episode semantics, three identifying demonstrations, four
distinct policy-dependent queries, public/private export boundaries, and
malicious public/private tampering. The verifier independently rebuilds every
episode, re-executes both Racket programs, checks all five labeled canonical
pairs, confirms content-addressed public files and sorted manifest rows, and
rejects source drift or untracked evidence files.

## Limits

This is bounded authoring evidence for two declared policies, not production
approval or training admission. Identifiability is checked only against the
opposite border policy, not arbitrary programs. The supported authored profile
contains exactly one noncorner border source per input; multiple border sources,
corners replaced by sources, and independently varying border-source counts are
not covered.
