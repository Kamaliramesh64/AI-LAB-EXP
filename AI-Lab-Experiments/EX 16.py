import math
 
def sigmoid(x):
    return 1 / (1 + math.exp(-x))
 
# Two input neurons, two hidden neurons, one output neuron
inputs = [1.0, 0.5]
w_input_hidden = [[0.4, 0.2], [0.3, 0.7]]
b_hidden = [0.1, 0.1]
w_hidden_output = [0.6, 0.5]
b_output = 0.2
 
# Forward propagation: input layer -> hidden layer
hidden = []
for j in range(2):
    total = sum(inputs[i] * w_input_hidden[i][j] for i in range(2))
    hidden.append(sigmoid(total + b_hidden[j]))
 
# Hidden layer -> output layer
out_sum = sum(hidden[j] * w_hidden_output[j] for j in range(2))
output = sigmoid(out_sum + b_output)
 
print("Input:", inputs)
print("Hidden layer:", [round(x, 4) for x in hidden])
print("Network output:", round(output, 4))