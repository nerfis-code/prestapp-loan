from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
    translation = {
      "pending": "pendiente",
      "late": "atrasado",
      "payed": "pagado",
      "mora": "mora",
      "late payment": "pago_atrasado",
    }
    return {
      "numero": self.number,
      "fecha_final": self.due_date.strftime("%Y-%m-%d"),
      "estado": translation[self.status],
      "interes": self.interest,
      "interes_cubierto": self.interest_covered,
      "capital_cubierto": self.capital_covered,
      "capital_restante": self.remaining_balance,
      "pagos": [p.to_dict() for p in self.payments],
    }

class Loan:
  def __init__(
      self, 
      capital: int, 
      monthly_rate: float, 
      term: int, 
      number_of_installments: int, 
      payment_history: list[dict],
      initial_date: str,
      end_date: str = None,
    ):
    if (term != 15 and term != 30):
      raise Exception("Los plazos en un prestos deben ser a 15 o 30 días")
    
    self.capital = capital
    self.rate = monthly_rate if term == 30 else monthly_rate / 2
    self.term = term
    self.number_of_installments = number_of_installments
    self.initial_date = self._strptime(initial_date)
    self.payments: list[DetailedPayment] = []

    P = self.capital
    r = self.rate
    n = self.number_of_installments
    # P (r(1+r)^n / (1+r)^n -1)
    self.fee = P * (r * (1+r)**n) / ((1+r)**n - 1) if self.rate != 0 else P / n

    self.installments: list[Installment]
    self.status: str
    self.remaining_balance: float
    self.end_date = self._strptime(end_date) if end_date != None else datetime.now(ZoneInfo("America/Santo_Domingo"))
    
    for payment in payment_history:
      self.register_payment(payment)
    self.process_loan()
  
  def _strptime(self, date: str):
    return datetime \
      .strptime(date, "%Y-%m-%d") \
      .replace(tzinfo=ZoneInfo("America/Santo_Domingo"))
  
  def pay(self, amount: float):
    if self.status == "concluido":
      raise Exception("Se ha intentado registrar un pago en un préstamo ya concluido")
    
    detailed_payment = DetailedPayment(
      number=len(self.payments)+1,
      date=self.end_date,
      amount=amount,
      interest_paid=0,
      capital_payment=0,
      remaining_balance=0,
    )
    self.payments.append(detailed_payment)
    
    self.remaining_balance = self.process_installment(
      [detailed_payment],
      self.installments,
      self.remaining_balance,
      True,
    )
    self.update_status()

  def register_payment(self, payment):
    amount = payment["amount"]
    date = self._strptime(payment["date"])
    
    if (date - self.end_date).days >= 1:
      raise Exception("Se ha intentado registrar un pago mas allá de la fecha actual")
    
    detailed_payment = DetailedPayment(
      number=len(self.payments)+1,
      date=date,
      amount=amount,
      interest_paid=0,
      capital_payment=0,
      remaining_balance=0,
    )
    self.payments.append(detailed_payment)

  def update_status(self):
    if self.remaining_balance < 0.01:
      self.status = "concluido"
    elif len(self.installments) > 1 and self.installments[-2].status == "late":
      self.status = "pago_atrasado"
    elif self.installments[-1].status == "pending":
      self.status = "pago_pendiente"
    else:
      self.status = "periodo_saldado"

  def get_due_date_by_date(self, date: datetime):
    period = self.initial_date + timedelta(days=self.term)

    while period < date:
      period += timedelta(days=self.term)
    
    return period

  def get_current_number_of_installment(self):
    return int((self.end_date - self.initial_date).days / self.term) + 1

  def recalculated_amortization_schedule(self):
    remaining_balance = self.capital
    table = []
    number = 1
    date = self.get_due_date_by_date(self.initial_date)
    
    for payment in self.payments:
      table.append({"estado": "pagado", **payment.to_dict()})
      remaining_balance -= payment.capital_payment
      
      number = payment.number + 1
      date = self.get_due_date_by_date(payment.date) + timedelta(days=self.term)

    while remaining_balance > 0.01:
      interest_paid = self.rate * remaining_balance
      capital_payment = min(self.fee - interest_paid, remaining_balance)
      remaining_balance -= capital_payment
      payment = DetailedPayment(
        number,
        date,
        capital_payment + interest_paid,
        interest_paid,
        capital_payment,
        remaining_balance
      ).to_dict()

      table.append({"estado": "por_pagar", **payment})
      number += 1
      date = date + timedelta(days=self.term)

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
  
  def process_loan(self):
    self.installments = self.process_installments()
    self.remaining_balance = self.installments[-1].remaining_balance
    self.update_status()
    
  def process_installments(self):
    remaining_balance = self.capital
    payment_queue = sorted(self.payments, key=lambda p: p.date)

    due_dates: list[datetime]
    due_dates = [self.initial_date + timedelta(days=self.term*i) 
                 for i in range(1, self.get_current_number_of_installment() + 1)]
    installments: list[Installment] = []
  
    for number, due_date in enumerate(due_dates):
      interest_due = remaining_balance * self.rate

      installment = Installment(
        number=number+1,
        due_date=due_date,
        status="pending",
        interest=interest_due,
        interest_covered=0,
        capital_covered=0,
        remaining_balance=remaining_balance,
        payments=[],
      )
      
      installments.append(installment)

      payments = []
      while payment_queue and payment_queue[0].date < due_date:
        detailed_payment = payment_queue.pop(0)
        payments.append(detailed_payment)

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
    
    return max(remaining_balance, 0)

  def process_interest(self, payment: DetailedPayment, installment: Installment):
    if installment.status == "payed" or installment.status == "late payment":
      return
    
    installment.interest_covered = min(installment.interest, payment.amount - payment.interest_paid)
    payment.interest_paid += installment.interest_covered

    if installment.interest_covered == installment.interest:
      installment.status = "payed" if installment.status == "pending" else "late payment"

  def to_dict(self):
    return {
      "fecha_inicial": self.initial_date.strftime("%Y-%m-%d"),
      "fecha_final": self.end_date.strftime("%Y-%m-%d"),
      "capital_restante": self.remaining_balance,
      "estado": self.status,
      "plazos": [l.to_dict() for l in self.installments]
    }
