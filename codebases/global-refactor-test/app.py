# Global state (Slob pattern)
config = {"debug": False, "retries": 3}
database_connection = None
process_count = 0

def init_db(connection_string):
    global database_connection
    database_connection = f"Connected to {connection_string}"
    return database_connection

def update_config(key, value):
    global config
    config[key] = value

def increment_process():
    global process_count
    process_count += 1
    return process_count

def get_status():
    return {
        "db": database_connection,
        "config": config,
        "count": process_count
    }
