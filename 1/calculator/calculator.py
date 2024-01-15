"""Simple Calculator

This module contains the class Calculator(), which is a simple tool to validate and calculate an input string and return the result as a float.

Personal learning goals of the author:
* How to validate input using exceptions
* How to handle the order of execution, including parentheses, potentiation, and multiplication 
* How to use the VSCode debugger
* Get more used to writing tests

History of this module
* Initially created a custom calculator 
* Switched to using a stack to add parentheses functionality, analog to https://algodaily.com/challenges/build-a-calculator/python 
    * Expanding onto that with potentiation and thus adding a higher order of execution
"""

import re
from string import ascii_letters

class Calculator():

    def __init__(self) -> None:
        self.allowed_digits: str = "0123456789."

    def validate_input(self, str_to_validate: str) -> int:
        """
        Validates an input string if it can be calculated.\n

        Returns an integer of either 0 as valid or the first error in the following order:\n
        \t0: valid input\n
        \t1: valid input - division by zero\n
        \t2: valid input - missing pair in paranthesis\n
        \t3: valid input - used letters\n
        \t4: valid input - missing an operator between numbers and parenthesis\n
        """

        if re.search("([\d]+/0[()/*-+])|([\d]+/0\Z)", str_to_validate):
            return 1
        elif not str_to_validate.count("(") == str_to_validate.count(")"):
            return 2
        elif re.search("[a-zA-Z]+", str_to_validate):
            return 3
        elif re.search("[0-9]+\(|\)[0-9]+", str_to_validate):
            return 4
        else:
            return 0


    def calculate(self, expression: str) -> float | int:
        """
        Calculates the operation and returns the solution as a float.
        Requires valid string as input.

        Allowed operations are + - / * ** and parentheses ( ) 
        
        Removes empty spaces.
        Changes "**" to "^", because "**" might mix up with the sign/operation "*"

        Order of execution is retained.
        """

        expression: str = expression.replace("**", "^").replace(" ", "") + "+"  

        number: float = 0
        sign: str = "+" 
        stack: list = []

        memory_index: int | None = None


        for index, current in enumerate(expression):
            # Numbers of type float or int
            if current in self.allowed_digits: 
                if memory_index == None:
                    if expression[index + 1] in self.allowed_digits:
                        memory_index = index
                    else: 
                        number = float(current)
                elif expression[index + 1] not in self.allowed_digits:
                    number = float(expression[memory_index:index + 1])
                    memory_index = None
                else:
                    continue
            

            # Handling opening parantheses with a stack
            if current == "(":
                stack.append(sign)
                stack.append("(")
                sign = "+"


            # Operation: Handle potentiation with higher precedence
            if current == "^":
                # Remember current sign and number
                stack.append(sign)
                stack.append(number)

                number = 0
                sign = current

                continue


            # Operation: Execute potentiation after "^" was current
            if sign == "^":
                    last_stack_number = stack.pop()
                    last_stack_sign = stack.pop()

                    power = last_stack_number ** number

                    if last_stack_sign == "+":
                        number = power
                    elif last_stack_sign == "-":
                        number = -power
                    elif last_stack_sign == "*":
                        number = stack.pop() * power
                    elif last_stack_sign == "/":
                        number = stack.pop() / power
                    elif last_stack_sign == "^":
                        number = power
                    else:
                        number = 0

                    sign = "+"


            # Operation: + - * /
            if current in "*/+-" or current == ")" or index == len(expression) - 1:
                if sign == "+":
                    stack.append(number)
                elif sign == "-":
                    stack.append(-number)
                elif sign == "*":
                    stack.append(stack.pop() * number)
                elif sign == "/":
                    stack.append(stack.pop() / number)

                if current == ")":
                    number = 0
                    element = stack.pop()
                    while element != "(":
                        number += element
                        element = stack.pop()
                    sign = stack.pop()
                else:
                    number = 0
                    sign = current

        else:
            solution = sum(stack)
            if solution // 1 == solution:
                solution = int(solution)
            return solution
