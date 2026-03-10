def helper():
    # Not imported anywhere. Should be private.
    # a.py also has a 'helper' function that IS used.
    return 3

def used_in_main():
    # Imported via module import in main.py. Shouldn't be private.
    return 4
