from heapq import heappush, heappop

GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)

def heuristic(state):
    return sum(
        abs(i // 3 - (value - 1) // 3) + abs(i % 3 - (value - 1) % 3)
        for i, value in enumerate(state) if value != 0
    )

def neighbors(state):
    zero = state.index(0)
    r, c = divmod(zero, 3)
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            j = nr * 3 + nc
            new_state = list(state)
            new_state[zero], new_state[j] = new_state[j], new_state[zero]
            yield tuple(new_state)

def solve(start):
    queue = []
    heappush(queue, (heuristic(start), 0, start, [start]))
    best = {start: 0}
    while queue:
        _, cost, state, path = heappop(queue)
        if state == GOAL:
            return path
        if cost != best[state]:
            continue
        for nxt in neighbors(state):
            new_cost = cost + 1
            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heappush(queue, (new_cost + heuristic(nxt), new_cost, nxt, path + [nxt]))
    return None

start = (1, 2, 3, 4, 0, 6, 7, 5, 8)
path = solve(start)
if path:
    for step, state in enumerate(path):
        print(f"Step {step}:")
        for i in range(0, 9, 3):
            print(state[i:i+3])
else:
    print("No solution found")
