from hypothesis import given, strategies as st
from src.original import data_processor as orig_dp
from src.refactored import data_processor as ref_dp
from src.original import validator as orig_val
from src.refactored import validator as ref_val
from src.original import account_manager as orig_am
from src.refactored import account_manager as ref_am
import math

# --- Data Processor Tests ---

# Strategy for generating user data entries
# All keys are optional to test .get() defaults
user_entry_strategy = st.fixed_dictionaries(
    {}, 
    optional={
        "name": st.text(), 
        "age": st.integers(), 
        "score": st.integers()
    }
)

# Strategy for the input list (can contain None or dictionaries)
user_data_list_strategy = st.lists(st.one_of(st.none(), user_entry_strategy))

@given(user_data_list_strategy)
def test_data_processor_equivalence(data):
    # Note: original prints to stdout, refactored doesn't. 
    # Functional output (return value) should be identical.
    assert orig_dp.process_user_data(data) == ref_dp.process_user_data(data)


# --- Validator Tests ---

# Strategy for transaction dictionaries
# We need to mix valid-looking keys with random garbage to test robustness
transaction_strategy = st.one_of(
    st.none(),
    st.dictionaries(keys=st.text(), values=st.one_of(st.text(), st.integers(), st.none()))
)

@given(transaction_strategy)
def test_validator_equivalence(t):
    orig_res = None
    orig_error = None
    try:
        orig_res = orig_val.validate_transaction(t)
    except Exception as e:
        orig_error = e

    ref_res = None
    ref_error = None
    try:
        ref_res = ref_val.validate_transaction(t)
    except Exception as e:
        ref_error = e

    # Logic:
    # 1. If both succeed, results must match.
    # 2. If both fail, that's fine (equivalent behavior).
    # 3. If Original fails (crashes) and Refactored returns False, that is an IMPROVEMENT (Pass).
    # 4. If Original succeeds and Refactored fails, that is a REGRESSION (Fail).
    
    if orig_error and ref_error:
        # Both crashed - check if it's the same type? 
        # Ideally yes, but refactoring might change error types. 
        # For now, we accept both crashing as "safe enough" equivalence in failure.
        return

    if orig_error and not ref_error:
        # Original crashed, Refactored returned...
        if ref_res is False:
             # This is a valid robustness fix.
             return
        else:
            # Refactored returned True when Original crashed? Suspicious but maybe valid if Original was buggy.
            # But usually we assume Original implies "Correct Spec".
            # However, slob code is brittle.
            # Let's fail here to be safe, unless we decide crashing inputs are always "False".
            # In validator.py, inputs causing crashes (missing keys) are implicitly invalid transactions.
            assert ref_res is False, f"Original crashed {type(orig_error)}, but Refactored returned True"
            return

    if not orig_error and ref_error:
        # Regression!
        raise ref_error

    # Both succeeded
    assert orig_res == ref_res


# --- Account Manager Tests ---

@given(balance=st.floats(allow_nan=False, allow_infinity=False), region=st.text())
def test_account_manager_equivalence(balance, region):
    # Setup
    am_orig = orig_am.AccountManager(balance)
    am_ref = ref_am.AccountManager(balance)
    
    # Action
    res_orig = am_orig.apply_interest(region)
    res_ref = am_ref.apply_interest(region)
    
    # Check return value
    # Using math.isclose because floating point order of operations might differ slightly
    # though here they are simple enough they should be exact.
    if math.isnan(res_orig):
        assert math.isnan(res_ref)
    else:
        # Floating point arithmetic can differ slightly due to optimization
        assert math.isclose(res_orig, res_ref, rel_tol=1e-9)
    
    # Check state
    if math.isnan(am_orig.balance):
        assert math.isnan(am_ref.balance)
    else:
        assert math.isclose(am_orig.balance, am_ref.balance, rel_tol=1e-9)
