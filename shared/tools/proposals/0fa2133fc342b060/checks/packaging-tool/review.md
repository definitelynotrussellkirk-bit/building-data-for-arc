# Packaging helper review and fixes

The task-owned helper is retained at `repo/generators/e58027e9749f/workspace/review_tools/`.
It passes a Path subclass to the unchanged official full-return builder and validator.
No official source, generator, shared implementation or RESULTS file was changed in this work.

## Resolved findings

1. The example command now uses cumulative `EXTRACTION-v2.json`, pinned to
   `31c4c524d2933b8425876483a614e9f8b07efd3aad8d02650d5e30a0ff350c20`.
   The older receipt cannot establish the later extraction history.
2. Before official imports, the CLI checks physical source hashes. Its import
   context then rejects any preloaded arcpuzzles module, source symlinks,
   adjacent sourceless bytecode and native extension candidates. It selects a
   fresh empty bytecode-cache namespace and disables bytecode writes for the
   complete official import, build and validation interval. Previous Python
   cache settings and sys.path are restored afterward. This closes the gap
   where verified .py bytes could be superseded by unchecked compiled code.

## Verification

Thirteen helper unittest tests pass with `ARCPUZZLES_TEST_SRC` pointing to the real
packet official source. The same thirteen tests collect and pass under pytest
using the installed task-owned dependencies. `tests.log`, `pytest.log` and
`commands.json` retain commands, outcomes and current authored source hashes.
The new tests were run red before implementation; the retained red logs show
missing isolation and acceptance of alternative executable modules, respectively.

The bytecode test first demonstrates ordinary import executing a poisoned
unchecked-hash .pyc, then proves the guarded context executes the intended source.
Another test demonstrates ordinary sourceless .pyc import, then checks fail-closed
handling of direct bytecode, native candidates and source-directory symlinks.
Preloaded modules are rejected before import. The original integration fixture
uses the real official builder: clean originals reach missing-report checking;
a modified shared original is rejected. Actual full-return packaging/replay
remains the parent's final step after reports are complete.

## Bounded trust

No remaining blocker was found in this review scope. The Python interpreter,
standard import machinery and helper are trusted infrastructure. Extraction
history is established by the independently pinned cumulative receipt, not
reconstructed from the present filesystem. Packaging must run in a quiescent
workspace; concurrent filesystem writers remain outside this adapter's guarantee.
Existing physical files remain authoritative, inventory-listed deletions fail,
and source ZIP members are fully hashed before fallback is enabled. The official
builder and validator retain responsibility for source scope and return semantics.
