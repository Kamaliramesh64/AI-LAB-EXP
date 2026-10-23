from collections import deque

# State: (missionaries_left, cannibals_left, boat_side)
# boat_side: 0 = left bank, 1 = right bank
def valid(m, c):
    return 0 <= m <= 3 and 0 <= c <= 3 and (m == 0 or m >= c)

def solve():
    start, goal = (3, 3, 0), (0, 0, 1)
    moves = [(2, 0), (0, 2), (1, 1), (1, 0), (0, 1)]
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        state, path = queue.popleft()
        if state == goal:
            return path
        m, c, boat = state
        for dm, dc in moves:
            if boat == 0:
                nxt = (m - dm, c - dc, 1)
            else:
                nxt = (m + dm, c + dc, 0)
            if not (0 <= nxt[0] <= 3 and 0 <= nxt[1] <= 3):
                continue
            if not valid(nxt[0], nxt[1]) or not valid(3 - nxt[0], 3 - nxt[1]):
                continue
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, path + [nxt]))
    return None

path = solve()
if path:
    for step, (m, c, boat) in enumerate(path):
        side = "Left" if boat == 0 else "Right"
        print(f"Step {step}: M_left={m}, C_left={c}, Boat={side}")
else:
    print("No solution found")
