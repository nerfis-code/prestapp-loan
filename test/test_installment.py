import unittest
from date_utils import DateUtils
from loan import Loan

class TestInstallment(unittest.TestCase):
    def test_cantidad_de_cuotas(self):
        d = DateUtils("2026-01-01")
        loan = Loan.create(100_000, 0.2, 30, 10, [], "2026-01-01", d.future(30))
        
        self.assertEqual(len(loan.installments), 2)

if __name__ == '__main__':
    unittest.main()