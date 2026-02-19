import datetime
from zoneinfo import ZoneInfo

from main import Loan


today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))

def test_couta_sin_interes():
  assert Loan(1000, 0.0, 15, 11, today).get_fee() == 90.91