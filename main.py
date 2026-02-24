import json
import pandas
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from loan import Loan

if __name__ == "__main__":
  today = datetime.now(ZoneInfo("America/Santo_Domingo"))

