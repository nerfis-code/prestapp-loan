import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan, DateUtils as d

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))
  payments = [
    { "amount": 200, "date": d.future(2) },
    { "amount": 200, "date": d.future(33) },
  ]
  loan = Loan(1000, 0.2, 15, 11, payments, d.future(0), d.future(35))

  loan.pay(200)
  loan.pay(200)
  print(json.dumps(loan.to_dict(), indent=2))
  #print(pandas.DataFrame(loan.outdate_amortization_schedule()))
  #print(json.dumps([i.to_dict() for i in loan.process_installments(d.future(16))], indent=2))
