tree = {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"]}
values = {"D": 3, "E": 5, "F": 2, "G": 9}

def alpha_beta(node, alpha, beta, maximizing):
    if node not in tree:
        return values[node]
    if maximizing:
        value = float("-inf")
        for child in tree[node]:
            value = max(value, alpha_beta(child, alpha, beta, False))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    value = float("inf")
    for child in tree[node]:
        value = min(value, alpha_beta(child, alpha, beta, True))
        beta = min(beta, value)
        if alpha >= beta:
            break
    return value

result = alpha_beta("A", float("-inf"), float("inf"), True)
print("Best value for MAX:", result)
