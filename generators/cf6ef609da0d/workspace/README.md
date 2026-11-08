# Workspace

`profile_generate.py` is a source-bound authoring probe for distinguishing slow
or failing component placement from an interrupted outer test harness. From the
repository root:

```sh
python3 generators/cf6ef609da0d/workspace/profile_generate.py \
  --seeds 5 --output ../checks/profile-generation.json
```

The JSON records the generator hash, requested bands/seeds, elapsed time,
observable axes, validator results, and exact failures. It is diagnostic only;
the Racket battery remains label authority.
