bird(sparrow).
bird(parrot).
bird(eagle).
bird(penguin).
bird(ostrich).
 
cannot_fly(penguin).
cannot_fly(ostrich).
 
can_fly(Bird) :-
    bird(Bird),
    \+ cannot_fly(Bird).
 
% Queries:
% ?- can_fly(sparrow).
% ?- can_fly(penguin).
% ?- bird(B).