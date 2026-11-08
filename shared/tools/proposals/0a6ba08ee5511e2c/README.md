# ARC review release tools

These scripts finish and independently validate a `SEND-THIS-ARCpuzzles-review(...).zip` workspace without replacing packet-native evidence.

## Roles

- `invoke_arc_packet_builder.py` discovers the packet's own documented return builder and invokes only a concrete, local packaging command. It records discovery and command output.
- `finalize_arc_review.py` inventories repaired workspace state, records Git changes and safe fresh checks, builds a transparent fallback when no strong packet-native return exists, writes a manifest, and rejects unsafe archive paths.
- `select_arc_ready_delivery.py` chooses a recent repair-specific native packet when one exists; otherwise it uses the verified fallback. It checks CRCs, duplicate members, path traversal, suspicious secret/cache paths, repair-specific markers, and emits SHA-256 plus JSON validation.

## Safety properties

The tools do not modify the original upload. They exclude `.git`, caches, bytecode, virtual environments, large unchanged datasets, credentials-like paths, absolute paths, and `..` archive traversal. The final selector copies a packet byte-for-byte; it does not rewrite a native packet.

## Typical sequence

```bash
python invoke_arc_packet_builder.py || true
python finalize_arc_review.py
python select_arc_ready_delivery.py
```

The scripts in this bundle retain the concrete source filename from this review. A future agent should parameterize the `SOURCE`/output constants or replace them before use on another packet.
