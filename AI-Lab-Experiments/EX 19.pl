% student(StudentID, StudentName, SubjectCode).
% teacher(TeacherID, TeacherName, SubjectCode).
student(101, anu, cs101).
student(102, ravi, cs102).
student(103, meena, cs101).
 
teacher(t1, kumar, cs101).
teacher(t2, priya, cs102).
 
% Find the teacher for a student's subject:
subject_teacher(Student, Teacher) :-
    student(_, Student, Code),
    teacher(_, Teacher, Code).
 
% Queries:
% ?- student(ID, anu, Code).
% ?- subject_teacher(meena, Teacher).
% ?- teacher(ID, Name, CS101).