% Initial facts
fact(rain).
 
% Rules represented as rule(Condition, Conclusion).
rule(rain, wet_ground).
rule(wet_ground, slippery_road).
rule(slippery_road, drive_carefully).
 
% Add a conclusion if its condition is already known.
derive :-
    rule(Condition, Conclusion),
    fact(Condition),
    \+ fact(Conclusion),
    assertz(fact(Conclusion)),
    fail.
derive.
 
% Query:
% ?- derive.
% ?- fact(X).