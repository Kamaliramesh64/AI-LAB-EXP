symptom(patient1, fever).
symptom(patient1, cough).
symptom(patient1, body_pain).
 
symptom(patient2, sneezing).
symptom(patient2, runny_nose).
 
symptom(patient3, fever).
symptom(patient3, headache).
symptom(patient3, body_pain).
 
diagnosis(Patient, flu_like_illness) :-
    symptom(Patient, fever),
    symptom(Patient, cough),
    symptom(Patient, body_pain).
 
diagnosis(Patient, common_cold_like_illness) :-
    symptom(Patient, sneezing),
    symptom(Patient, runny_nose).
 
diagnosis(Patient, fever_with_body_pain) :-
    symptom(Patient, fever),
    symptom(Patient, headache),
    symptom(Patient, body_pain).
 
% Queries:
% ?- diagnosis(patient1, Disease).
% ?- diagnosis(patient2, Disease).