import unittest
from date_utils import DateUtils
from loan import Loan

class TestLoanStatus(unittest.TestCase):
    def test_estado_pendiente(self):
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-01-01")
        self.assertEqual(loan.status, "pago_pendiente")
        
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-01-15")
        self.assertEqual(loan.status, "pago_pendiente")
        
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-01-30")
        self.assertEqual(loan.status, "pago_pendiente")
    
    def test_estado_atrasado(self):
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-02-01")
        self.assertEqual(loan.status, "pago_atrasado")
        
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-02-15")
        self.assertEqual(loan.status, "pago_atrasado")
        
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-02-28")
        self.assertEqual(loan.status, "pago_atrasado")
        
    def test_estado_saldado(self):
        loan = Loan(100_000, 0.2, 30, 12, [], "2023-01-01", "2023-01-01")
        loan.pay(20_001)
        self.assertEqual(loan.status, "periodo_saldado")