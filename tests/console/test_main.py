import pytest
from unittest.mock import patch
from src.console.main import main


def test_main_exit() -> None:
    # Option 7 is now the clean Exit system endpoint in the expanded menu structure
    with patch("builtins.input", side_effect=["7"]):
        with pytest.raises(SystemExit):
            main()
