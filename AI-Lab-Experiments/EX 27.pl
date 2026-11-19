% edge(Node1, Node2).
edge(a, b).
edge(a, c).
edge(b, d).
edge(b, e).
edge(c, f).
edge(e, g).
edge(f, g).
 
% heuristic(Node, EstimatedDistanceToGoal).
heuristic(a, 6).
heuristic(b, 4).
heuristic(c, 2).
heuristic(d, 5).
heuristic(e, 3).
heuristic(f, 1).
heuristic(g, 0).
 
best_first(Start, Goal, Path) :-
    search([[Start]], Goal, ReversePath),
    reverse(ReversePath, Path).
 
search([[Goal|Rest]|_], Goal, [Goal|Rest]).
search([[Current|Rest]|OtherPaths], Goal, Path) :-
    findall([Next,Current|Rest],
        (edge(Current, Next), \+ member(Next, [Current|Rest])),
        NewPaths),
    append(OtherPaths, NewPaths, Combined),
    sort_paths(Combined, Sorted),
    search(Sorted, Goal, Path).
 
sort_paths(Paths, Sorted) :-
    predsort(compare_path, Paths, Sorted).
 
compare_path(Order, [Node|_], [Other|_]) :-
    heuristic(Node, H1),
    heuristic(Other, H2),
    compare(Order, H1, H2).
 
% Query: ?- best_first(a, g, Path).