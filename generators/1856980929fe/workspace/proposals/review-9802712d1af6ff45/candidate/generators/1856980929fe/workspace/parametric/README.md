# Proposed `branch_mode` extension for `1856980929fe`

Status: **prototype / proposed, not selected for production or training**. The
production generator, canonical Racket program, `RULE_HASH`, and approved default
behavior are unchanged.

## Parameter

`branch_mode` is selected once from the deterministic episode seed and held fixed
for every demonstration and query.

| Value | Transformation |
| --- | --- |
| `both` | Canonical default: copy every green seed rectangle down-left and down-right at each rectangle-height level. |
| `left` | Copy only the down-left branch. |
| `right` | Copy only the down-right branch. |

The object role, rectangle extraction, vertical stride, copy size, clipping, and
color remain invariant. `materialize_rule("both")` is byte-for-byte the registered
canonical Racket authority.

## Sampling constraints

The prototype draws inputs from the selected canonical generator, rejects duplicate
inputs, and retains only inputs for which the three legal settings produce three
different outputs. It fails loudly after `--max-attempts`; it never clones queries
or silently lowers `--demos`/`--queries`. Public challenges contain demonstration
inputs/outputs and query inputs only. Hidden settings, seeds, programs, and query
answers remain under `private/`.

## Exact four-query evidence command

Run from the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/1856980929fe/workspace/parametric/prototype.py build \
  --seeds 30 31 32 \
  --difficulty medium \
  --demos 5 \
  --queries 4 \
  --max-attempts 256 \
  --out ../checks/parametric/1856980929fe-branch-mode-v2
```

This executes the exact materialized Racket program for all 27 episode labels,
checks every label against the independent Python mirror, checks the canonical
`both` program against all four registered canonical pairs, and writes three
complete episodes (one per setting).

Recheck the retained bundle, including all 31 Racket executions:

```bash
python3 review.py run python3 \
  generators/1856980929fe/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/1856980929fe-branch-mode-v2 \
  --rerun-racket
```

The verifier also checks exact generator/prototype/program source bindings,
visible-byte-derived IDs, sorted/unique public IDs, public/private file sets, path
containment and symlinks, public payload hashes, omission of query answers and
metadata, safe integer Racket literals, and each private setting-to-program
association.

## Scope and limits

Evidence is bounded to the stated seeds, difficulty, and retry limit. The
pairwise-distinguishing filter deliberately narrows the canonical input domain so
each demonstration directly identifies direction. This prototype does not alter
canonical approval, establish broad distribution calibration, or admit the new
settings to training.
