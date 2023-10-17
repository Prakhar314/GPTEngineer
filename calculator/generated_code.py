main.cpp
```
#include "calculator.h"
#include <iostream>
#include <string>

int main() {
    std::string input;
    std::getline(std::cin, input);

    Calculator calculator;
    double result = calculator.calculate(input);

    std::cout << "Result: " << result << std::endl;

    return 0;
}
```

calculator.h
```
#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <string>

class Calculator {
    public:
        double calculate(std::string input);
};

#endif
```

calculator.cpp
```
#include "calculator.h"
#include <iostream>
#include <stack>
#include <vector>

double evaluate(double a, double b, char op) {
    switch (op) {
        case '+': return a + b;
        case '-': return a - b;
        case '*': return a * b;
        case '/': return a / b;
        default: return 0;
    }
}

bool is_operator(char c) {
    return c == '+' || c == '-' || c == '*' || c == '/';
}

int get_precedence(char op) {
    if (op == '+' || op == '-') {
        return 1;
    } else if (op == '*' || op == '/') {
        return 2;
    } else {
        return 0;
    }
}

std::vector<std::string> tokenize(const std::string& input) {
    std::vector<std::string> tokens;
    std::string token;

    for (size_t i = 0; i < input.length(); i++) {
        char c = input[i];

        if (c == ' ') {
            if (!token.empty()) {
                tokens.push_back(token);
                token.clear();
            }
        } else if (is_operator(c)) {
            if (!token.empty()) {
                tokens.push_back(token);
                token.clear();
            }
            tokens.push_back(std::string(1, c));
        } else {
            token += c;
        }
    }

    if (!token.empty()) {
        tokens.push_back(token);
    }

    return tokens;
}

double Calculator::calculate(std::string input) {
    std::vector<std::string> tokens = tokenize(input);
    std::stack<double> values;
    std::stack<char> operators;

    for (size_t i = 0; i < tokens.size(); i++) {
        std::string token = tokens[i];

        if (token.length() == 1 && is_operator(token[0])) {
            while (!operators.empty() && is_operator(operators.top()) &&
                   get_precedence(operators.top()) >= get_precedence(token[0])) {
                double b = values.top();
                values.pop();
                double a = values.top();
                values.pop();
                char op = operators.top();
                operators.pop();
                double result = evaluate(a, b, op);
                values.push(result);
            }
            operators.push(token[0]);
        } else {
            double value = std::stod(token);
            values.push(value);
        }
    }

    while (!operators.empty()) {
        double b = values.top();
        values.pop();
        double a = values.top();
        values.pop();
        char op = operators.top();
        operators.pop();
        double result = evaluate(a, b, op);
        values.push(result);
    }

    return values.top();
}
```

This implementation uses the Shunting Yard Algorithm to convert the input expression into Reverse Polish Notation (RPN), which is then evaluated using a stack. The `tokenize` function splits the input into tokens, which can be either numbers or operators. The `calculate` method takes an input string, tokenizes it, converts it into RPN, and then evaluates it using the stack. 

Note: This implementation assumes that the input is well-formed and does not handle error cases such as division by zero.

CMakeLists.txt
```
cmake_minimum_required(VERSION 3.10)

project(calculator)

add_executable(calculator main.cpp calculator.cpp)
```

this concludes a fully working implementation.