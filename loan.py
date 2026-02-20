import datetime

class Loan:
  def __init__(self, capital: int, monthly_rate: float, term: int, number_of_installments: int, initial_date: datetime):
    if (term != 15 and term != 30):
      raise Exception("Los plazos en un prestos deben ser a 15 o 30 días")
    
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
    period = self.get_period_by_date(date)

    previous_period = period - datetime.timedelta(days=self.term)

    if previous_period > self.initial_date and len(self.search_payments_by_period(previous_period)) == 0:
      return "pago_atrasado"
    
    if len(self.search_payments_by_period(period)) == 0:
      return "pago_pendiente"
    
    return "periodo_saldado"

  def get_period_by_date(self, date: datetime):
    period = self.initial_date + datetime.timedelta(days=self.term)

    while period < date:
      period += datetime.timedelta(days=self.term)
    
    return period

  def get_detailed_payments(self):
    detailed_payments = list(map(lambda p: p.to_dict(), self.get_detailed_periods().get_detailed_payments()))
    return detailed_payments
  
  def get_detailed_periods(self):
    payments_sorted = sorted(self.payments, key=lambda p: p["date"])
    remaining_balance = self.capital
    pipeline = PaymentPipeline(self, self.get_period_by_date(self.initial_date))

    for number, payment in enumerate(payments_sorted, 1):
      p = pipeline.pipe(
        DetailedPayment(
          number=number,
          date=payment["date"],
          mount=payment["mount"],
          interest_paid=0,
          capital_payment=0,
          remaining_balance=remaining_balance
        )
      )
      remaining_balance = p.remaining_balance
    
    return pipeline

  def search_payments_by_period(self, period: datetime):
    start_date = period - datetime.timedelta(days=self.term)
    end_date = period

    return list(filter(lambda p: start_date <= p["date"] <= end_date, self.payments))

  def recalculated_amortization_schedule(self):
    remaining_balance = self.capital
    detailed_payments = self.get_detailed_periods().get_detailed_payments()
    table = []

    for payment in detailed_payments:
      table.append(payment.to_dict())
      remaining_balance -= payment.capital_payment

    number = detailed_payments[-1].number + 1
    date = self.get_period_by_date(detailed_payments[-1].date)

    while remaining_balance > 0:
      interest_paid = self.rate * remaining_balance
      capital_payment = min(self.fee - interest_paid, remaining_balance)
      remaining_balance -= capital_payment
      date = date + datetime.timedelta(days=self.term)

      table.append(
        DetailedPayment(
          number,
          date,
          capital_payment + interest_paid,
          interest_paid,
          capital_payment,
          remaining_balance
        ).to_dict()
      )
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

      table.append(
        DetailedPayment(
          i + 1,
          date,
          self.fee,
          interest_paid,
          capital_payment,
          remaining_balance
        ).to_dict()
      )
    
    return table

class DetailedPayment:
  def __init__(
      self, 
      number: int, 
      date: datetime.datetime, 
      mount: float, 
      interest_paid: float, 
      capital_payment: float, 
      remaining_balance: float
  ):
    self.number = number
    self.date = date
    self.mount = mount
    self.interest_paid = interest_paid
    self.capital_payment = capital_payment
    self.remaining_balance = remaining_balance

  def to_dict(self):
    return {
      "numero": self.number,
      "fecha": self.date.strftime("%Y-%m-%d"),
      "monto": round(self.mount, 2),
      "interes_pagado": round(self.interest_paid, 2),
      "abono_al_capital": round(self.capital_payment, 2),
      "capital_restante": round(self.remaining_balance, 2),
    }
  
  def to_dict_precise(self):
    return {
      "numero": self.number,
      "fecha": self.date.strftime("%Y-%m-%d"),
      "monto": self.mount,
      "interes_pagado": self.interest_paid,
      "abono_al_capital": self.capital_payment,
      "capital_restante": self.remaining_balance,
    }

class PaymentPipeline:
  def __init__(self, loan: Loan, date: datetime.datetime):
    self.loan = loan
    self.interest: float = None
    self.late_fee = 0
    self.unpaid_interest: float = None
    self.date = date
    self.payments: list[DetailedPayment] = []
    self.child = None
    self.status = "pending"

  def to_dict(self):
    info = {
      "interes": self.interest,
      "interes_sin_pagar": self.unpaid_interest,
      "mora": self.late_fee,
      "fecha": self.date.strftime("%Y-%m-%d"),
      "estado": self.status,
      "pagos": list(map(lambda p: p.to_dict(), self.payments))
    }
    if self.child:
      return [info, *self.child.to_dict()]
    return [info]
  
  def get_detailed_payments(self) -> list[DetailedPayment]:
    if self.child:
      return [*self.payments, *self.child.get_detailed_payments()]
    return [*self.payments] 

  def pipe(self, payment: DetailedPayment) -> DetailedPayment:
    if self.interest == None:
      self.interest = self.loan.rate * payment.remaining_balance
      self.unpaid_interest = self.interest

    diff_days = (self.loan.get_period_by_date(payment.date) - self.date).days
    diff = diff_days / self.loan.term

    if diff < 0:
      raise Exception("Un pago no debería pasar de su periodo objetivo")

    if diff == 0:
      self.status = "payed" if self.pay_interest(payment) == "complete" else self.status
      payment.capital_payment = payment.mount - payment.interest_paid
      payment.remaining_balance -= payment.capital_payment
      self.payments.append(payment)
      return payment
    
    elif diff == 1:
      self.status = "late payment" if self.pay_interest(payment) == "complete" else "late"

    elif diff > 1:
      self.apply_late_fee(payment)
        
    if self.child == None:
      self.child = PaymentPipeline(self.loan, self.date + datetime.timedelta(days=self.loan.term))
    
    return self.child.pipe(payment)
  
  def pay_interest(self, payment):
    if self.unpaid_interest == 0:
      return
    
    if self.unpaid_interest <= payment.mount - payment.interest_paid:
      payment.interest_paid += self.unpaid_interest
      self.unpaid_interest = 0
      return "complete"
    else:
      self.unpaid_interest -= payment.mount - payment.interest_paid
      payment.interest_paid = payment.mount
      return "partial"
    
  def apply_late_fee(self, payment):
    if self.unpaid_interest == 0:
      return
    
    self.status = "mora"
    self.late_fee = self.unpaid_interest
    payment.remaining_balance += self.late_fee
    self.unpaid_interest = 0
