import kernel_profiler


def test_version_exists():
    assert hasattr(kernel_profiler, "__version__")
