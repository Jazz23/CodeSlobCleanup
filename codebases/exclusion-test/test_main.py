import main
import utils

def test_everything():
    print("Testing main_func...")
    main.main_func(10)
    
    print("Testing utils.targeted_slob...")
    utils.targeted_slob([1, 2, 3, "Test"])

if __name__ == "__main__":
    test_everything()
