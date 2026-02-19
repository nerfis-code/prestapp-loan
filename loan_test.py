import datetime
from zoneinfo import ZoneInfo

from main import Loan


today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))

def test_cuota_sin_interés():
  assert Loan(1000, 0.0, 15, 11, today).get_fee() == 90.91

def test_periodo_saldado():
  loan = Loan(1000, 0.0, 15, 11, today)
  loan.register_payment(mount=2000, date=today + datetime.timedelta(days=1))

  assert loan.get_status(today) == "Periodo saldado"

def test_pago_pendiente():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today) == "Pago pendiente"

def test_pago_atrasado():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today + datetime.timedelta(days=16)) == "Pago atrasado"

def test_pago_atrasado_paga_mas_interés():
  today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 11, today)
  loan.register_payment(mount=253.963142, date=today + datetime.timedelta(days=16))

  assert loan.get_detailed_payments()[0]["Interés pagado"] == 200

def test_capitalización_interés():
  today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 11, today)
  loan.register_payment(mount=253.963142, date=today + datetime.timedelta(days=31))

  # Paga el interés del periodo actual y el anterior atrasado
  assert loan.get_detailed_payments()[0]["Interés pagado"] == 200
  # Se agrego al capital el interés sin pagar, debido a que llego al 3er periodo sin pagar el 1ro
  # Entonces el capital restantes es la consecuencia de Capital 1100 - 53.963142, 
  # que es el monto restante después de quitar el interés
  assert loan.get_detailed_payments()[0]["Capital restante"] == 1046.036858