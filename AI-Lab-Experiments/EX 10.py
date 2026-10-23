import heapq

def a_star(graph, heuristic, start, goal):
    queue = [(heuristic[start], 0, start, [start])]
    best_cost = {start: 0}

    while queue:
        _, cost, node, path = heapq.heappop(queue)
        if node == goal:
            return path, cost
        if cost != best_cost[node]:
            continue
        for neighbor, edge_cost in graph[node]:
            new_cost = cost + edge_cost
            if new_cost < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = new_cost
                priority = new_cost + heuristic[neighbor]
                heapq.heappush(queue, (priority, new_cost, neighbor, path + [neighbor]))
    return None, float("inf")

graph = {
    "A": [("B", 1), ("C", 4)],
    "B": [("C", 2), ("D", 5)],
    "C": [("D", 1)],
    "D": []
}
heuristic = {"A": 4, "B": 3, "C": 1, "D": 0}
path, cost = a_star(graph, heuristic, "A", "D")
print("Best path:", " -> ".join(path) if path else "No path found")
print("Path cost:", cost)

