# Layout x motif family

finish=expand_only|highlight_largest; exact canonical default. Native counts: 2..6 demonstrations, exactly four queries. Alternative uses binary 4-connectivity after expansion and selects all maximum-size ties. It does not substitute layout component size or same-color connectivity.

From the outer packet directory:

```sh
python3 review.py run python3 -m pytest generators/public_eval_bf45cf4b/tests -q
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_bf45cf4b --root . --out ../checks/motif-new-preflight
python3 review.py run python3 generators/public_eval_bf45cf4b/workspace/parametric/authoring.py audit --preflight ../checks/motif-new-preflight/preflight.json --out ../checks/motif-new-audit --census-seeds 128
python3 review.py run python3 generators/public_eval_bf45cf4b/workspace/parametric/authoring.py verify-export --bundle ../checks/motif-new-audit/preview
```

Choose new outputs after source changes. The audit checks source hashes, protected labels, finite rivals, a protected causal counterfactual and strict public projection. Only one content-hashed public file is exposed at a time. Programs, settings, source indices, presentation order, future inputs and all query answers remain private. Never give a model the whole directory listing or private manifest.

Input-only generator controls: grid_h/grid_w 14..30; mask_h/mask_w and motif_h/motif_w 3..6; axis=horizontal|vertical|both; motif_colors 2..3. Products must be <=30 on each axis. Explicit controls are exact and invalid requests raise ValueError. The generator and native adapter use only adjacent task-local source and standard Python; no shared authoring helper is imported for sampling.

The catalog-bound task-tests command cannot address unregistered public homes. Run the explicit pytest command above; checks/verify_handoff.py independently relocates each task alone and executes labels with the protected packet runtime. Registration and owner-native acceptance remain separate.
