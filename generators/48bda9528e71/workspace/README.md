# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reusable review tools

`probe_convexification.py` discovers the current generator's three rival
declarations, retains sampling metadata and source hashes, and uses the public
`arcpuzzles apply` command for independent Racket checks. It keeps Python-mirror
distribution measurements separate from reference-labelled cases. From `WORK/`:

```sh
python3 run_with_racket.py python3 generators/48bda9528e71/workspace/probe_convexification.py --baseline-generator ../checks/baseline-source/generator.py --out-dir ../checks/convexification-new --per-band 100
```

The baseline snapshot in this review is the exact original 2.0.0 generator.
Use a new output directory to preserve earlier evidence. The final return's
`checks/convexification/` contains the completed run, including actual outputs
for canonical inputs, eight minimum-size witness symmetries, a historical
witness, and generated examples from every schedule phase and difficulty.

`propose_authority_sync.py` builds or checks an optional, separate formatting
patch for the two selected authority JSON fields. It validates original or
patched whole-file hashes, the canonical rule text, and the catalog mapping;
it refuses unexpected input. Its `check` action is read-only:

```sh
python3 generators/48bda9528e71/workspace/propose_authority_sync.py check --repo . --state original
```

Run that command from `WORK/repo/`. The proposed patch and application guide
are in the return's `checks/authority-proposal/`. This tool does not select or
approve a shared change, rewrite archival programs, or change the Racket rule.
