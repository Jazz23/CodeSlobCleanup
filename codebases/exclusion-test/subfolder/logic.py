def some_complex_func(data):
    output = {}
    for key, value in data.items():
        if len(key) > 10:
            if isinstance(value, int):
                if value > 100:
                    output[key] = value * 2
                elif value > 50:
                    output[key] = value + 50
                else:
                    output[key] = value + 100
            elif isinstance(value, str):
                if value.startswith("A"):
                    output[key] = value.upper()
                else:
                    output[key] = value.lower()
            else:
                output[key] = str(value)
        elif len(key) > 5:
            if isinstance(value, list):
                if len(value) > 3:
                    output[key] = sum(value)
                else:
                    output[key] = len(value)
            else:
                output[key] = value
        else:
            output[key] = "small_key"
    return output
