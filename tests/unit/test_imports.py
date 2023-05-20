from hya.imports import is_torch_available


def test_is_torch_available() -> None:
    assert isinstance(is_torch_available(), bool)
