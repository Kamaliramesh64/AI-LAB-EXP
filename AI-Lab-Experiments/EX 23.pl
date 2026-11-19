% parent(Parent, Child).
parent(ramesh, arun).
parent(ramesh, priya).
parent(lakshmi, arun).
parent(lakshmi, priya).
parent(arun, kiran).
parent(meena, kiran).
parent(priya, divya).
 
father(X, Y) :- parent(X, Y), male(X).
mother(X, Y) :- parent(X, Y), female(X).
 
male(ramesh).
male(arun).
female(lakshmi).
female(priya).
female(meena).
female(divya).
 
grandparent(X, Z) :-
    parent(X, Y),
    parent(Y, Z).
 
sibling(X, Y) :-
    parent(P, X),
    parent(P, Y),
    X \= Y.
 
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :-
    parent(X, Z),
    ancestor(Z, Y).
 
% Queries:
% ?- grandparent(ramesh, Who).
% ?- sibling(arun, Who).
% ?- ancestor(ramesh, kiran).