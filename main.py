import pandas
import datetime
from zoneinfo import ZoneInfo

class Loan:
  def __init__(self, capital: int, monthly_rate: float, term: int, number_of_installments: int, initial_date: datetime):
    if (term != 15 and term != 30):
      raise Exception("Los plazos en un prestos deben ser a 15 o 30 dias")
    
    self.capital = capital
    self.rate = monthly_rate if term == 30 else monthly_rate / 2
    self.term = term
    self.number_of_installments = number_of_installments
    self.initial_date = initial_date
    self.payments = []

    P = self.capital
    r = self.rate
    n = self.number_of_installments
    # P (r(1+r)^n / (1+r)^n -1)
    self.fee = P * (r * (1+r)**n) / ((1+r)**n - 1) if self.rate != 0 else P / n

  #TODO No se pueda registrar un pago que no cubra el interés
  def register_payment(self, mount: int, date: datetime):
    self.payments.append(dict(mount=mount, date=date))

  def get_status(self, date: datetime):
    period = self._get_period_by_date(date)

    previous_period = period - datetime.timedelta(days=self.term)

    if previous_period > self.initial_date and len(self._search_payments_by_period(previous_period)) == 0:
      return "Pago atrasado"
    
    if len(self._search_payments_by_period(period)) == 0:
      return "Pago pendiente"
    
    return "Periodo saldado"

  def _get_period_by_date(self, date: datetime):
    period = self.initial_date + datetime.timedelta(days=self.term)

    while period < date:
      period += datetime.timedelta(days=self.term)
    
    return period

  def get_detailed_payments(self):
    detailed_payments = []
    payments_sorted = sorted(self.payments, key=lambda p: p["date"])
    remaining_balance = self.capital
    period_interest = self.rate * remaining_balance

    for i in range(len(payments_sorted)):
      payment = payments_sorted[i]
      is_first_payment = i == 0
      previous_date: datetime = payments_sorted[i-1]["date"] if not is_first_payment else self.initial_date
      diff = (self._get_period_by_date(payment["date"]) - self._get_period_by_date(previous_date)).days / self.term

      if is_first_payment: diff += 1

      if diff == 0:
        pass
      elif diff == 1: # Pago a tiempo
        period_interest = self.rate * remaining_balance
      elif diff == 2: # Pago atrasado
        period_interest = self.rate * remaining_balance * 2
      else: # Mora
        late_fee = diff - 2
        remaining_balance += late_fee * period_interest
        period_interest *= 2

      #Este modelo se basa en que el mondo siempre cubre el interés
      remaining_balance -= payment["mount"] - period_interest
      detailed_payments.append({
        "fecha": payment["date"],
        "monto": payment["mount"],
        "interes_pagado": period_interest,
        "abono_al_capital": payment["mount"] - period_interest,
        "capital_restante": remaining_balance
      })
      period_interest = 0

    return detailed_payments
  
  def _search_payments_by_period(self, period: datetime):
    start_date = period - datetime.timedelta(days=self.term)
    end_date = period

    return list(filter(lambda p: start_date <= p["date"] <= end_date, self.payments))

  def recalculated_amortization_schedule(self):
    remaining_balance = self.capital
    detailed_payments = self.get_detailed_payments()
    table = []
    number = 1

    for payment in detailed_payments:
      remaining_balance -= payment["monto"]

      table.append({
        "numero": number,
        "fecha": payment["fecha"],
        "cuota": payment["monto"],
        "interes_pagado": payment["interes_pagado"],
        "abono_al_capital": payment["abono_al_capital"],
        "saldo_restante": remaining_balance
      })

      number += 1

    date = self._get_period_by_date(detailed_payments[-1]["fecha"])
    while remaining_balance > 0:
      interest_paid = self.rate * remaining_balance
      capital_payment = min(self.fee - interest_paid, remaining_balance)
      remaining_balance -= capital_payment
      date = date + datetime.timedelta(days=self.term)

      table.append({
        "numero": number,
        "fecha": date.strftime("%Y-%m-%d"),
        "cuota": capital_payment + interest_paid,
        "interes_pagado": interest_paid,
        "abono_al_capital": capital_payment,
        "saldo_restante": remaining_balance
      })

      number += 1

    return table

  def outdate_amortization_schedule(self):
    remaining_balance = self.capital
    date: datetime = self.initial_date
    table = []

    for i in range(self.number_of_installments):
      interest_paid = self.rate * remaining_balance
      capital_payment = self.fee - interest_paid
      remaining_balance -= capital_payment
      date = date + datetime.timedelta(days=self.term)

      table.append({
        "numero": i + 1,
        "fecha": date.strftime("%Y-%m-%d"),
        "cuota": self.fee,
        "interes_pagado": interest_paid,
        "abono_al_capital": capital_payment,
        "saldo_restante": remaining_balance
      })
    
    return table

if __name__ == "__main__":
  today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.2, 15, 2, today)
  loan.register_payment(200, today)
  print(pandas.DataFrame(loan.recalculated_amortization_schedule()))
  print(pandas.DataFrame(loan.outdate_amortization_schedule()))

  # for i in range(11):
  #   loan.register_payment(mount=153.963142, date=today + datetime.timedelta(days=16*i))
  
  # print(pandas.DataFrame(loan.get_detailed_payments()))
  # print(pandas.DataFrame(loan.outdate_amortization_schedule()))