N = 8
board = [-1] * N  # board[row] = column

def safe(row, col):
    for prev_row in range(row):
        prev_col = board[prev_row]
        if prev_col == col or abs(prev_col - col) == abs(prev_row - row):
            return False
    return True

def solve(row=0):
    if row == N:
        return True
    for col in range(N):
        if safe(row, col):
            board[row] = col
            if solve(row + 1):
                return True
            board[row] = -1
    return False

if solve():
    for row in range(N):
        print(" ".join("Q" if board[row] == col else "." for col in range(N)))
else:
    print("No solution found")
