import unittest
from date_utils import DateUtils
from loan import Loan, InstallmentStatus

class TestInterestCapitalization(unittest.TestCase):
    def test_capitalización_del_interés(self):
        d = DateUtils("2026-01-01")
        loan = Loan.create(100_000, 0.2, 30, 10, [], "2026-01-01", d.future(65))
        
        self.assertEqual(loan.installments[0].status, InstallmentStatus.MORA)
        self.assertEqual(loan.installments[0].interest, 20_000)
        self.assertNotEqual(loan.installments[-1].interest, 20_000)
        
if __name__ == '__main__':
    unittest.main()
      