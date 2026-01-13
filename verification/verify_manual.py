import sys
import os

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.original import data_processor as orig_dp
from src.refactored import data_processor as ref_dp
from src.original import validator as orig_val
from src.refactored import validator as ref_val
from src.original import account_manager as orig_am
from src.refactored import account_manager as ref_am

def test_data_processor():
    print("\n--- Testing Data Processor ---")
    data = [
        {"name": " Alice ", "age": 25, "score": 95},
        {"name": "bob", "age": -5, "score": 85},
        None,
        {"name": "Charlie", "score": 50} # Missing age
    ]
    
    print("Running Original (expect print output):")
    res_orig = orig_dp.process_user_data(data)
    
    print("Running Refactored (expect silent):")
    res_ref = ref_dp.process_user_data(data)
    
    if res_orig == res_ref:
        print("PASS: Results match.")
    else:
        print("FAIL: Results differ!")
        print(f"Orig: {res_orig}")
        print(f"Ref:  {res_ref}")

def test_validator():
    print("\n--- Testing Validator ---")
    tx_valid = {"id": "123456789", "amount": 100, "status": "pending"}
    tx_invalid_amt = {"id": "123456789", "amount": 0, "status": "pending"}
    tx_invalid_id = {"id": "123", "amount": 100, "status": "pending"}
    tx_invalid_status = {"id": "123456789", "amount": 100, "status": "completed"}
    
    cases = [tx_valid, tx_invalid_amt, tx_invalid_id, tx_invalid_status, None, {}]
    
    for i, case in enumerate(cases):
        res_orig = orig_val.validate_transaction(case)
        res_ref = ref_val.validate_transaction(case)
        if res_orig == res_ref:
             # print(f"Case {i} PASS: {res_orig}")
             pass
        else:
            print(f"Case {i} FAIL! Input: {case}")
            print(f"Orig: {res_orig}, Ref: {res_ref}")
            return
            
    print("PASS: All validator cases match.")

def test_account_manager():
    print("\n--- Testing Account Manager ---")
    # Original
    acct_orig = orig_am.AccountManager(1000)
    res_orig = acct_orig.apply_interest("US")
    res_orig_2 = acct_orig.apply_interest("EU")
    
    # Refactored
    acct_ref = ref_am.AccountManager(1000)
    res_ref = acct_ref.apply_interest("US")
    res_ref_2 = acct_ref.apply_interest("EU")
    
    if res_orig == res_ref and res_orig_2 == res_ref_2:
        print(f"PASS: Balances match ({res_orig}, {res_orig_2}).")
    else:
        print("FAIL: Account Manager logic differs.")
        print(f"Orig: {res_orig}, {res_orig_2}")
        print(f"Ref:  {res_ref}, {res_ref_2}")

if __name__ == "__main__":
    test_data_processor()
    test_validator()
    test_account_manager()
