import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan, DateUtils as d

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(15_000, 0.1, 15, 5, today)

  loan.register_payment(800, d.future(3))
  loan.register_payment(800, d.future(23))
  print(json.dumps([i.to_dict() for i in loan.process_loan(d.future(44))], indent=2))
