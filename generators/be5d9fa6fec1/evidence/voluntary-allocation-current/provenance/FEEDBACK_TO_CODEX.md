# Targeted tooling feedback

F1: Expose a standard-library unittest fallback as an explicit separate check
result when task tests are unittest-compatible but pytest is unavailable. The
current prerequisite gate blocks before useful task collection. Evidence:
`checks/portability/before/result.json` and
`checks/parametric/relocated-final/receipt.json`. A reusable isolated runner is
retained at `checks/parametric/relocated_checks.py`; it does not claim the
pytest aggregate passed. Consumer: review task-test tooling.


F2: Invoke the existing metadata-only byte/inode preflight before packet
extraction. The follow-up storage diagnosis measured about 104.5 MiB available
and fewer than 200 free inodes on the normal writable filesystem, while the
supplied archive requires 11,768 fresh file/directory entries and an estimated
219,590,656 allocation bytes before runtime/reserve allowances. The partial
scan found at least 24.96 GB in other visible workspace trees; the current task
uses about 62 MB on that disk. Directory footprints are not an additive
reconciliation of overlay filesystem accounting. Exact observations and limits:
`checks/storage/diagnostic.json`, `checks/storage/zip_preflight_actual.json` and
`checks/storage/zip_preflight_metadata.json`.

The existing proposal at
`repo/shared/tools/proposals/f067eb92fdc48c7e/checks/tooling/resource-preflight/packet_resource_preflight.py`
was reused unchanged: seven focused tests and four capacity boundary checks
passed; the supplied archive was correctly rejected on both available-byte and
inode budgets. `checks/storage/README_zip_preflight.md` gives the runnable
command, source hash and limitations. No duplicate helper or shared-runtime
patch was introduced. Consumer: review packet launch/extraction tooling.

This follow-up was explicitly requested by the user. Its evidence explains the
observed storage failure; it does not establish a model-specific Astra/Sol
quota. The original failure/workaround remains recorded in
`checks/environment.json`; the source-bound working tree was reused rather
than extracted again.

F3: User-requested extra allocation ticket `extra-ticket-61127ac40e9a0a16`
completed a uniform source-bound draw and one passing seven-label Racket probe
for `be5d9fa6fec1`. The runnable probe and visible-only four-query challenge are
under `checks/extra-ticket/extra-ticket-61127ac40e9a0a16/`; `REPORT.md` compares
three pinned families and proposes a future 20/30/10-minute authoring allocation
with a capped pilot and stopping rule. This is an evidence-informed proposal,
not a measured training optimum or changed dataset weight. Consumer: allocation
quality assessment. The original required ticket reports remain separate.
