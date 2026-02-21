import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(15_000, 0.1, 15, 5, today)
  print(loan.fee)

  loan.register_payment(mount=4000, date=today + timedelta(days=13))
  loan.register_payment(mount=4000, date=today + timedelta(days=50))


  print(pandas.DataFrame(loan.recalculated_amortization_schedule()))
  detailed_periods = loan.get_detailed_periods(date=today + timedelta(days=50))

  print(json.dumps(detailed_periods.to_dict(), indent=2))
