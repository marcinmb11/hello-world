"""Tools for modelling company-wide costs needed to calculate hourly rates."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EmployeeCompensation:
    """Represents the cost of an employee on an employment contract."""

    name: str
    net_salary: float
    gross_salary: float
    salary_components: Dict[str, float]

    def total_cost(self) -> float:
        """Return the total gross cost for the employee."""
        return self.gross_salary


@dataclass
class BoardTaxScale:
    """Progressive tax scale for Polish PIT calculation."""

    first_threshold: float = 120_000.0
    first_rate: float = 0.12
    second_rate: float = 0.32
    tax_free_amount: float = 30_000.0

    def calculate_tax(self, taxable_income: float) -> float:
        """Return annual PIT value for the provided taxable income."""
        if taxable_income <= self.tax_free_amount:
            return 0.0
        taxable_income -= self.tax_free_amount
        if taxable_income <= self.first_threshold:
            return taxable_income * self.first_rate
        return (
            self.first_threshold * self.first_rate
            + (taxable_income - self.first_threshold) * self.second_rate
        )


@dataclass
class BoardMemberCompensation:
    """Compensation data for a management board member."""

    name: str
    gross_salary: float
    social_security: float
    health_insurance: float
    tax_scale: BoardTaxScale = field(default_factory=BoardTaxScale)

    def annual_cost(self) -> float:
        """Return the total annual gross cost including contributions and tax."""
        taxable_income = max(self.gross_salary * 12 - self.social_security * 12, 0.0)
        tax = self.tax_scale.calculate_tax(taxable_income)
        return self.gross_salary * 12 + self.social_security * 12 + self.health_insurance * 12 + tax


@dataclass
class OfficeCost:
    """Cost entry for office expenses (rent, utilities, supplies)."""

    description: str
    amount: float
    category: str


@dataclass
class AdditionalCost:
    """Represents an additional company-wide cost such as insurance."""

    description: str
    amount: float


@dataclass
class LeasingCost:
    """Represents a car leasing cost and deductible portion."""

    description: str
    amount: float
    deductible_ratio: float  # 0.5 for 50%, 1.0 for 100%

    def deductible_amount(self) -> float:
        return self.amount * self.deductible_ratio


@dataclass
class CompanyCosts:
    """Aggregates all costs and exposes helper calculations."""

    employees: List[EmployeeCompensation] = field(default_factory=list)
    office_costs: List[OfficeCost] = field(default_factory=list)
    additional_costs: List[AdditionalCost] = field(default_factory=list)
    leasing_costs: List[LeasingCost] = field(default_factory=list)
    board_compensations: List[BoardMemberCompensation] = field(default_factory=list)

    def total_employee_costs(self) -> float:
        return sum(employee.total_cost() for employee in self.employees)

    def total_office_costs(self) -> float:
        return sum(cost.amount for cost in self.office_costs)

    def total_additional_costs(self) -> float:
        return sum(cost.amount for cost in self.additional_costs)

    def total_leasing_costs(self) -> float:
        return sum(cost.deductible_amount() for cost in self.leasing_costs)

    def total_board_costs(self) -> float:
        return sum(comp.annual_cost() / 12 for comp in self.board_compensations)

    def monthly_total(self) -> float:
        """Return the aggregated monthly cost of running the company."""
        return (
            self.total_employee_costs()
            + self.total_office_costs()
            + self.total_additional_costs()
            + self.total_leasing_costs()
            + self.total_board_costs()
        )

    def total_headcount(self) -> int:
        return len(self.employees)

    def available_hours_per_month(self, hours_per_week: float = 80.0) -> float:
        """Calculate available hours based on headcount and weekly availability."""
        weeks_per_month = 52 / 12
        return self.total_headcount() * hours_per_week * weeks_per_month

    def hourly_rate(self, hours_per_week: float = 80.0) -> float:
        """Return the base hourly rate for an employee."""
        total_hours = self.available_hours_per_month(hours_per_week)
        if total_hours == 0:
            raise ValueError("Cannot compute hourly rate without employees.")
        return self.monthly_total() / total_hours
