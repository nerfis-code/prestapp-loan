import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan, DateUtils as d

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 11, today)

  print(json.dumps([i.to_dict() for i in loan.process_loan(d.future(16))], indent=2))
