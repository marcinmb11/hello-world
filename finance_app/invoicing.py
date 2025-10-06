"""Simple invoicing utilities compliant with Polish requirements."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List

from .project_module import AcceptanceProtocol


@dataclass
class InvoiceIssuer:
    name: str
    address: str
    nip: str  # Polish tax identification number
    bank_account: str


@dataclass
class InvoiceBuyer:
    name: str
    address: str
    nip: str


@dataclass
class InvoiceLine:
    description: str
    net_amount: float
    tax_rate: float

    def tax_amount(self) -> float:
        return self.net_amount * self.tax_rate / 100

    def gross_amount(self) -> float:
        return self.net_amount + self.tax_amount()


@dataclass
class Invoice:
    number: str
    issue_date: date
    sale_date: date
    issuer: InvoiceIssuer
    buyer: InvoiceBuyer
    payment_terms: str
    lines: List[InvoiceLine] = field(default_factory=list)

    def total_net(self) -> float:
        return sum(line.net_amount for line in self.lines)

    def total_tax(self) -> float:
        return sum(line.tax_amount() for line in self.lines)

    def total_gross(self) -> float:
        return sum(line.gross_amount() for line in self.lines)


class InvoiceGenerator:
    """Create invoices from acceptance protocols."""

    def __init__(self, issuer: InvoiceIssuer) -> None:
        self.issuer = issuer

    def from_acceptance(
        self,
        protocol: AcceptanceProtocol,
        buyer: InvoiceBuyer,
        invoice_number: str,
        payment_terms: str = "14 dni",
        tax_rate: float = 23.0,
    ) -> Invoice:
        line = InvoiceLine(
            description=f"Protokół odbioru: {protocol.protocol_number} - {protocol.accepted_scope}",
            net_amount=protocol.value,
            tax_rate=tax_rate,
        )
        invoice = Invoice(
            number=invoice_number,
            issue_date=date.today(),
            sale_date=protocol.date_signed,
            issuer=self.issuer,
            buyer=buyer,
            payment_terms=payment_terms,
            lines=[line],
        )
        return invoice
