from itertools import permutations

cities = ["A", "B", "C", "D"]
distance = {
    ("A","B"): 10, ("A","C"): 15, ("A","D"): 20,
    ("B","C"): 35, ("B","D"): 25,
    ("C","D"): 30
}

def dist(a, b):
    return distance.get((a, b), distance.get((b, a)))

start = "A"
best_route, best_cost = None, float("inf")
for order in permutations([c for c in cities if c != start]):
    route = (start,) + order + (start,)
    cost = sum(dist(route[i], route[i+1]) for i in range(len(route)-1))
    if cost < best_cost:
        best_route, best_cost = route, cost

print("Best route:", " -> ".join(best_route))
print("Minimum distance:", best_cost)

