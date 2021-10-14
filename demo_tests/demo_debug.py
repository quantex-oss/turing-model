def sum_demo(x, y):
    for _ in range(3):
        x += 1
        y += 1
        r = x + y
    return r


if __name__ == '__main__':
    r = sum_demo(1, 1)
    print(r)
