from app import init_db, update_config, increment_process, get_status

def test_workflow():
    # Setup
    init_db("sqlite:///:memory:")
    update_config("debug", True)
    
    # Action
    increment_process()
    increment_process()
    
    # Assertions
    status = get_status()
    assert status["db"] == "Connected to sqlite:///:memory:"
    assert status["config"]["debug"] is True
    assert status["count"] == 2
