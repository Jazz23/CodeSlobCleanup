from a import helper, UsefulClass
import b

def main():
    # The helper from a.py is used here
    val = helper()
    
    # The UsefulClass from a.py is used here
    obj = UsefulClass()
    
    # used_in_main from b.py is used here (via module attribute)
    val2 = b.used_in_main()
    
if __name__ == "__main__":
    main()
