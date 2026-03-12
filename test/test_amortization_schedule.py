import unittest
from date_utils import DateUtils
from loan import Loan

class TestAmortizationSchedule(unittest.TestCase):
    def setUp(self):
        self.loan = Loan.create(100_000, 0.2, 30, 10, [], "2026-01-01")
        self.d = DateUtils("2026-01-01")
        
    def test_cantidad_de_cuotas(self):
        self.assertEqual(len(self.loan.outdate_amortization_schedule()), 10)
        self.assertEqual(len(self.loan.recalculated_amortization_schedule()), 10)

    def test_fechas_de_pago_en_dia_de_corte(self):
        n = self.loan.number_of_installments
        self.assertEqual(
            [self.d.future(self.loan.term * i) for i in range(1, n + 1)],
            list(map(lambda p: p["fecha"], self.loan.outdate_amortization_schedule()))
        )
    
if __name__ == '__main__':
    unittest.main()
