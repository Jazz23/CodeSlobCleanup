# Typical Code Slob File: math_utils.py
# This file contains many global variables and irrelevant classes.

global_state = 0
unnecessary_list = []
# codeslob: ignore begin
foo = 0
class MathOperations:
    def add(self, a, b):
        return a + b
# codeslob: ignore end
    
class DatabaseConnector:
    """This class is irrelevant to math_utils.py"""
    def connect(self):
        print("Connecting...")

class UserProfile:
    """This class is also irrelevant to math_utils.py"""
    def get_name(self):
        return "User"

class Logger:
    """Misplaced logger class"""
    def log(self, msg):
        print(msg)

def very_complex_function(a, b, c, d, e):
    # This is to trigger radon complexity as well
    if a > b:
        if b > c:
            if c > d:
                if d > e:
                    return a
                else:
                    return b
            else:
                return c
        else:
            return d
    else:
        return e
