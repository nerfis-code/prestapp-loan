from datetime import datetime, timedelta
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
    detailed_periods = self.process_installments(date)

    if len(detailed_periods) > 1 and detailed_periods[-2].status == "late":
      return "pago_atrasado"
    elif detailed_periods[-1].status == "pending":
      return "pago_pendiente"
    return "periodo_saldado"

  def get_due_date_by_date(self, date: datetime):
    period = self.initial_date + timedelta(days=self.term)

    while period < date:
      period += timedelta(days=self.term)
    
    return period

  def get_number_of_installment(self, date: datetime):
    installment = self.initial_date + timedelta(days=self.term)
    number = 1

    while installment < date:
      installment += timedelta(days=self.term)
      number += 1
    
    return number

  def get_detailed_payments(self) -> list[DetailedPayment]:
    all_payments = []
    for payments in [i.payments for i in self.process_installments(None)]:
      all_payments.extend(payments)
    
    return all_payments
  
  def recalculated_amortization_schedule(self):
    remaining_balance = self.capital
    detailed_payments = self.get_detailed_payments()
    table = []

    for payment in detailed_payments:
      table.append(payment.to_dict())
      remaining_balance -= payment.capital_payment

    number = detailed_payments[-1].number + 1
    date = self.get_due_date_by_date(detailed_payments[-1].date)

    while remaining_balance > 0.01:
      interest_paid = self.rate * remaining_balance
      capital_payment = min(self.fee - interest_paid, remaining_balance)
      remaining_balance -= capital_payment
      date = date + timedelta(days=self.term)

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
      date = date + timedelta(days=self.term)

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
  
  def process_loan(self, now: datetime):
    installments = self.process_installments(now)
    remaining_balance = installments[-1].remaining_balance
    status = "open"

    if remaining_balance > 0.01:
      status = "closed"
    
    return {
      "installments": installments,
      "remaining_balance": remaining_balance,
      "status": status
    }

  def process_installments(self, now: datetime):
    remaining_balance = self.capital
    payment_queue = sorted(self.payments, key=lambda p: p["date"])

    due_dates: list[datetime]
    due_dates = [self.initial_date + timedelta(days=self.term*i) 
                 for i in range(1, self.get_number_of_installment(now or payment_queue[-1]["date"]) + 1)]
    payment_number = 0
    installments: list[Installment] = []
  
    for number, due_date in enumerate(due_dates):
      interest_due = remaining_balance * self.rate

      payments = []
      installment = Installment(
        number=number,
        due_date=due_date,
        status="pending",
        interest=interest_due,
        interest_covered=0,
        capital_covered=0,
        remaining_balance=remaining_balance,
        payments=[],
      )
      
      installments.append(installment)

      while payment_queue and payment_queue[0]["date"] < due_date:
        payment = payment_queue.pop(0)

        detailed_payment = DetailedPayment(
          number=payment_number,
          date=payment["date"],
          amount=payment["amount"],
          interest_paid=0,
          capital_payment=0,
          remaining_balance=0,
        )
        payments.append(detailed_payment)
        payment_number += 1

      remaining_balance = self.process_installment(
        payments,
        installments,
        remaining_balance, 
        installments[-1].number == len(due_dates) - 1
      )

    return installments
  
  def process_installment(
      self, 
      payments: list[DetailedPayment], 
      installments: list[Installment], 
      remaining_balance: float, 
      last_installment: bool
    ):
    installment = installments[-1]

    if len(installments) > 1:
      prev_installment = installments[-2]
      for p in payments:
        self.process_interest(p, prev_installment)

      # Solo sera mora cuando el plazo de pago atrasado concluya sin pagar el interés,
      # osea que no se allá amortizado el interés y el plazo no este anterior al actual
      if prev_installment.status == "late" and not last_installment:
        prev_installment.status = "mora"
        remaining_balance += prev_installment.interest - prev_installment.interest_covered
        installment.interest = remaining_balance * self.rate

    for p in payments:
        self.process_interest(p, installment)
    
    for payment in payments:
      payment.capital_payment = payment.amount - payment.interest_paid
      installment.capital_covered += payment.capital_payment

      remaining_balance -= payment.capital_payment
      payment.remaining_balance = remaining_balance

      installment.payments.append(payment)

    installment.remaining_balance = remaining_balance

    if installment.status != "payed" and not last_installment:
      installment.status = "late"
    
    return remaining_balance

  def process_interest(self, payment: DetailedPayment, installment: Installment):
    if installment.status == "payed" or installment.status == "late payment":
      return
    
    installment.interest_covered = min(installment.interest, payment.amount - payment.interest_paid)
    payment.interest_paid += installment.interest_covered

    if installment.interest_covered == installment.interest:
      installment.status = "payed" if installment.status == "pending" else "late payment"

class Installment:
  def __init__(
      self,
      number: int, 
      due_date: datetime, 
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
      "fecha_final": self.due_date.strftime("%Y-%m-%d"),
      "estado": self.status,
      "interes": self.interest,
      "interes_cubierto": self.interest_covered,
      "capital_cubierto": self.capital_covered,
      "capital_restante": self.remaining_balance,
      "pagos": [p.to_dict() for p in self.payments],
    }

class DetailedPayment:
  def __init__(
      self, 
      number: int, 
      date: datetime, 
      amount: float, 
      interest_paid: float, 
      capital_payment: float, 
      remaining_balance: float
  ):
    self.number = number
    self.date = date
    self.amount = amount
    self.interest_paid = interest_paid
    self.capital_payment = capital_payment
    self.remaining_balance = remaining_balance

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

class DateUtils:
  @staticmethod
  def future(days: int) -> datetime:
    today = datetime.now(ZoneInfo("America/Santo_Domingo"))
    return today + timedelta(days=days)