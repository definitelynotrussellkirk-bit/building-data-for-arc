"""Promotion adapter for the proposed completion-transform prototype."""
import prototype


def _transform(settings):
    if type(settings) is not dict or set(settings) != {"completion_transform"}:
        raise ValueError("settings must contain exactly completion_transform")
    value = settings["completion_transform"]
    prototype._validate_transform(value)
    return value


def program(settings):
    return prototype.program_for(_transform(settings))


def generate(seed, settings, demos, queries):
    transform = _transform(settings)
    episode = prototype.make_episode(
        seed,
        completion_transform=transform,
        train_count=demos,
        query_count=queries,
    )
    return dict(episode, program_solution=episode["program"])
