"""Finite declared-rival screen for an already labelled FINAL assembled episode.

This is a proposed export guard, not reference label authority or a production
integration. A caller must explicitly select lawful-domain rivals and explain
why each belongs in this export's allowlist.
"""
from collections.abc import Mapping
from copy import deepcopy


def _grid(value, location):
    if not isinstance(value, list) or not value or not isinstance(value[0], list) or not value[0]:
        raise ValueError(f"{location}: expected nonempty list grid")
    width = len(value[0])
    if any(not isinstance(row, list) or len(row) != width for row in value):
        raise ValueError(f"{location}: expected rectangular grid")
    if any(type(color) is not int or not 0 <= color <= 9 for row in value for color in row):
        raise ValueError(f"{location}: expected integer colors 0..9")
    return deepcopy(value)


def screen_episode(episode, rivals, *, rationale, query_rotation=False):
    """Fail closed if a declared rival fits demos but changes a held-out label.

    ``rivals`` is an explicit nonempty mapping of names to pure input->grid
    callables. ``rationale`` must give a nonempty export-domain explanation for
    exactly those names. Current test positions are screened together by
    default. Opt-in ``query_rotation=True`` instead screens every final example
    once as the sole query, with every other labelled example as a demo.

    Results use zero-based flattened indices (train first, then test), with
    ``examples`` mapping each index back to its original split/index. Invalid
    inputs raise ValueError; rival errors, mutation, or observed nondeterminism
    return allowed=False with source indices. Exporters must stop on either.
    A passing result does not verify reference labels or unlisted hypotheses.
    """
    if type(query_rotation) is not bool:
        raise ValueError("query_rotation must be an explicit boolean")
    if not isinstance(rivals, Mapping) or not rivals:
        raise ValueError("explicit nonempty rival allowlist required")
    if any(not isinstance(name, str) or not name.strip() or not callable(fn) for name, fn in rivals.items()):
        raise ValueError("rivals must map nonempty names to callables")
    if not isinstance(rationale, Mapping) or set(rationale) != set(rivals):
        raise ValueError("supply an explicit rationale for exactly every declared rival")
    if any(not isinstance(reason, str) or not reason.strip() for reason in rationale.values()):
        raise ValueError("each rival requires a nonempty export-domain rationale")
    if not isinstance(episode, Mapping):
        raise ValueError("episode must map train/test to labelled examples")
    pairs, origins = [], []
    for split in ("train", "test"):
        if not isinstance(episode.get(split), list) or not episode[split]:
            raise ValueError(f"{split}: at least one labelled example required")
        for index, pair in enumerate(episode[split]):
            if not isinstance(pair, Mapping) or "input" not in pair or "output" not in pair:
                raise ValueError(f"{split}[{index}]: input and authoritative output required")
            pairs.append({key: _grid(pair[key], f"{split}[{index}].{key}") for key in ("input", "output")})
            origins.append({"split": split, "index": index})
    count = len(pairs)
    train_count = len(episode["train"])
    partitions = [([i for i in range(count) if i != query], [query]) for query in range(count)] if query_rotation else [
        (list(range(train_count)), list(range(train_count, count)))]
    predictions, errors = {}, {}
    for name, fn in rivals.items():
        predictions[name], errors[name] = [], []
        for index, pair in enumerate(pairs):
            try:
                outputs = []
                for _ in range(2):
                    inp = deepcopy(pair["input"])
                    output = fn(inp)
                    if inp != pair["input"]:
                        raise ValueError("rival mutated its input")
                    outputs.append(_grid(output, "rival output"))
                if outputs[0] != outputs[1]:
                    raise ValueError("rival is nondeterministic on repeated input")
                predictions[name].append(outputs[0])
            except Exception as exc:
                predictions[name].append(None)
                errors[name].append({"rival": name, "example_index": index,
                                     "source": origins[index], "error": f"{type(exc).__name__}: {exc}"})
    checks = []
    for demo_indices, query_indices in partitions:
        verdicts, violations, case_errors = {}, [], []
        for name in rivals:
            case_errors.extend(errors[name])
            demo_matches = [predictions[name][i] == pairs[i]["output"] for i in demo_indices]
            fits = not errors[name] and all(demo_matches)
            disagreement = [i for i in query_indices if predictions[name][i] != pairs[i]["output"]] if fits else []
            verdicts[name] = {"fits_all_demos": fits,
                              "matching_demo_indices": [i for i, matched in zip(demo_indices, demo_matches) if matched],
                              "disagreeing_query_indices": disagreement}
            if disagreement:
                violations.append({"rival": name, "demo_indices": demo_indices,
                                   "query_indices": disagreement,
                                   "query_sources": [origins[i] for i in disagreement]})
        checks.append({"demo_indices": demo_indices, "query_indices": query_indices,
                       "rivals": verdicts, "violations": violations, "errors": case_errors,
                       "allowed": not violations and not case_errors})
    return {"schema": "final-episode-finite-rival-screen-v1",
            "allowed": all(check["allowed"] for check in checks),
            "query_rotation": query_rotation,
            "examples": origins, "rival_allowlist_rationale": dict(rationale),
            "checks": checks, "reference_labels_verified": False,
            "scope": "Only the caller's declared rivals on the final labelled examples; no universal identifiability or model-gain claim."}
