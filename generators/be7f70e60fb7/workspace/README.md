# Workspace

The selected implementation is `../generator.py`; workspace files are reviewer tools and are never selected as runtime generators.

## `audit_curriculum.py`

Run a deterministic semantic audit over any seed prefix:

```bash
python3 generators/be7f70e60fb7/workspace/audit_curriculum.py --seeds 100
python3 generators/be7f70e60fb7/workspace/audit_curriculum.py --seeds 100 --json /tmp/be7f70e60fb7-audit.json
```

The probe checks all bands and profiles for deterministic generation, exact override observability, self-check validity, non-identity outputs, four-example lesson identifiability, and refutation of every declared rival.
