# Minimax on a small game tree
tree = {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"]}
values = {"D": 3, "E": 5, "F": 2, "G": 9}

def minimax(node, maximizing):
    if node not in tree:
        return values[node]
    scores = [minimax(child, not maximizing) for child in tree[node]]
    return max(scores) if maximizing else min(scores)

print("Best value for MAX:", minimax("A", True))
