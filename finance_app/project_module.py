"""Project planning structures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class EmployeeAssignment:
    """Assign an employee and planned hours to a project."""

    employee_name: str
    hourly_rate: float
    planned_hours: float

    def planned_cost(self) -> float:
        return self.hourly_rate * self.planned_hours


@dataclass
class SocialBudget:
    """Covers hotel, daily allowance and social container rental."""

    hotel_budget: float
    per_diem_budget: float
    container_rental_budget: float

    def total(self) -> float:
        return self.hotel_budget + self.per_diem_budget + self.container_rental_budget


@dataclass
class MaterialBudget:
    """Budget for materials required for project execution."""

    items: Dict[str, float] = field(default_factory=dict)

    def total(self) -> float:
        return sum(self.items.values())


@dataclass
class AcceptanceProtocol:
    """Represents acceptance of completed works."""

    protocol_number: str
    project_name: str
    accepted_scope: str
    date_signed: date
    value: float
    partial: bool = False


@dataclass
class ProjectBudget:
    """Aggregates budgets and acceptance protocols."""

    project_name: str
    employee_assignments: List[EmployeeAssignment] = field(default_factory=list)
    social_budget: Optional[SocialBudget] = None
    material_budget: Optional[MaterialBudget] = None
    acceptance_protocols: List[AcceptanceProtocol] = field(default_factory=list)

    def total_employee_budget(self) -> float:
        return sum(assignment.planned_cost() for assignment in self.employee_assignments)

    def total_social_budget(self) -> float:
        return self.social_budget.total() if self.social_budget else 0.0

    def total_material_budget(self) -> float:
        return self.material_budget.total() if self.material_budget else 0.0

    def total_budget(self) -> float:
        return (
            self.total_employee_budget()
            + self.total_social_budget()
            + self.total_material_budget()
        )

    def register_acceptance(self, protocol: AcceptanceProtocol) -> None:
        self.acceptance_protocols.append(protocol)

    def accepted_value(self) -> float:
        return sum(protocol.value for protocol in self.acceptance_protocols)
