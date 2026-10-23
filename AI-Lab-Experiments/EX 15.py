from sklearn.tree import DecisionTreeClassifier

# Features: [hours studied, hours slept]
X = [[1, 5], [2, 6], [3, 7], [4, 6], [5, 8], [6, 7]]
y = ["Fail", "Fail", "Pass", "Pass", "Pass", "Pass"]

model = DecisionTreeClassifier(random_state=0)
model.fit(X, y)

predictions = model.predict([[2, 5], [5, 7]])
print("Prediction for 2 study hours, 5 sleep hours:", predictions[0])
print("Prediction for 5 study hours, 7 sleep hours:", predictions[1])
