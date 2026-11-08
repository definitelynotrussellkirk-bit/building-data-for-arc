# Streaming review checkpoints

The checkpoint.py utility uses only Python's standard library. It reads file
contents in 1 MiB blocks and keeps path/hash metadata in memory. No catalog or
puzzle runtime is imported. Source trees, ZIPs, and destination paths must remain
unchanged by other processes during an operation.

Create a checkpoint outside the extracted tree:

    python checkpoint.py create original.zip /path/to/packet /shared/step-01.zip \
      --exclude WORK/.review/racket-runtime

The ZIP contains changed and added files, assignment contracts, frozen
.review/baseline files, and a CHECKPOINT.json receipt. Contract and frozen-baseline
protection applies to the packet's root or its WORK/ workspace layout. The receipt records the
exact original ZIP SHA-256, original packet-manifest hashes, per-file hashes,
permission modes, explicit directory exclusions, and missing original files.
Unchanged ordinary files are recovered from the original ZIP. Empty directories
and permission-only changes to unchanged ordinary files are not checkpointed.
There are no automatic exclusions. Exclusions that cover assignment contracts or
the frozen baseline are refused. Retain evidence unless an explicit directory
exclusion deliberately names a disposable runtime copy.

Successful creation certifies the captured bytes and receipt, not review
completeness: a checkpoint cannot recover files that were already absent from its
source. Inspect the deletion receipt, and checkpoint before beginning risky work.
The output must be on a filesystem that survives the execution session; being
outside the source tree alone does not establish persistence.

Restore over an independently prepared, complete fresh extraction:

    python checkpoint.py restore original.zip /shared/step-01.zip /fresh/packet \
      --fresh-extraction

This mode verifies every original file, the full file inventory, the original
packet manifest, and all checkpoint payloads before writing. Only verified
original bytes can be replaced; extra files or conflicting edits cause refusal.
There is no force option and no permission-repair fallback.

Alternatively, recover only saved files into an explicitly empty area:

    python checkpoint.py restore original.zip /shared/step-01.zip /empty/recovery \
      --empty-checkpoint-area

The utility never extracts the entire original ZIP and never applies recorded
deletions. Neither mode redraws assignments. A restore validates all input hashes
and destination conflicts before installation, then installs individual files
atomically. The full restore is not a transaction: an I/O failure can leave a
partial restore, and its error lists the files already installed. Destination
paths must remain quiescent; symlinks are refused, but this utility does not claim
to prevent hostile concurrent filesystem substitutions.

Run the focused tests on tiny, synthetic ZIPs:

    python -m unittest -v test_checkpoint.py
