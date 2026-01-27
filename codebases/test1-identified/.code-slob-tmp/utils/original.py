def calculate_fibonacci(n):
    # This is a very inefficient way to calculate fibonacci
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def format_names(names):
    # poor variable naming and string concatenation
    l = []
    for x in names:
        if x != "":
            s = x.strip().lower()
            temp = ""
            for i in range(len(s)):
                if i == 0:
                    temp += s[i].upper()
                else:
                    temp += s[i]
            l.append(temp)
    return l

def get_max_value(data):
    # reinventing the wheel
    if len(data) == 0:
        return None
    m = data[0]
    for i in range(len(data)):
        if data[i] > m:
            m = data[i]
    return m
