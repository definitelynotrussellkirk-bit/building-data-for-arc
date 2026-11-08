# Returned authoring-tool candidates

Inspected source from review-0987eedf78c5ead6, feedback F5. One hash-bound copy
of each lives in shared/tools/proposals; the links below locate it. These are retained
proposals, not automatically qualified shared tools or training-label producers.

- [retain_census.py](../../../../shared/tools/proposals/b9c06c8d7d6937e8/checks/retain_census.py): deterministic gzip, original and compressed hashes,
  byte-for-byte restoration, and refusal of unequal existing outputs. Shared
  use still needs bounded manifest fields and descriptor-bound file checks.
- [run_recorded.py](../../../../shared/tools/proposals/b9c06c8d7d6937e8/checks/run_recorded.py): exact command/source/timing receipt. Its original packet
  layout expects this script at `WORK/checks/run_recorded.py` with `WORK` below
  the packet root. Restore that layout before use; this archived location does
  not change its path contract.
- [materialize_generated_witness.py](../../../../shared/tools/proposals/75a9d5371ea44821/checks/local-windows/materialize_generated_witness.py): actual selected-generator input and public
  Racket comparison, exact source/rule identities, fresh output directory.
  Use its original `WORK/run_with_racket.py` wrapper. It does not admit data.

The directly usable task-owned diagnostic is `../probe_local_windows.py`; its
finite local-mask coverage and separate global witnesses are documented there.
