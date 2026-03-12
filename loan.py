from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Any, Optional

class DetailedPayment(BaseModel):
    number: int
    date: datetime
    amount: float
    interest_paid: float
    capital_payment: float
    remaining_balance: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "numero": self.number,
            "fecha": self.date.strftime("%Y-%m-%d"),
            "monto": round(self.amount, 2),
            "interes_pagado": round(self.interest_paid, 2),
            "abono_al_capital": round(self.capital_payment, 2),
            "capital_restante": round(self.remaining_balance, 2),
        }

    def to_dict_precise(self) -> dict[str, Any]:
        return {
            "numero": self.number,
            "fecha": self.date.strftime("%Y-%m-%d"),
            "monto": self.amount,
            "interes_pagado": self.interest_paid,
            "abono_al_capital": self.capital_payment,
            "capital_restante": self.remaining_balance,
        }


class InstallmentStatus(Enum):
    PENDING = 0
    LATE = 1
    PAYED = 2
    MORA = 3
    LATE_PAYMENT = 4


class Installment(BaseModel):
    number: int
    due_date: datetime
    status: InstallmentStatus
    interest: float
    interest_covered: float
    capital_covered: float
    remaining_balance: float
    payments: list[DetailedPayment]

    def to_dict(self) -> dict[str, Any]:
        translation = {
            InstallmentStatus.PENDING: "pendiente",
            InstallmentStatus.LATE: "atrasado",
            InstallmentStatus.PAYED: "pagado",
            InstallmentStatus.MORA: "mora",
            InstallmentStatus.LATE_PAYMENT: "pago_atrasado",
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


class LoanStatus(Enum):
    COMPLETED = 0
    LATE = 1
    PENDING = 2
    PAID = 3


class Loan(BaseModel):
    capital: float
    rate: float
    term: int
    number_of_installments: int
    initial_date: datetime
    end_date: datetime
    fee: float
    payments: list[DetailedPayment] = []
    installments: list[Installment] = []
    status: LoanStatus = LoanStatus.PENDING
    remaining_balance: float = 0.0

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        capital: int,
        monthly_rate: float,
        term: int,
        number_of_installments: int,
        payment_history: list[dict[str, Any]],
        initial_date: str,
        end_date: Optional[str] = None,
    ) -> "Loan":
        if term != 15 and term != 30:
            raise Exception("Los plazos en un prestos deben ser a 15 o 30 días")

        rate = monthly_rate if term == 30 else monthly_rate / 2
        P, r, n = capital, rate, number_of_installments
        fee = P * (r * (1 + r) ** n) / ((1 + r) ** n - 1) if rate != 0 else P / n
        parsed_initial = cls._strptime_static(initial_date)
        parsed_end = (
            cls._strptime_static(end_date)
            if end_date is not None
            else datetime.now(ZoneInfo("America/Santo_Domingo"))
        )

        loan = cls(
            capital=capital,
            rate=rate,
            term=term,
            number_of_installments=number_of_installments,
            initial_date=parsed_initial,
            end_date=parsed_end,
            fee=fee,
        )

        for payment in payment_history:
            loan.register_payment(payment)
        loan.process_loan()
        return loan

    @staticmethod
    def _strptime_static(date: str) -> datetime:
        return datetime.strptime(date, "%Y-%m-%d").replace(
            tzinfo=ZoneInfo("America/Santo_Domingo")
        )

    def _strptime(self, date: str) -> datetime:
        return self._strptime_static(date)

    def pay(self, amount: float) -> None:
        if self.status == LoanStatus.COMPLETED:
            raise Exception("Se ha intentado registrar un pago en un préstamo ya concluido")

        detailed_payment = DetailedPayment(
            number=len(self.payments) + 1,
            date=self.end_date,
            amount=amount,
            interest_paid=0,
            capital_payment=0,
            remaining_balance=0,
        )
        self.payments.append(detailed_payment)
        self.remaining_balance = self.process_installment(
            [detailed_payment], self.installments, self.remaining_balance, True
        )
        self.update_status()

    def register_payment(self, payment: dict[str, Any]) -> None:
        amount = payment["amount"]
        date = self._strptime(payment["date"])

        if (date - self.end_date).days >= 1:
            raise Exception("Se ha intentado registrar un pago mas allá de la fecha actual")

        detailed_payment = DetailedPayment(
            number=len(self.payments) + 1,
            date=date,
            amount=amount,
            interest_paid=0,
            capital_payment=0,
            remaining_balance=0,
        )
        self.payments.append(detailed_payment)

    def update_status(self) -> None:
        if self.remaining_balance < 0.1:
            self.status = LoanStatus.COMPLETED
        elif len(self.installments) > 1 \
            and self.installments[-2].status == InstallmentStatus.LATE:
            self.status = LoanStatus.LATE
        elif self.installments[-1].status != InstallmentStatus.PAYED:
            self.status = LoanStatus.PENDING
        else:
            self.status = LoanStatus.PAID

    def get_due_date_by_date(self, date: datetime) -> datetime:
        period = self.initial_date + timedelta(days=self.term)
        while period < date:
            period += timedelta(days=self.term)
        return period

    def get_current_number_of_installment(self) -> int:
        return int((self.end_date - self.initial_date).days / self.term) + 1

    def recalculated_amortization_schedule(self) -> list[dict[str, Any]]:
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
            payment_dict = DetailedPayment(
                number=number,
                date=date,
                amount=capital_payment + interest_paid,
                interest_paid=interest_paid,
                capital_payment=capital_payment,
                remaining_balance=remaining_balance,
            ).to_dict()
            table.append({"estado": "por_pagar", **payment_dict})
            number += 1
            date = date + timedelta(days=self.term)

        return table

    def outdate_amortization_schedule(self) -> list[dict[str, Any]]:
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
                    number=i + 1,
                    date=date,
                    amount=self.fee,
                    interest_paid=interest_paid,
                    capital_payment=capital_payment,
                    remaining_balance=remaining_balance,
                ).to_dict()
            )

        return table

    def process_loan(self) -> None:
        self.installments = self.process_installments()
        self.remaining_balance = self.installments[-1].remaining_balance
        self.update_status()

    def process_installments(self) -> list[Installment]:
        remaining_balance = self.capital
        payment_queue = sorted(self.payments, key=lambda p: p.date)
        due_dates: list[datetime] = [
            self.initial_date + timedelta(days=self.term * i)
            for i in range(1, self.get_current_number_of_installment() + 1)
        ]
        installments: list[Installment] = []

        for number, due_date in enumerate(due_dates):
            interest_due = remaining_balance * self.rate
            installment = Installment(
                number=number + 1,
                due_date=due_date,
                status=InstallmentStatus.PENDING,
                interest=interest_due,
                interest_covered=0,
                capital_covered=0,
                remaining_balance=remaining_balance,
                payments=[],
            )
            installments.append(installment)

            payments = []
            while payment_queue and payment_queue[0].date < due_date:
                payments.append(payment_queue.pop(0))

            remaining_balance = self.process_installment(
                payments,
                installments,
                remaining_balance,
                installments[-1].number == len(due_dates),
            )

        return installments

    def process_installment(
        self,
        payments: list[DetailedPayment],
        installments: list[Installment],
        remaining_balance: float,
        last_installment: bool,
    ) -> float:
        installment = installments[-1]

        if len(installments) > 1:
            prev_installment = installments[-2]
            for p in payments:
                self.process_interest(p, prev_installment)

            if prev_installment.status == InstallmentStatus.LATE and not last_installment:
                prev_installment.status = InstallmentStatus.MORA
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

        if installment.status != InstallmentStatus.PAYED and not last_installment:
            installment.status = InstallmentStatus.LATE

        return max(remaining_balance, 0)

    def process_interest(self, payment: DetailedPayment, installment: Installment) -> None:
        if installment.status in (InstallmentStatus.PAYED, InstallmentStatus.LATE_PAYMENT):
            return

        interest_paid = min(
            installment.interest - installment.interest_covered,
            payment.amount - payment.interest_paid,
        )
        installment.interest_covered += interest_paid
        payment.interest_paid += interest_paid

        if installment.interest_covered == installment.interest:
            installment.status = (
                InstallmentStatus.PAYED
                if installment.status == InstallmentStatus.PENDING
                else InstallmentStatus.LATE_PAYMENT
            )

    def to_dict(self) -> dict[str, Any]:
        translation = {
            LoanStatus.COMPLETED: "concluido",
            LoanStatus.LATE: "pago_atrasado",
            LoanStatus.PENDING: "pago_pendiente",
            LoanStatus.PAID: "periodo_saldado"
        }
        return {
            "fecha_inicial": self.initial_date.strftime("%Y-%m-%d"),
            "fecha_final": self.end_date.strftime("%Y-%m-%d"),
            "capital_restante": self.remaining_balance,
            "estado": translation[self.status],
            "plazos": [l.to_dict() for l in self.installments],
        }