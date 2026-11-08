# Tool reproduction — ticket-bdb9a5b6599dee2d

**Status:** completed. **Proposed request disposition:** `partially_implemented_keep_open`.

The pinned request and every retained manifest asset verify exactly. Current shared semantic-check tooling already supports `LESSON_SCHEDULE_PERIOD`, retained schedule receipts, and exact period enumeration; the retained `dc155169ea57` census enumerates period 4 without errors. However, the production `export_dataset` → `generate_in_runtime` path exposes no schedule-receipt argument and contains no schedule-period enforcement.

Keep the request open, but narrow it to export/admission integration. Reuse the existing receipt/enumeration contract instead of adding another schedule scorer.

Evidence: `probe.py`, `probe.log`, and `result.json` in this directory. `probe-authoring-red.log` retains the preflight assertion correction. No shared source was modified and no fresh dataset export was run.
