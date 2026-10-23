# Map coloring using backtracking (CSP)
variables = ["A", "B", "C", "D"]
domains = {v: ["Red", "Green", "Blue"] for v in variables}
neighbors = {"A": ["B", "C"], "B": ["A", "C", "D"],
             "C": ["A", "B", "D"], "D": ["B", "C"]}
assignment = {}

def consistent(region, color):
    return all(assignment.get(n) != color for n in neighbors[region])

def backtrack():
    if len(assignment) == len(variables):
        return True
    region = next(v for v in variables if v not in assignment)
    for color in domains[region]:
        if consistent(region, color):
            assignment[region] = color
            if backtrack():
                return True
            del assignment[region]
    return False

if backtrack():
    for region in variables:
        print(f"Region {region}: {assignment[region]}")
else:
    print("No solution found")

