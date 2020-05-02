import contextlib
import os

from kernel_profiler import github_action as ga


@contextlib.contextmanager
def set_env(environ):
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def test_on_github_action():
    with set_env({"GITHUB_ACTION": "true"}):
        assert ga.on_github_action()


def test_get_action_input():
    env = {
        "INPUT_A": "a",
    }

    with set_env(env):
        assert ga.get_action_input("a") == "a"


def test_get_action_inputs():
    env = {
        "INPUT_STR": "x",
        "INPUT_INT": "0",
        "INPUT_FLOAT": "0.1",
    }

    input_types = {
        "str": str,
        "int": int,
        "float": float,
    }

    with set_env(env):
        args = ga.get_action_inputs(input_types)
        assert args.str == "x"
        assert args.int == 0
        assert args.float == 0.1


def test_set_action_output(capsys):
    ga.set_action_output("a", "b")
    captured = capsys.readouterr()
    assert captured.out == "::set-output name=a::b\n"


def test_set_action_outputs(capsys):
    ga.set_action_outputs({"a": "b", "c": "d"})
    captured = capsys.readouterr()
    assert captured.out == "::set-output name=a::b\n::set-output name=c::d\n"
