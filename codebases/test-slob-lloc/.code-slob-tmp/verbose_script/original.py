def monolithic_processor(large_data_blob):
    """
    Deliberately long function with high LLOC.
    """
    processed_count = 0
    total_value = 0
    errors = []
    
    # Sequential processing without modularization
    line_1 = large_data_blob.get("header", "")
    line_2 = large_data_blob.get("body", "")
    line_3 = large_data_blob.get("footer", "")
    
    val_a = 10.5
    val_b = 20.0
    val_c = val_a * val_b
    val_d = val_c / 2
    val_e = val_d + 100
    
    status_0 = "INIT"
    status_1 = "STARTED"
    status_2 = "PROCESSING_A"
    status_3 = "PROCESSING_B"
    status_4 = "PROCESSING_C"
    status_5 = "FINALIZING"
    status_6 = "DONE"
    
    reg_1 = "alpha"
    reg_2 = "beta"
    reg_3 = "gamma"
    reg_4 = "delta"
    reg_5 = "epsilon"
    reg_6 = "zeta"
    reg_7 = "eta"
    reg_8 = "theta"
    reg_9 = "iota"
    reg_10 = "kappa"
    
    print(f"Starting with {reg_1} and {status_0}")
    
    if line_1:
        processed_count += 1
        total_value += val_a
    
    if line_2:
        processed_count += 1
        total_value += val_b
        
    if line_3:
        processed_count += 1
        total_value += val_c
        
    # More sequential lines to increase LLOC
    x1 = 1
    x2 = 2
    x3 = 3
    x4 = 4
    x5 = 5
    x6 = 6
    x7 = 7
    x8 = 8
    x9 = 9
    x10 = 10
    x11 = 11
    x12 = 12
    x13 = 13
    x14 = 14
    x15 = 15
    x16 = 16
    x17 = 17
    x18 = 18
    x19 = 19
    x20 = 20
    x21 = 21
    x22 = 22
    x23 = 23
    x24 = 24
    x25 = 25
    x26 = 26
    x27 = 27
    x28 = 28
    x29 = 29
    x30 = 30
    x31 = 31
    x32 = 32
    x33 = 33
    x34 = 34
    x35 = 35
    x36 = 36
    x37 = 37
    x38 = 38
    x39 = 39
    x40 = 40
    
    final_score = (processed_count * total_value) + (x40 - x1)
    
    return {
        "status": status_6,
        "score": final_score,
        "count": processed_count,
        "errors": errors
    }
