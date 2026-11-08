# Source-bound packet recovery findings

These findings concern the supplied packet's infrastructure. They are based on read-only source inspection and metadata, not a generator audit. Numbered source excerpts and complete source SHA-256 values are retained in `evidence/packet-infrastructure-excerpts.txt`.

## Complete source materialization is required

In `review.py`, lines 96–106, the native `verify` command iterates every manifest-listed workspace file, requiring a regular nonsymlink file with the expected SHA-256. A partially extracted workspace cannot pass that verifier.

In `WORK/repo/src/arcpuzzles/review_full_return.py`, lines 370–373, the return builder verifies all frozen baseline files. At lines 399–404 it also verifies every manifest-listed repository source outside the selected repair candidates. Missing shared files prevent a valid official return even if the proposed repair contains no source changes.

A sparse extraction would therefore leave both initial verification and final packaging unsatisfied. This toolkit does not modify or bypass those integrity checks.

## The first draw has an unjournaled verification interval

In `WORK/repo/src/arcpuzzles/review_full_draw.py`, lines 207–217, the program chooses a seed/task and verifies the selected baseline and question. It constructs and commits the pending draw record only at lines 218–226.

The selected baseline includes every issued file under the selected generator, the complete canonical JSONL, and bound reference-authority files (`_base_paths`, lines 47–59). The baseline is copied after journal publication (lines 227–230).

**Consequence:** a missing selected input can fail before the pending record is written. Starting again against an incomplete extraction can choose a new seed rather than resume the original unrecorded selection. This is an inference from the source ordering; no real assignment was drawn to demonstrate it. We left the assignment undrawn.

## Measured capacity failure

The last actual extraction ran the final tested helper against the original complete ZIP. Full archive validation succeeded before extraction began. It published 6,256 members, then received `OSError` errno 28 while allocating the next temporary member. The receipt is `evidence/extraction-final.json`.

At the final workspace observation, the root filesystem reported zero available bytes and 1,136 available inodes. The partial extraction and its archive-identity record remain intact. No `WORK/ASSIGNMENT.json` or pending-main-draw record exists (`evidence/final-workspace-state.json`).

The 1,133,563,806 uncompressed bytes require 1,329,700,864 bytes when each file's content alone is rounded to 4 KiB blocks. That figure excludes directory allocation, baseline copies, runtime expansion, and check outputs. It is a storage estimate derived from ZIP member sizes, not an actual full-extraction disk-usage measurement.

## Source hashes

| File in the original ZIP | SHA-256 |
| --- | --- |
| `review.py` | `d4e6086ce6e1e09364bfda3c382244763fbdf521393d06d69731fd6f9c5e6c49` |
| `WORK/repo/src/arcpuzzles/review_full_draw.py` | `1d0795faef11f4fc71f7c2b997d882d8dd464f9bd576b787296e71f428635518` |
| `WORK/repo/src/arcpuzzles/review_full_return.py` | `a021d00ec056acbdf0958955f5d08f110bff934375a6dac397fc3f86089a2f74` |
