"""Production promotion adapter for the reviewed stack-side prototype."""
import prototype


def program(settings):
    return prototype.rule_text(settings['stack_side'])


def generate(seed, settings, demos, queries):
    return prototype.generate_episode(seed, stack_side=settings['stack_side'],
                                      demos=demos, queries=queries)
