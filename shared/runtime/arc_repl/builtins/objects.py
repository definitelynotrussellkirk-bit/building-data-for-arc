"""
Object builtins — object detection, properties, relations.
"""


def register(env):
    """Register object builtins into env."""

    # Object accessors
    env.define('obj-color', lambda obj: obj['color'])
    env.define('obj-size', lambda obj: obj['size'])
    env.define('obj-cells', lambda obj: obj['cells'])
    env.define('obj-bbox', lambda obj: obj['bbox'])
    env.define('obj-center', lambda obj: (obj.get('center_r', 0), obj.get('center_c', 0)))
