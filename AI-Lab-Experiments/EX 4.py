from itertools import permutations

# Find a solution to SEND + MORE = MONEY
letters = "SENDMORY"
for digits in permutations(range(10), len(letters)):
    values = dict(zip(letters, digits))
    if values["S"] == 0 or values["M"] == 0:
        continue

    def number(word):
        result = 0
        for ch in word:
            result = result * 10 + values[ch]
        return result

    if number("SEND") + number("MORE") == number("MONEY"):
        print(f"SEND  = {number('SEND')}")
        print(f"MORE  = {number('MORE')}")
        print(f"MONEY = {number('MONEY')}")
