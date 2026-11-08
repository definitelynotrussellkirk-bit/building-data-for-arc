# Memory-safe review-packet extractor

Optional review utility; it does not replace any shared packet command.
Use it on an intact packet ZIP to reduce duplicate immutable file data while retaining every declared path:

```bash
python3 memory_safe_extract.py extract SOURCE.zip DEST --editable-task 8b6a2892a064 --verify
python3 memory_safe_extract.py verify DEST
python3 memory_safe_extract.py detach DEST --task TASK_ID
```

Run from this directory, or supply the absolute script path. DEST must be new.
After extraction, use the packet's own review entrypoint and return builder.

The extractor verifies the manifest, rejects traversal, symbolic links, duplicate ZIP members, unsupported directory payloads, missing files, and wrong hashes. Byte-identical immutable files may be hardlinked. The explicitly editable task and all shared data remain independent copies. Omit --editable-task to keep every generator tree independently writable. Before editing a formerly immutable task, run detach; it breaks that task's shared links without changing file contents.

It copies file data in 1 MiB chunks. ZIP central-directory, manifest, and duplicate indexes still scale with file count; this is not a constant-memory extractor. Hardlinks require filesystem support and save duplicate data, not all path inodes. Output cleanup preserves a path created concurrently by another process.

Tests use small synthetic ZIPs and cover failure cleanup, exact hashes, mutable boundaries, and detach. The production review packet was initially extracted with the stock tool, then immutable duplicates were deduplicated as a resource workaround; that is separate from these 15 utility tests. This tool is proposed for future agents, not integrated into the frozen shared runtime.
