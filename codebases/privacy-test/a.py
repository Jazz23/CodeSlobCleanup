import b

def helper():
    # This helper is imported by main.py, so it shouldn't be private.
    # Notice that b.py also has a function named 'helper', testing our resolution.
    return 1

def unused_helper():
    # Not used anywhere outside this file. Should be private.
    return 2

class UsefulClass:
    # Imported by main.py, shouldn't be private
    def process(self):
        # Unused outside, should be private
        pass

class UnusedClass:
    # Not used outside, should be private
    pass
