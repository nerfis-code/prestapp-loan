import unittest
from date_utils import DateUtils
from loan import Loan, InstallmentStatus, LoanStatus

class TestPagosParciales(unittest.TestCase):
    def test_pago_de_interes_entre_pagos(self):
        payments = [
            {"amount": 10_000, "date": "2026-01-15"},
            {"amount": 10_000, "date": "2026-01-15"},
        ]
        loan = Loan.create(100_000, 0.2, 30, 10, payments, "2026-01-01", "2026-01-15")
        self.assertEqual(loan.payments[0].interest_paid, 10_000)
        self.assertEqual(loan.payments[1].interest_paid, 10_000)
        self.assertEqual(loan.remaining_balance, 100_000)

    def test_pagar_interest_pendiente_de_plazo_atrasado(self):
        payments = [
            {"amount": 10_000, "date": "2026-01-15"},
            {"amount": 30_000, "date": "2026-02-15"},
        ]
        loan = Loan.create(100_000, 0.2, 30, 10, payments, "2026-01-01", "2026-02-15")
        self.assertEqual(loan.installments[0].status, InstallmentStatus.LATE_PAYMENT)
        self.assertEqual(loan.installments[1].status, InstallmentStatus.PAYED)
        self.assertEqual(loan.status, LoanStatus.PAID)
        self.assertEqual(loan.payments[0].interest_paid, 10_000)
        self.assertEqual(loan.payments[1].interest_paid, 30_000)
        self.assertEqual(loan.remaining_balance, 100_000)


if __name__ == '__main__':
    unittest.main()