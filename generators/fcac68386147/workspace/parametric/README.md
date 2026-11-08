# Proposed repeat-offset parameters (non-production)

This task-local prototype preserves the canonical reasoning for `fcac68386147`:
read the complete `n × n` source tile, then fill the output by looking up the
source cell with the same row and column residues modulo `n`.  It changes only
how many whole copies are emitted on each axis:

- `row_repeat_offset ∈ {0,1}` gives `n` or `n+1` vertical copies.
- `column_repeat_offset ∈ {0,1}` gives `n` or `n+1` horizontal copies.
- `(0,0)` returns the exact canonical Racket program byte-for-byte.

The two values are selected once from a deterministic rule-only seed stream and
stay fixed across the episode.  Input sampling uses a separate stream, so paired
settings receive identical lawful inputs.  Output dimensions distinguish all
four declared settings on every pair; the source tile, palette, periodic residue
lookup, and cell values do not change.

The prototype accepts `1..8` demonstrations and `1..8` queries independently,
with at most 16 total pairs.  The retained evidence uses three demonstrations
and four distinct queries for one episode per setting.  Public challenge files
contain only labeled demonstrations and unlabeled query inputs; hidden settings,
Racket programs, and query answers stay under private evidence.  Filenames are
the SHA-256 of the exact public bytes.

From the outer packet directory, run the exact four-query evidence command:

```bash
python3 review.py run python3 \
  generators/fcac68386147/workspace/parametric/prototype.py \
  --base-seed 20261023 \
  --demos 3 \
  --queries 4 \
  --out ../checks/fcac68386147/repeat-offset-evidence-v1
```

The command executes all four exact Racket programs through
`arc_repl.isolated_verifier.verify_candidate`, checks every returned grid against
an independent Python periodic-tiling mirror, verifies each episode against all
three declared rival settings, and writes a source-bound report plus separate
public/private artifacts.

This is proposed prototype evidence only.  It does not modify `generator.py`,
replace the canonical rule, refresh an approval hash, enter the production
parametric API, or establish training admission or measured learning benefit.
