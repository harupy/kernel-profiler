import os
from collections import namedtuple


def on_github_action():
    """
    Examples
    --------
    >>> import os
    >>>
    >>> os.environ["GITHUB_ACTION"] = "true"
    >>> on_github_action()
    True

    """
    return "GITHUB_ACTION" in os.environ


def get_action_input(name):
    """
    Examples
    --------
    >>> import os
    >>>
    >>> os.environ["INPUT_A"] = "a"
    >>> get_action_input("a")
    'a'

    """
    return os.getenv(f"INPUT_{name.upper()}")


def get_action_inputs(input_types):
    """
    Examples
    --------
    >>> import os
    >>>
    >>> os.environ["INPUT_STR"] = "a"
    >>> os.environ["INPUT_INT"] = "0"
    >>>
    >>> inputs = get_action_inputs({"str": str, "int": int})
    >>> inputs.str
    'a'
    >>> inputs.int
    0

    """
    Args = namedtuple("Args", list(input_types.keys()))
    return Args(*[t(get_action_input(k)) for k, t in input_types.items()])


def set_action_output(key, value):
    os.system(f'echo "::set-output name={key}::{value}"')


def set_action_outputs(outputs):
    for key, value in outputs.items():
        set_action_output(key, value)
