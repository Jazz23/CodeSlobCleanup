from src.app import format_user_list, calculate_stats, _LOG
import pytest

def test_format_user_list_functionality():
    users = [{"name": "alice"}, {"name": "bob"}]
    result = format_user_list(users)
    assert result == "ALICE, BOB"

def test_format_user_list_brittle_side_effect():
    """
    This test is brittle because it checks the exact content of a global log 
    which is an implementation detail that might be removed during refactoring.
    """
    # Clear the global log first
    import src.app
    src.app._LOG = []
    
    users = [{"name": "charlie"}]
    format_user_list(users)
    
    # If the refactorer removes the global log or changes the message, this fails.
    assert src.app._LOG == ["Processing user: charlie"]

def test_calculate_stats():
    assert calculate_stats([10, 20, 30]) == 20
    assert calculate_stats([5, None, 15]) == 10
    assert calculate_stats([]) == 0
