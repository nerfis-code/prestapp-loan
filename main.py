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
    self.fee = P * (r * (1+r)**n) / ((1+r)**n - 1) if self.rate != 0 else P / n

  def register_payment(mount: int, date: datetime):
    pass

  def get_status(date: datetime):
    pass

  def get_fee(self) -> float:
    return round(self.fee, 2)

  def amortization_schedule(self):
    # P (r(1+r)^n / (1+r)^n -1)

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
  print(
    pandas.DataFrame(Loan(1000, 0.0, 15, 11, today).amortization_schedule())
  )