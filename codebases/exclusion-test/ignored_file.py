# cs-cleanup: ignore-file
# This file is completely ignored.

def very_complex_slob_function(x):
    # This would normally be caught as slob
    res = 0
    if x > 0:
        if x < 100:
            if x % 2 == 0:
                if x % 4 == 0:
                    res = 1
                else:
                    res = 2
            else:
                if x % 3 == 0:
                    res = 3
                else:
                    res = 4
        else:
            if x % 10 == 0:
                res = 5
            else:
                res = 6
    else:
        if x < -100:
            res = -1
        else:
            res = -2
    return res

def untested_but_file_ignored_func():
    # This function is not called but should NOT be removed because the file is ignored.
    return 100
