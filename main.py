import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan, DateUtils as d

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 11, today, d.future(35))
  loan.register_payment(amount=1000)

  print(json.dumps(loan.to_dict(), indent=2))
  #print(pandas.DataFrame(loan.outdate_amortization_schedule()))
  #print(json.dumps([i.to_dict() for i in loan.process_installments(d.future(16))], indent=2))
