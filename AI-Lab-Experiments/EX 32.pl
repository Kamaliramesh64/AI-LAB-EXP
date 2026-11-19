% A structured term:
student(kamali, biomedical, 2027).
 
% Pattern matching/unification queries:
% ?- student(Name, biomedical, Year).
% ?- student(kamali, Department, Year).
 
% A rule that matches only a student in the given department:
is_biomedical_student(Name) :-
    student(Name, biomedical, _).