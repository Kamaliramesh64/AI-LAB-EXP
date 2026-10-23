from collections import deque

def water_jug(cap_a, cap_b, target):
    start = (0, 0)
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        (a, b), path = queue.popleft()
        if a == target or b == target:
            return path

        pour_ab = min(a, cap_b - b)
        pour_ba = min(b, cap_a - a)
        next_states = [
            (cap_a, b), (a, cap_b), (0, b), (a, 0),
            (a - pour_ab, b + pour_ab),
            (a + pour_ba, b - pour_ba)
        ]
        for state in next_states:
            if state not in visited:
                visited.add(state)
                queue.append((state, path + [state]))
    return None

path = water_jug(4, 3, 2)
if path:
    for step, state in enumerate(path):
        print(f"Step {step}: Jug A = {state[0]} L, Jug B = {state[1]} L")
else:
    print("Target cannot be measured")
