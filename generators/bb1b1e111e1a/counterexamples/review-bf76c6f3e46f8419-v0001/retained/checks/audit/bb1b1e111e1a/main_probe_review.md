# Separate static review: 832404dc8a5c curriculum probe

No actionable correctness or provenance finding was identified in the read-only review. This is a static assessment; the reviewer did not execute the probe or tests or inspect post-repair solve files.

Reviewed files and hashes recorded at handoff:
- `generators/832404dc8a5c/workspace/probe_curriculum.py`: `86632a7f4f3f3b4d011bf19bcff29bdcba6be2097706ee65c61f0308ed6d8d72`
- `generators/832404dc8a5c/tests/test_curriculum_probe.py`: `29293aa2000cd192c84525ece97dda173b33b6e1e402809ec7ea86c2e40f3efd`

The probe executes the selected canonical lambda through RacketBridge (lines 62–67), retains the actual outputs as labels (114–126), evaluates rival outputs separately on copies (117–122), labels its larger census input-only (83–101), and expressly avoids claiming lesson/rotation identifiability (143–146). Source checks and hashes bind generator, probe and canonical program (109, 129, 133–136). Existing output paths are refused and creation is exclusive (155–163).

The tests cover rival discovery, changed/missing/extra cells, recipes, source hashes, boundaries, and overwrite refusal. The integration test's nested zip at lines 65–68 assumes equal shapes; this holds for the current rivals, and the diagnostic helper has a separate shape-difference test at lines 37–41. No change was requested for this bounded condition.

The `label_source` string assertion at line 57 is metadata coverage, not independent proof of label correctness. The source inspection establishes an actual Racket call path; runtime correctness was not independently re-executed by this reviewer.

