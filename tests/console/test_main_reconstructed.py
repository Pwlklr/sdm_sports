import pytest
from unittest.mock import patch

from src.console.main_reconstructed import main


def test_main_exit() -> None:
    with patch("builtins.input", side_effect=["7"]):
        with pytest.raises(SystemExit):
            main()
