# Fresh-handoff replay attempt 1 (superseded)

- Fresh packet: `/mnt/data/arcpuzzles_review_fresh_060120`
- Isolated Git root: fresh packet root (confirmed by `git rev-parse --show-toplevel`).
- From `WORK/`, plain `git apply --check /mnt/data/prelim-source.patch` and
  `git apply /mnt/data/prelim-source.patch` both returned 0.
- Result: every `repo/...` patch path was silently skipped because it resolved
  outside the current Git prefix; the selected generator stayed at baseline SHA
  `556a0c58d8412a1474557dd3463d26f225c3068c34626618c4a7977b13486bf1`.
- The follow-up pytest command exited 4 because the new selected-task test file
  had not been created.
- Resolution: repeat from a new extraction with `git apply --directory=WORK`; see
  `replay.log` and `report.json`.
