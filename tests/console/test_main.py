import pytest
from unittest.mock import patch
from src.console.main import main
from src.core.engine import SportsSystemEngine

def test_main_exit():
    # Test that option 6 triggers system exit cleanly with the new engine
    with patch('builtins.input', side_effect=['6']):
        with pytest.raises(SystemExit):
            main()