# Reviewer workspace

`verify_role_lesson.py` replays the original seed-8 blue-only-blocker ambiguity and the repaired three-demo/four-query lesson through the supported Racket API. From the packet root:

```bash
python3 review.py run python3 generators/0b8ba9bb3c63/workspace/verify_role_lesson.py --baseline-generator ../.review/baseline/repo/generators/0b8ba9bb3c63/generator.py --out ../checks/lesson-regression-replay.json
```

The optional baseline path is available in the assigned working packet; omit it when only the exact retained counterexample is available. Use a fresh output path.

`parametric/` contains the separate proposed red/green transparency parameter, default canonical Racket source, CLI, evidence format and usage. Its independent demonstration/query counts and demo-only identifiability check support four-query episodes without exposing settings or query labels publicly. It is not part of the selected production transformation.
