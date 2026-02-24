import main
import utils
import ignored_file

def test_everything():
    print("Testing main_func...")
    main.main_func(10)
    
    print("Testing utils.targeted_slob...")
    utils.targeted_slob([1, 2, 3, "Test"])

    print("Testing main.ignored_function_slob...")
    assert main.ignored_function_slob(200, 50) == 10000
    assert main.ignored_function_slob(50, 200) == -150

    print("Testing main.line_ignored_slob...")
    assert main.line_ignored_slob(5) == 5
    assert main.line_ignored_slob(20) == 200
    assert main.line_ignored_slob(200) == 20000

    print("Testing utils.block_ignored_slob...")
    assert utils.block_ignored_slob([1, 2, 3, 4]) == 2 # -1 + 2 - 3 + 4

    print("Testing ignored_file.very_complex_slob_function...")
    assert ignored_file.very_complex_slob_function(4) == 1
    assert ignored_file.very_complex_slob_function(-10) == -2

    print("All tests passed!")

if __name__ == "__main__":
    test_everything()
