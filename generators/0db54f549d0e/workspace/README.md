# Gallery authoring probes

`probe_counterexamples.py` prepares and verifies task-local legal counterexamples.
It reads canonical authoring data; never run it during a visible-only solve.
From the outer packet directory:

```bash
python3 review.py run python3 generators/0db54f549d0e/workspace/probe_counterexamples.py prepare --out generators/0db54f549d0e/counterexamples
python3 review.py run python3 -m arcpuzzles apply 0db54f549d0e --input generators/0db54f549d0e/counterexamples/input.json --out ../checks/gallery-counterexamples-racket.json
python3 review.py run python3 generators/0db54f549d0e/workspace/probe_counterexamples.py verify --out generators/0db54f549d0e/counterexamples --racket ../checks/gallery-counterexamples-racket.json
```

Use a fresh output path for a new public application. The five inputs cover two
lawful minimal-intersection cases, one generated teaching grid, and a canonical
input before/after a role-preserving color swap. Verification binds actual
reference results to the generator and rule hashes. The probe iterates current
shortcut/competitor declarations and separately tests numeric color rank.

Other reusable focused probes and infrastructure helpers are preserved under
`checks/` in the assignment return. They are not installed shared-tool changes.
