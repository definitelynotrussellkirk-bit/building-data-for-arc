# Run the focused repair checks

From the outer extracted review packet:

```sh
python3 review.py run python3 -m pytest -q generators/2fb8d019f6ca/tests
python3 review.py run python3 -m arcpuzzles lesson-census 2fb8d019f6ca --enumerate-schedule-period --schedule-seed 0 --rotation-policy require --out ../checks/new-schedule.json
python3 review.py run python3 -m arcpuzzles lesson-census 2fb8d019f6ca --per-band 100 --rotate-query --out ../checks/new-census.json
```

Choose new output paths. For the isolated task-test stage, use one Python 3.12+
interpreter with pytest, NumPy and Pillow installed outside its user-site-only
path. WORK/RETURN-GUIDE.md documents the supported wrapper and stage.

The return includes `checks/tooling/probe_storage.py` for optional read-only
byte/inode diagnostics and `checks/tooling/bootstrap_test_env.py` for offline
copying of already installed dependencies into a new isolated environment.
Neither tool is an additional review gate. Labels must still come from Racket;
the independent Python stamping helper in the tests is a differential oracle.
