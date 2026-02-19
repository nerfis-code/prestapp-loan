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

  def register_payment(self, mount: int, date: datetime):
    self.payments.append(dict(mount=mount, date=date))

  def get_status(self, date: datetime):
    current_period = self.initial_date + datetime.timedelta(days=self.term)

    while current_period < date:
      current_period += datetime.timedelta(days=self.term)

    previous_period = current_period - datetime.timedelta(days=self.term)

    if previous_period > self.initial_date and len(self._search_payments_by_period(previous_period)) == 0:
      return "Pago atrasado"
    
    if len(self._search_payments_by_period(current_period)) == 0:
      return "Pago pendiente"
    
    return "Periodo saldado"

  def _search_payments_by_period(self, period: datetime):
    start_date = period - datetime.timedelta(days=self.term)
    end_date = period

    return list(filter(lambda p: start_date <= p["date"] <= end_date, self.payments))

  def get_fee(self) -> float:
    return round(self.fee, 2)

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
        "Número": i + 1,
        "Fecha": date.strftime("%Y-%m-%d"),
        "Cuota": self.fee,
        "Interes pagado": interest_paid,
        "Abono al capital": capital_payment,
        "Saldo restante": remaining_balance
      })
    
    return table

if __name__ == "__main__":
  today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
  loan = Loan(1000, 0.0, 15, 11, today)
  loan.register_payment(mount=2000, date=today + datetime.timedelta(days=1))
  print(loan.get_status(today))
  print(pandas.DataFrame(loan.outdate_amortization_schedule()))