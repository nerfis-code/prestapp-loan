import datetime
from zoneinfo import ZoneInfo

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

  def register_payment(self, amount: int, date: datetime):
    self.payments.append(dict(amount=amount, date=date))

  def get_status(self, date: datetime):
    detailed_periods = self.get_detailed_periods(date).to_dict()

    if len(detailed_periods) > 1 and detailed_periods[-2]["estado"] == "late":
      return "pago_atrasado"
    elif detailed_periods[-1]["estado"] == "pending":
      return "pago_pendiente"
    return "periodo_saldado"

  def get_due_date_by_date(self, date: datetime.datetime):
    period = self.initial_date + datetime.timedelta(days=self.term)

    while period < date:
      period += datetime.timedelta(days=self.term)
    
    return period

  def get_number_of_installment(self, date: datetime.datetime):
    installment = self.initial_date + datetime.timedelta(days=self.term)
    number = 1

    while installment < date:
      installment += datetime.timedelta(days=self.term)
      number += 1
    
    return number

  def get_detailed_payments(self):
    detailed_payments = list(map(lambda p: p.to_dict(), self.get_detailed_periods().get_detailed_payments()))
    return detailed_payments
  
  def get_detailed_periods(self, date: datetime.datetime=None):
    payments_sorted = sorted(self.payments, key=lambda p: p["date"])
    remaining_balance = self.capital
    pipeline = PaymentPipeline(self, self.get_due_date_by_date(self.initial_date))

    for number, payment in enumerate(payments_sorted, 1):
      p = pipeline.pipe(
        DetailedPayment(
          number=number,
          date=payment["date"],
          amount=payment["amount"],
          interest_paid=0,
          capital_payment=0,
          remaining_balance=remaining_balance
        )
      )
      remaining_balance = p.remaining_balance
    
    if date != None:
      pipeline.pipe(
        DetailedPayment(
          number=-1,
          date=date,
          amount=0,
          interest_paid=0,
          capital_payment=0,
          remaining_balance=remaining_balance,
          wildcard=True
        )
      )

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
    date = self.get_due_date_by_date(detailed_payments[-1].date)

    while round(remaining_balance, 0) != 0:
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
  
  def process_loan(self, now: datetime.datetime):
    remaining_balance = self.capital
    payment_queue = sorted(self.payments, key=lambda p: p["date"])

    due_dates: list[datetime.datetime] = [self.initial_date + datetime.timedelta(days=self.term*i) 
                 for i in range(1, self.get_number_of_installment(now or payment_queue[-1]["date"]) + 1)]
    
    installments = []
  
    for number, due_date in enumerate(due_dates):
      interest_due = remaining_balance * self.rate

      payments = []
      installment = {
        "number": number,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "status": "pending",
        "interest": interest_due,
        "interest_covered": 0,
        "capital_covered": 0,
        "remaining_balance": remaining_balance,
        "payments": []
      }

      while payment_queue and payment_queue[0]["date"] < due_date:
        payment = payment_queue.pop(0)

        detailed_payment = DetailedPayment(
          number=0,
          date=payment["date"],
          amount=payment["amount"],
          interest_paid=0,
          capital_payment=0,
          remaining_balance=0,
        )
        payments.append(detailed_payment)
      
      if len(installments) > 0:
        prev_installment = installments[-1]
        [self.process_payment(p, prev_installment) for p in payments]
        if prev_installment["status"] == "late":
          prev_installment["status"] = "mora"
          remaining_balance += prev_installment["interest"] - prev_installment["interest_covered"] 

      [self.process_payment(p, installment) for p in payments]
      
      for payment in payments:
        installment["capital_covered"] += payment.capital_payment
        remaining_balance -= payment.capital_payment
        payment.remaining_balance = remaining_balance
        installment["payments"].append(payment.to_dict())

      installment["remaining_balance"] = remaining_balance

      if installment["status"] != "payed" and number != len(due_dates) - 1:
        installment["status"] = "late"
      
      installments.append(installment)

    return installments
  
  def process_payment(self, payment: DetailedPayment, installment):
    if installment["status"] == "payed" or installment["status"] == "late payment":
      return
    
    installment["interest_covered"] = min(installment["interest"], payment.amount - payment.interest_paid)
    payment.interest_paid += installment["interest_covered"]
    payment.capital_payment = payment.amount - payment.interest_paid

    if installment["interest_covered"] == installment["interest"]:
      installment["status"] = "payed" if installment["status"] == "pending" else "late payment"

class Installment:
  def __init__(
      self,
      number: int, 
      due_date: datetime.datetime, 
      status: str, 
      interest: float, 
      interest_covered: float,
      capital_covered: float,
      remaining_balance: float,
      payments: list[DetailedPayment]
  ):
    self.number = number
    self.due_date = due_date
    self.status = status
    self.interest = interest
    self.interest_covered = interest_covered
    self.capital_covered = capital_covered
    self.remaining_balance = remaining_balance
    self.payments = payments

  def to_dict(self):
    return {
      "numero": self.number,
      "fecha_final": self.due_date,
      "estado": self.status,
      "interes": self.interest,
      "interes_cubierto": self.interest_covered,
      "capital_cubierto": self.capital_covered,
      "capital_restante": self.remaining_balance,
      "numero": [p.to_dict() for p in self.payments],
    }


class DetailedPayment:
  def __init__(
      self, 
      number: int, 
      date: datetime.datetime, 
      amount: float, 
      interest_paid: float, 
      capital_payment: float, 
      remaining_balance: float,
      wildcard: bool=False
  ):
    self.number = number
    self.date = date
    self.amount = amount
    self.interest_paid = interest_paid
    self.capital_payment = capital_payment
    self.remaining_balance = remaining_balance
    self.wildcard = wildcard

  def to_dict(self):
    return {
      "numero": self.number,
      "fecha": self.date.strftime("%Y-%m-%d"),
      "monto": round(self.amount, 2),
      "interes_pagado": round(self.interest_paid, 2),
      "abono_al_capital": round(self.capital_payment, 2),
      "capital_restante": round(self.remaining_balance, 2),
    }
  
  def to_dict_precise(self):
    return {
      "numero": self.number,
      "fecha": self.date.strftime("%Y-%m-%d"),
      "monto": self.amount,
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
      "fecha_de_corte": self.date.strftime("%Y-%m-%d"),
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

    diff_days = (self.loan.get_due_date_by_date(payment.date) - self.date).days
    diff = diff_days / self.loan.term

    if diff < 0:
      raise Exception("Un pago no debería pasar de su periodo objetivo")

    if diff == 0:
      if payment.wildcard: return
      self.status = "payed" if self.pay_interest(payment) == "complete" else self.status
      payment.capital_payment = payment.amount - payment.interest_paid
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
      return "complete"
    
    if self.unpaid_interest <= payment.amount - payment.interest_paid:
      payment.interest_paid += self.unpaid_interest
      self.unpaid_interest = 0
      return "complete"
    else:
      self.unpaid_interest -= payment.amount - payment.interest_paid
      payment.interest_paid = payment.amount
      return "partial"
    
  def apply_late_fee(self, payment):
    if self.unpaid_interest == 0:
      return
    
    self.status = "mora"
    self.late_fee = self.unpaid_interest
    payment.remaining_balance += self.late_fee
    self.unpaid_interest = 0

class DateUtils:
  @staticmethod
  def future(days: int) -> datetime.datetime:
    today = datetime.datetime.now(ZoneInfo("America/Santo_Domingo"))
    return today + datetime.timedelta(days=days)