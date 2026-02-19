import datetime
from zoneinfo import ZoneInfo

from main import Loan


today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))

def test_couta_sin_interes():
  assert Loan(1000, 0.0, 15, 11, today).get_fee() == 90.91

def test_perido_saldado():
  loan = Loan(1000, 0.0, 15, 11, today)
  loan.register_payment(mount=2000, date=today + datetime.timedelta(days=1))

  assert loan.get_status(today) == "Periodo saldado"

def test_pago_pendiente():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today) == "Pago pendiente"

def test_pago_atrasado():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today + datetime.timedelta(days=16)) == "Pago atrasado"