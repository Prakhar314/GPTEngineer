main.cpp
```
#include <iostream>
#include "calculator.h"

int main() {
    Calculator calculator;
    calculator.run();
    return 0;
}
```

calculator.h
```
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    void run();
};

#endif
```

calculator.cpp
```
#include <iostream>
#include "calculator.h"

void Calculator::run() {
    double num1, num2;
    char op;

    std::cout << "Enter first number: ";
    std::cin >> num1;

    std::cout << "Enter operator (+, -, *, /): ";
    std::cin >> op;

    std::cout << "Enter second number: ";
    std::cin >> num2;

    double result;

    switch (op) {
        case '+':
            result = num1 + num2;
            break;
        case '-':
            result = num1 - num2;
            break;
        case '*':
            result = num1 * num2;
            break;
        case '/':
            result = num1 / num2;
            break;
        default:
            std::cout << "Invalid operator";
            return;
    }

    std::cout << "Result: " << result << std::endl;
}
```

This concludes a fully working implementation.