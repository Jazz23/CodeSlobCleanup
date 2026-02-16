def global_excluded_func(x):
    res = 0
    if x > 0:
        if x < 10:
            res = 1
        elif x < 20:
            res = 2
        elif x < 30:
            res = 3
        else:
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
    elif x < -10:
        if x > -20:
            res = -1
        else:
            res = -2
    else:
        res = 0
    return res

def main_func(y):
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
    
    total = 0
    for val in data:
        if val > 100:
            if val < 200:
                total += val
            else:
                total += val / 2
        elif val > 50:
            total += val * 1.5
        else:
            if val < 0:
                total -= 10
            else:
                total += val
    return total

def ubiquitous_slob(a):
    res = 0
    for i in range(a):
        if i % 2 == 0:
            if i % 4 == 0:
                if i % 8 == 0:
                    res += i * i
                else:
                    res += i * 2
            else:
                if i % 6 == 0:
                    res += i * 3
                else:
                    res += i
        else:
            if i % 3 == 0:
                if i % 9 == 0:
                    res -= i * 2
                else:
                    res -= i
            else:
                if i % 5 == 0:
                    res += 10
                else:
                    res += 1
    return res

def targeted_slob(b):
    data = []
    for i in range(b):
        if i % 5 == 0:
            if i % 10 == 0:
                if i % 20 == 0:
                    data.append(i * 10)
                else:
                    data.append(i * 5)
            else:
                if i % 15 == 0:
                    data.append(i * 3)
                else:
                    data.append(i * 2)
        else:
            if i % 2 == 0:
                data.append(i + 1)
            else:
                data.append(i - 1)
    return sum(data)
