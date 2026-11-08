# Workspace

`semantic_probe.py` is a task-local, dependency-free semantic census for future
reviewers. It checks canonical pairs, exact axis boundaries in all three bands,
canonical profile scheduling, witness firing, named-rival separation, the
three-example lesson contract, unknown-override rejection, and the `no_anchor`
negative fixture.

From the task directory:

```bash
python3 workspace/semantic_probe.py --per-band 20 \
  --json-out workspace/semantic_probe_report.json
```

The selected implementation remains `../generator.py`; workspace files are
review aids and are never automatically selected.
