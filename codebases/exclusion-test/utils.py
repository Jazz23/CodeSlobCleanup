def global_excluded_func(a, b):
    if a > b:
        if a - b > 50:
            return 1
        elif a - b > 20:
            return 2
        elif a - b > 10:
            return 3
        else:
            return 4
    elif a < b:
        if b - a > 50:
            return -1
        elif b - a > 20:
            return -2
        elif b - a > 10:
            return -3
        else:
            return -4
    else:
        if a == 0:
            if b == 0:
                return 0
            else:
                return -100
        else:
            return 100

def pattern_helper_func(x):
    res = 0
    for i in range(x):
        if i % 2 == 0:
            res += i
        else:
            if i % 3 == 0:
                res -= i
            elif i % 5 == 0:
                res += 1
            else:
                res -= 1
    return res

def specifically_another_one(y):
    data = []
    for i in range(y):
        if i % 2 == 0:
            if i % 4 == 0:
                data.append(i * 2)
            else:
                data.append(i * 3)
        else:
            if i % 3 == 0:
                data.append(i + 5)
            else:
                data.append(i - 1)
    return sum(data)

def normal_func(items):
    result = []
    for item in items:
        if isinstance(item, int):
            if item > 100:
                result.append(item * 10)
            elif item > 50:
                result.append(item * 5)
            elif item > 0:
                result.append(item * 2)
            else:
                result.append(item)
        elif isinstance(item, str):
            if len(item) > 10:
                result.append(item.upper())
            else:
                result.append(item.lower())
    return result

def ubiquitous_slob(n):
    s = 0
    for i in range(n):
        if i % 2 == 0:
            if i % 8 == 0:
                if i % 16 == 0:
                    s += i * i
                else:
                    s += i * 2
            else:
                if i % 4 == 0:
                    s += i * 3
                else:
                    s += i
        else:
            if i % 5 == 0:
                if i % 25 == 0:
                    s -= i * 10
                else:
                    s -= i
            else:
                if i % 3 == 0:
                    s += 100
                else:
                    s += 1
    return s

def targeted_slob(data):
    out = []
    for d in data:
        if isinstance(d, int):
            if d > 1000:
                out.append(d / 100)
            elif d > 500:
                out.append(d / 10)
            elif d > 100:
                out.append(d * 2)
            else:
                out.append(d + 5)
        elif isinstance(d, str):
            if d.startswith("T"):
                if len(d) > 10:
                    out.append(d.upper())
                else:
                    out.append(d)
            else:
                if d.endswith("s"):
                    out.append(d.lower())
                else:
                    out.append(d + "!")
    return out
