import datetime
from zoneinfo import ZoneInfo
from loan import Loan

today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))

def test_cuota_sin_interés():
  assert round(Loan(1000, 0.0, 15, 11, today).fee, 2) == 90.91

def test_periodo_saldado():
  loan = Loan(1000, 0.0, 15, 11, today)
  loan.register_payment(amount=2000, date=today + datetime.timedelta(days=1))

  assert loan.get_status(today) == "periodo_saldado"

def test_pago_pendiente():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today) == "pago_pendiente"

def test_pago_atrasado():
  assert Loan(1000, 0.0, 15, 11, today).get_status(today + datetime.timedelta(days=16)) == "pago_atrasado"

def test_pago_atrasado_paga_mas_interés():
  loan = Loan(1000, 0.2, 15, 11, today)
  loan.register_payment(amount=253.963142, date=today + datetime.timedelta(days=16))

  assert loan.get_detailed_payments()[0]["interes_pagado"] == 200

def test_capitalización_interés():
  loan = Loan(1000, 0.2, 15, 11, today)
  loan.register_payment(amount=300, date=today + datetime.timedelta(days=31))

  # Paga el interés del periodo actual y el anterior atrasado
  assert loan.get_detailed_payments()[0]["interes_pagado"] == 220
  # Se agrego al capital el interés sin pagar, debido a que llego al 3er periodo sin pagar el 1ro
  # Entonces el capital restantes es la consecuencia de Capital 1100 - 300 - 220, 
  # que es el monto restante después de quitar el interés
  assert loan.get_detailed_payments()[0]["capital_restante"] == 1020

def test_pago_final_menor_cuota():
  loan = Loan(1000, 0.2, 15, 2, today)
  loan.register_payment(200, today)
  # La cuota aquí esta definida en 576.19, pero debido a que solo se necesita 455.19 para concluir el préstamo,
  # ese monto se designa
  assert loan.recalculated_amortization_schedule()[-1]["monto"] == 455.19