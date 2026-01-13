import sys
import os
import random
import string
import contextlib

# Add src to path to import modules
sys.path.append(os.path.join(os.getcwd(), "src"))

from original import account_manager as orig_am
from original import data_processor as orig_dp
from original import validator as orig_val

from refactored import account_manager as ref_am
from refactored import data_processor as ref_dp
from refactored import validator as ref_val

from benchmark_runner import BenchmarkRunner

@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters, k=length))

def gen_user_data(n=1000):
    data = []
    for _ in range(n):
        if random.random() < 0.1:
            data.append(None)
        else:
            item = {
                "name": generate_random_string(),
                "age": random.randint(-5, 100),
                "score": random.randint(0, 100)
            }
            data.append(item)
    return [data] 

def gen_transactions(n=1000):
    transactions = []
    for _ in range(n):
        t = {}
        if random.random() > 0.1: 
            t["id"] = generate_random_string(random.randint(5, 15))
            # Original code expects amount if id is present
            t["amount"] = random.randint(-10, 1000)
            # Original code expects status if amount > 0
            t["status"] = random.choice(["pending", "completed", "failed"])
        
        transactions.append(t)
    return transactions

def main():
    runner = BenchmarkRunner()

    print("\n--- Benchmarking Validator ---")
    # No print in function, so no need to suppress
    runner.compare(
        name="Validator",
        original_func=orig_val.validate_transaction,
        refactored_func=ref_val.validate_transaction,
        input_generator=lambda: gen_transactions(10000),
        num_runs=50
    )

    print("\n--- Benchmarking Data Processor ---")
    # This one prints, so we suppress, but capture results to print later
    results = None
    with suppress_stdout():
        results = runner.compare(
            name="Data Processor",
            original_func=orig_dp.process_user_data,
            refactored_func=ref_dp.process_user_data,
            input_generator=lambda: [gen_user_data(1000)[0] for _ in range(10)], 
            num_runs=20
        )
    
    if results:
        print(f"  Original:   {results['original_avg']:.6f}s")
        print(f"  Refactored: {results['refactored_avg']:.6f}s")
        print(f"  Speedup:    {results['speedup']:.2f}x")


    print("\n--- Benchmarking Account Manager ---")
    inputs_data = ["US", "EU", "US", "Asia"] * 250 
    
    orig_mgr = orig_am.AccountManager(1000)
    ref_mgr = ref_am.AccountManager(1000)
    
    def run_orig(region):
        orig_mgr.apply_interest(region)
        
    def run_ref(region):
        ref_mgr.apply_interest(region)

    runner.compare(
        name="Account Manager (Apply Interest)",
        original_func=run_orig,
        refactored_func=run_ref,
        input_generator=lambda: inputs_data,
        num_runs=100
    )

if __name__ == "__main__":
    main()
