import unittest
from calculator import calculator


class TestCalculatorMethods(unittest.TestCase):
    
    tc = calculator.Calculator()

    def test_addition(self):
        self.assertEqual(self.tc.calculate("123.45 + 670.89"), 794.34)
    
    def test_substraction(self):
        self.assertAlmostEqual(self.tc.calculate("670.89 - 123.45"), 547.44)
    
    def test_multiplication(self):
        self.assertEqual(self.tc.calculate("123.45 * 670.89"), 82821.3705)
    
    def test_division(self):
        self.assertEqual(self.tc.calculate("123.45 / 670.89"), 0.18400930107767294)
    
    def test_exponentiation_power(self):
        # 2nd to 9th potentiation 
        err_msg = "result of potentiation calculation is wrong"

        self.assertEqual(self.tc.calculate("2 ** 2"), 4.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 3"), 8.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 4"), 16.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 5"), 32.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 6"), 64.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 7"), 128.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 8"), 256.0, err_msg)
        self.assertEqual(self.tc.calculate("2 ** 9"), 512.0, err_msg)

    def test_exponentiation_consecutive_power(self):
        self.assertEqual(self.tc.calculate("2 ** 2 ** 2"), 16.0,
                         "result of consecutive potentiation calculation is wrong")

    def test_exponentiation_roots(self):

        # square root
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/2)"), 11.111110696055547, 
                         "result of square root claculation is wrong")

        # qubic root
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/3)"), 4.979338483283606, 
                         "result of qubic root claculation is wrong")
        
        # 4th to 9th root 
        err_msg = "result of root is wrong"

        self.assertEqual(self.tc.calculate("123.4567809 ** (1/4)"), 3.333333271074998, err_msg)
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/5)"), 2.620010246173881, err_msg)
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/6)"), 2.2314431391553775, err_msg)
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/7)"), 1.9897011447521342, err_msg)
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/8)"), 1.8257418413004063, err_msg)
        self.assertEqual(self.tc.calculate("123.4567809 ** (1/9)"), 1.7076173150528808, err_msg)


    def test_operations_hirarchy(self):
        # PEMDAS: Parentheses, Exponents, Multiplication/Division,
        #         Addition/Subtraction from left to right.
        self.assertEqual(self.tc.calculate("10 + 15 * (3 - 8) ** 5"), -46865.0, "order of operation is violated")

    def test_string_vaildation(self):
        # validate_input() returns True if input is valid, otherwise it returns a list of exceptions
        self.assertEqual(self.tc.validate_input("10+0.23023--100*(15-5)**2"), 0)
        
        # division by zero
        self.assertEqual(self.tc.validate_input("10/0"), 1)
        
        # missing a pair of paranthesis
        self.assertEqual(self.tc.validate_input("10+0.23023--100*15-5)**2"), 2)

        # no letters allowed
        self.assertEqual(self.tc.validate_input("10/15a"), 3)

        # missing an operator between paranthesis and numbers
        self.assertEqual(self.tc.validate_input("10+0.23023(100*15-5)**2"), 4)


if __name__ == "__name__":
    unittest.main()