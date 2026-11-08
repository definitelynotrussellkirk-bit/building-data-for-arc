# Optional authority formatting synchronization: 48bda9528e71

The original battery failure is a difference in source formatting. The two
canonical `program_solution` records (original ledger lines 657 and 1261) have
identical formatted text. Both selected `racket_target.target_code` fields have
the same compact text. Whitespace normalization gives the same Racket source
hash for every authority: `b9f9e9bda3f360c20aa772dfedc3adc436e725f5f33659fc056cee0312ee293f`.

`generated/authority-sync.patch` changes only `/racket_target/target_code` in
these repository-relative files:

- `shared/data/base/solutions/augmented/aa62e3f4__9e325a53a30a.json`
- `shared/data/base/solutions/training/aa62e3f4__48bda9528e71.json`

It copies the existing canonical text into those two selected fields. The
canonical ledger, archival `raw_code`, metadata, examples and all other fields
are unchanged. The normalized rule hash remains `b9f9e9bda3f3`. The patch is an
optional shared-file proposal kept separate from the selected generator delta.
No active shared authority file was edited while preparing or testing it.

## Evidence

`generated/manifest.json` records original/patched whole-file hashes, the patch
hash, canonical and catalog inspection hashes, and exact source identities.
The task-local builder refuses unexpected authority file bytes, canonical task
sources, catalog mappings, or lexical constructs that would make its simple
whitespace argument invalid. Its `check` action writes no files.

`replay/receipt.json` and `replay/commands.log` retain actual commands, working
directories and exit codes for a tiny copied authority tree. The unchanged
checker reproduced the failure before application (exit 1, two active exact
groups) and accepted the patch afterward (exit 0, one exact group across all
four active authorities). Its resulting payload status is
`SELECTED_SYNC_ARCHIVAL_DIVERGENT`; the two preserved archival strings account
for that explicit status. Independent JSON comparison found exactly one changed
field per file. A deliberately altered file was refused with exit 2 and left
unchanged. The small temporary tree was removed after the receipt was written.

This replay tested text synchronization and patch guards; it did not execute
Racket. The already retained original battery evidence at
`../before/checks/48bda9528e71_before_authority_sync.json` reports execution parity
PASS for both distinct source texts on 2 train and 1 test pair each. A full
relocated replay with Racket is a separate check and must be reported separately.

## Reproduce the retained small replay

From `WORK/`, use a new output directory:

```sh
python3 checks/authority-proposal/replay_proposal.py --repo repo --proposal checks/authority-proposal/generated --out checks/authority-proposal/replay-new
```

## Maintainer application after selecting this optional proposal

From the repository root of a fresh full copy:

```sh
python3 generators/48bda9528e71/workspace/propose_authority_sync.py check --repo . --state original
git apply --check ../checks/authority-proposal/generated/authority-sync.patch
git apply ../checks/authority-proposal/generated/authority-sync.patch
python3 generators/48bda9528e71/workspace/propose_authority_sync.py check --repo . --state patched
```

The patch uses repository-root `shared/` paths. It is not directly formatted for
the flattened runtime checker's `--patch` option. Run the normal supported
`authority_sync` stage against the full patched copy to check Racket execution.
The proposal remains unselected in the active review tree.

## Completed full relocated verification

The parent reviewer applied this exact proposal only to a fresh original
packet after its task delta had passed 30/30 portable regression tests.
Both original/patched whole-file guards passed. The complete supported battery
then passed **12/12 stages**, including Racket execution parity, with unchanged
generator SHA `fa8f82d356825247d12033364a9c6de885922c2d3829e2de75399d211516cae6`.
See `../return-validation/authority-patch-application.json` and
`../return-validation/fresh-with-authority-battery/`.

That fresh Git root was the outer packet directory. Consequently, running
from its `WORK/repo/` required `--directory=WORK/repo` on both `git apply`
commands. A repository that is itself the Git root needs no such prefix.
The hash guards verify actual application in either layout; do not interpret
a zero Git exit status alone as proof that files were changed.
