# Workspace: independent review probes

The selected implementation is `../generator.py`. Files here are not selected automatically.

## `deep_audit.py`

A reusable, source-bound audit for generator `058ae70e4bdb`. It deliberately uses an independent connected-component oracle instead of trusting `rule_mirror` for expected outputs. It also discovers the generator's current `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `PROFILE_WITNESSES` declarations at runtime, so declaration drift cannot silently leave a copied rival list stale.

Run from the packet root through the Racket wrapper:

```bash
python3 run_with_racket.py \
  python3 repo/generators/058ae70e4bdb/workspace/deep_audit.py \
  --samples 50 \
  --schedule-starts 100 \
  --out checks/deep-audit.json
```

Inside this review packet the equivalent runtime-relative command used `generators/...` and wrote `../checks/deep-audit.json` because `run_with_racket.py` executes payloads from `repo/`.

The report includes:

- source and tool SHA-256 hashes;
- exact-profile draw and uniqueness counts;
- independent-oracle, self-check, strict-profile, replay, observer, and non-identity results;
- canonical shortcut claims checked against all authoritative pairs;
- every hold-one-out rotation for each requested cyclic schedule start;
- all surviving declared rivals or other failures, capped only in console display, not in JSON.

Exit status is nonzero when any failure is recorded. Keep the JSON alongside the command in `RESULTS.json` so later agents can distinguish a measured pass from prose.
