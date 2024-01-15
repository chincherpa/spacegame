# Project: Calculator with GUI

This is a simple calculator with a GUI using [PySimpleGui](https://www.pysimplegui.org/en/latest/)
> **Goal:** GUI, calculations and call functions in order

## Task

Create a Calculator WITHOUT using eval() on the input

### Input

* GUI input
  * numbers
  * operations
    * Addition (+)
    * Subtraction (-)
    * Multiplication (*)
    * Division (/)
    * Exponentiation
      * potentiation (**)
      * square root (sqrt())
      * cubic root (**(1./3.))
      * x root (**(1./x.))
  * minus sign (-)
  * float point
  * compute (=)

### Conversions

* check if calculation is possible (division by 0)
* calculate

### Output

* result
* Feedback when division is not possible

## Psuedo code

```text
TipCalculator
    Initialize calculator
    Initialize GUI
        buttons
        text-field

    Repeat
        Get input
        Update text-field
    
    On calculate
        Split field input to numbers and operations
        Convert numbers to numbers (float)
        Calculate operations in order while checking if operations are possible
    
    Feedback-Pop-Up on error if there is an error
    Display result
End

```

## Project Structure

```text
.
├── .gitignore
├── readme.md
├── requirements.txt
├── simple_gui.py
├── calculator
│   ├── __init__.py
│   └── calculator.py
└── tests/
    ├── __init__.py
    └── test_calculator.py
```

## Tests

* Operations (as float)
  * Addition (+)
  * Subtraction (-)
  * Multiplication (*)
  * Division (/)
  * Exponentiation
    * potentiation (x**y)
    * consecutive potentiation (x\*\*y\*\*z)
    * square root (sqrt(x))
    * cubic root (x**(1/3))
    * xth root (y**(1/x))
* Division by 0
* Operations hierarchy (PEMDAS[^1])
  * Parentheses, Exponentiation, Multiplication/Division, Addition/Subtraction from left to right.
* Input-string validation  

### Assertion-Test: Operations (as float)

**Test-Plan: Addition (+)**

```text
Inputs:
  123.45 + 670.89
Expected result:
  794.34
```

**Test-Plan: Substraction (-)**

```text
Inputs:
  670.89 - 123.45
Expected result:
  547.44
```

**Test-Plan: Multiplication (*)**

```text
Inputs:
    123.45 * 670.89
Expected result:
  82821.3705
```

**Test-Plan: Division (/)**

```text
Inputs:
  123.45 / 670.89
Expected result:
  0.18400930107767294
```

**Test-Plan: Exponentiation, potentiate (x\*\*y)**

```text
Inputs:
  2 ** 2
  2 ** 3
  2 ** 4
  2 ** 5
  2 ** 6
  2 ** 7
  2 ** 8
  2 ** 9
Expected result:
  4
  8
  16
  32
  64
  128
  256
  512
```

**Test-Plan: Exponentiation, consecutive potentiation (x\*\*y\*\*z)**

```text
Inputs:
  2 ** 2 ** 2
Expected result:
  16
```

**Test-Plan: Exponentiation, square root (sqrt(x))**

```text
Inputs:
  123.4567809 ** (1/2)
Expected result:
  11.111110696055547
```

**Test-Plan: Exponentiation, qubic root (x\*\*(1/3))**

```text
Inputs:
  123.4567809 ** (1/3)
Expected result:
  4.979338483283606
```

**Test-Plan: Exponentiation, xth root (y\*\*(1/x))**

```text
Inputs:
  123.4567809 ** (1/4)
  123.4567809 ** (1/5)
  123.4567809 ** (1/6)
  123.4567809 ** (1/7)
  123.4567809 ** (1/8)
  123.4567809 ** (1/9)
Expected result:
  3.333333271074998
  2.620010246173881
  2.2314431391553775
  1.9897011447521342
  1.8257418413004063
  1.7076173150528808

```

### Assertion-Test: Division by 0

**Test-Plan:**

```text
Inputs:
  10 / 0 
Expected result:
  ZeroDivisionError
```

### Assertion-Test: Operations hierarchy (PEMDAS)

**Test-Plan:**

```text
Inputs:
  10 + 15 * (3 - 8) ** 5
Expected result:
  -46865
```

### Assertion-Test: Input-string validation

**Test-Plan:**

```text
Inputs:
  10+0.23023--100*(15-5)**2
  10/15a
  10/0
  10+0.23023--100*15-5)**2
  10+0.23023(100*15-5)**2
Expected result:
  True
  Type = str
  Type = str
  Type = str
  Type = str
```

## Additional, optional Tasks

* Add brackets/parentheses functionality
* Add scientific calculations
* Display thousand-separator on input "1,000,000.00"

[^1]: [Order of operations](https://en.wikipedia.org/wiki/Order_of_operations) from *Ali Rahman, Ernna Sukinnah; Shahrill, Masitah; Abbas, Nor Arifahwati*; Tan, Abby (Summer 2017) [2016-08-29, 2017-03-06]. "Developing Students' Mathematical Skills Involving Order of Operations" ([:link: PDF](https://files.eric.ed.gov/fulltext/EJ1148460.pdf)). *International Journal of Research in Education and Science (IJRES)*. University of Brunei Darussalam. 3 (2): 373–382. [doi:10.21890/ijres.327896](https://doi.org/10.21890%2Fijres.327896). [ISSN 2148-9955](https://www.worldcat.org/issn/2148-9955).
