from dualuse import greet


def test_dualuse_is_linked():
    """The `dualuse` workspace package must be installed as a backend dependency."""
    assert greet("backend") == "Hello, backend!"
