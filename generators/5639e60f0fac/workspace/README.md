# Stencil review tools

`probe_role_positions.py` is an opt-in counterfactual gate for this task's fixed green3/cyan8 roles. It constructs translated versions of all three canonical masks, validates domain and separation, discovers declared rivals dynamically, and checks actual Racket labels independently of its Python expected output. Optional coverage scans 8 seeds ×12 indices ×3 bands and clearly labels these generated-label observations as a Python proxy.

From an extracted packet's WORK directory, use the public wrapper (substitute your independent Python environment):

```bash
python3 run_with_racket.py python3 generators/5639e60f0fac/workspace/probe_role_positions.py prepare --coverage --out ../checks/roles-input.json
python3 run_with_racket.py python3 -m arcpuzzles apply 5639e60f0fac --input ../checks/roles-input.json --out ../checks/roles-racket.json
python3 run_with_racket.py python3 generators/5639e60f0fac/workspace/probe_role_positions.py score --inputs ../checks/roles-input.json --racket ../checks/roles-racket.json --out ../checks/roles-report.json
```

Preparation writes the one-key public apply payload to `roles-input.json` and the complete source/rule/counterfactual metadata to `roles-input.meta.json`. Keep both: scoring compares the input payload with that sidecar and verifies each returned input, input hash, output hash, rule identity and output status. Existing output paths and identity mismatches are rejected. A PASS covers only the recorded task domain, sources, authority cases and declared rivals. Complete lesson assembly uses the shared production `lesson-census`; this tool does not replace it. A translated object can be illegal or change the intended rule in another task, so reuse requires an explicit domain/role adapter and fresh Racket labels.

No solve episode may consult this authoring tool or canonical answers.
