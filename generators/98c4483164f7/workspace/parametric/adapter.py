"""Thin proposed promotion adapter; this file does not grant acceptance."""
import core


def program(settings):
    return core.materialize_program(settings)


def generate(seed, settings, demos, queries):
    from episodes import generate_episode
    return generate_episode(seed, settings, demos, queries)
