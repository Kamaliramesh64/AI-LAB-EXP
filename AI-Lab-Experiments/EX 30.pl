% Facts
parent(john, mary).
parent(mary, alice).
parent(john, peter).
 
% Rules
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :-
    parent(X, Z),
    ancestor(Z, Y).
 
% Queries:
% ?- ancestor(john, alice).
% ?- ancestor(john, Who).