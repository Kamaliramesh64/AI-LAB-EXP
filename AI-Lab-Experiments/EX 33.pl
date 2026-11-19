count_vowels(Text, Count) :-
    string_chars(Text, Characters),
    include(is_vowel, Characters, Vowels),
    length(Vowels, Count).
 
is_vowel(a).
is_vowel(e).
is_vowel(i).
is_vowel(o).
is_vowel(u).
is_vowel('A').
is_vowel('E').
is_vowel('I').
is_vowel('O').
is_vowel('U').
 
% Queries:
% ?- count_vowels("education", N).
% ?- count_vowels("Artificial Intelligence", N).