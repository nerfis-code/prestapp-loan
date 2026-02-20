import pandas
import datetime
from zoneinfo import ZoneInfo
from loan import Loan

if __name__ == "__main__":
  today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 2, today)
  loan.register_payment(200, today)
  print(pandas.DataFrame(loan.outdate_amortization_schedule()))
