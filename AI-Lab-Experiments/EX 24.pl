% food_for(Disease, Food).
food_for(diabetes, whole_grains).
food_for(diabetes, leafy_vegetables).
food_for(diabetes, legumes).
 
food_for(hypertension, fruits).
food_for(hypertension, vegetables).
food_for(hypertension, low_sodium_food).
 
food_for(anemia, iron_rich_food).
food_for(anemia, beans).
food_for(anemia, spinach).
 
diet_suggestion(Disease, Food) :-
    food_for(Disease, Food).
 
% Queries:
% ?- diet_suggestion(diabetes, Food).
% ?- diet_suggestion(hypertension, Food).