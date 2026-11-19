% State: state(MonkeyPosition, MonkeyHeight, BoxPosition, HasBanana).
% Initial state: monkey at door, on floor, box at window, no banana.
 
move(state(P, on_floor, P, no),
     state(P, on_box, P, yes)) :-
    banana_at(P).
 
move(state(P1, on_floor, P1, no),
     state(P2, on_floor, P2, no)) :-
    box_at(P1),
    banana_at(P2),
    P1 \= P2.
 
move(state(P1, on_floor, P1, no),
     state(P2, on_floor, P2, no)) :-
    adjacent(P1, P2).
 
banana_at(middle).
box_at(window).
adjacent(door, window).
adjacent(window, middle).
adjacent(middle, door).
 
% A compact reachability rule for the planned solution:
can_get_banana :-
    adjacent(door, window),
    adjacent(window, middle),
    box_at(window),
    banana_at(middle).
 
% Query: ?- can_get_banana.