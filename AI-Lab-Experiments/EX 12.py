board = [" "] * 9

def show_board():
    print(f"{board[0]} | {board[1]} | {board[2]}")
    print("--+---+--")
    print(f"{board[3]} | {board[4]} | {board[5]}")
    print("--+---+--")
    print(f"{board[6]} | {board[7]} | {board[8]}")

def winner():
    lines = [(0,1,2), (3,4,5), (6,7,8),
             (0,3,6), (1,4,7), (2,5,8),
             (0,4,8), (2,4,6)]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] != " ":
            return board[a]
    return None

player = "X"
while True:
    show_board()
    try:
        move = int(input(f"Player {player}, choose position (1-9): ")) - 1
    except ValueError:
        print("Enter a number from 1 to 9.")
        continue
    if move not in range(9) or board[move] != " ":
        print("Invalid or occupied position. Try again.")
        continue
    board[move] = player
    if winner():
        show_board()
        print(f"Player {player} wins!")
        break
    if " " not in board:
        show_board()
        print("It's a draw!")
        break
    player = "O" if player == "X" else "X"
