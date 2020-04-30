import os
from collections import namedtuple


def on_github_action():
    return "GITHUB_ACTION" in os.environ


def get_action_input(name):
    return os.getenv(f"INPUT_{name.upper()}")


def get_action_inputs(input_types):
    Args = namedtuple("Args", list(input_types.keys()))
    return Args(*[t(get_action_input(k)) for k, t in input_types.items()])


def set_action_output(key, value):
    os.system(f'echo "::set-output name={key}::{value}"')


def set_action_outputs(outputs):
    for key, value in outputs.items():
        set_action_output(key, value)
