"""Repository helpers bridging SQLAlchemy models and domain dataclasses."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, Optional

from sqlalchemy.orm import Session

from .company_costs import (
    AdditionalCost as AdditionalCostData,
    BoardMemberCompensation,
    CompanyCosts,
    EmployeeCompensation,
    LeasingCost as LeasingCostData,
    OfficeCost as OfficeCostData,
)
from .database import (
    AdditionalCost,
    BoardMember,
    Employee,
    InvoiceIssuerModel,
    InvoiceModel,
    OfferModel,
    OfficeCost,
    LeasingCost,
    Project,
    ProjectAcceptanceProtocol,
    ProjectEmployeeAssignment,
    ProjectMaterialItem,
    ProjectSocialBudget,
)
from .invoicing import Invoice, InvoiceBuyer, InvoiceIssuer, InvoiceLine
from .offer_module import OfferBreakdown
from .project_module import (
    AcceptanceProtocol,
    EmployeeAssignment,
    MaterialBudget,
    ProjectBudget,
    SocialBudget,
)


def _employee_from_model(model: Employee) -> EmployeeCompensation:
    return EmployeeCompensation(
        name=model.name,
        net_salary=model.net_salary,
        gross_salary=model.gross_salary,
        salary_components=model.salary_components or {},
    )


def _office_cost_from_model(model: OfficeCost) -> OfficeCostData:
    return OfficeCostData(description=model.description, amount=model.amount, category=model.category)


def _additional_cost_from_model(model: AdditionalCost) -> AdditionalCostData:
    return AdditionalCostData(description=model.description, amount=model.amount)


def _leasing_cost_from_model(model: LeasingCost) -> LeasingCostData:
    return LeasingCostData(description=model.description, amount=model.amount, deductible_ratio=model.deductible_ratio)


def _board_member_from_model(model: BoardMember) -> BoardMemberCompensation:
    return BoardMemberCompensation(
        name=model.name,
        gross_salary=model.gross_salary,
        social_security=model.social_security,
        health_insurance=model.health_insurance,
    )


def load_company_costs(session: Session) -> CompanyCosts:
    """Build a :class:`CompanyCosts` object from persisted data."""

    employees = [_employee_from_model(model) for model in session.query(Employee).all()]
    office_costs = [_office_cost_from_model(model) for model in session.query(OfficeCost).all()]
    additional_costs = [_additional_cost_from_model(model) for model in session.query(AdditionalCost).all()]
    leasing_costs = [_leasing_cost_from_model(model) for model in session.query(LeasingCost).all()]
    board_compensations = [_board_member_from_model(model) for model in session.query(BoardMember).all()]
    return CompanyCosts(
        employees=employees,
        office_costs=office_costs,
        additional_costs=additional_costs,
        leasing_costs=leasing_costs,
        board_compensations=board_compensations,
    )


def _assignment_from_model(model: ProjectEmployeeAssignment) -> EmployeeAssignment:
    return EmployeeAssignment(
        employee_name=model.employee_name,
        hourly_rate=model.hourly_rate,
        planned_hours=model.planned_hours,
    )


def _social_budget_from_model(model: Optional[ProjectSocialBudget]) -> Optional[SocialBudget]:
    if model is None:
        return None
    return SocialBudget(
        hotel_budget=model.hotel_budget,
        per_diem_budget=model.per_diem_budget,
        container_rental_budget=model.container_rental_budget,
    )


def _material_budget_from_models(models: Iterable[ProjectMaterialItem]) -> Optional[MaterialBudget]:
    items = {item.item_name: item.item_cost for item in models}
    if not items:
        return None
    return MaterialBudget(items=items)


def _acceptance_from_model(model: ProjectAcceptanceProtocol, project_name: str) -> AcceptanceProtocol:
    return AcceptanceProtocol(
        protocol_number=model.protocol_number,
        project_name=project_name,
        accepted_scope=model.accepted_scope,
        date_signed=model.date_signed,
        value=model.value,
        partial=model.partial,
    )


def project_to_budget(project: Project) -> ProjectBudget:
    assignments = [_assignment_from_model(model) for model in project.employee_assignments]
    social_budget = _social_budget_from_model(project.social_budget)
    material_budget = _material_budget_from_models(project.material_items)
    acceptance_protocols = [
        _acceptance_from_model(model, project.name) for model in project.acceptance_protocols
    ]
    return ProjectBudget(
        project_name=project.name,
        employee_assignments=assignments,
        social_budget=social_budget,
        material_budget=material_budget,
        acceptance_protocols=acceptance_protocols,
    )


def offer_payload_from_breakdown(breakdown: OfferBreakdown) -> Dict[str, float]:
    return breakdown.to_dict()


def offer_breakdown_from_model(model: OfferModel) -> OfferBreakdown:
    return OfferBreakdown(**model.result_payload)


def invoice_to_payload(invoice: Invoice) -> Dict[str, Any]:
    return {
        "number": invoice.number,
        "issue_date": invoice.issue_date.isoformat(),
        "sale_date": invoice.sale_date.isoformat(),
        "issuer": {
            "name": invoice.issuer.name,
            "address": invoice.issuer.address,
            "nip": invoice.issuer.nip,
            "bank_account": invoice.issuer.bank_account,
        },
        "buyer": {
            "name": invoice.buyer.name,
            "address": invoice.buyer.address,
            "nip": invoice.buyer.nip,
        },
        "payment_terms": invoice.payment_terms,
        "lines": [
            {
                "description": line.description,
                "net_amount": line.net_amount,
                "tax_rate": line.tax_rate,
            }
            for line in invoice.lines
        ],
    }


def invoice_from_payload(payload: Dict[str, Any]) -> Invoice:
    issuer = InvoiceIssuer(**payload["issuer"])
    buyer = InvoiceBuyer(**payload["buyer"])
    lines = [InvoiceLine(**line_data) for line_data in payload.get("lines", [])]
    return Invoice(
        number=payload["number"],
        issue_date=date.fromisoformat(payload["issue_date"]),
        sale_date=date.fromisoformat(payload["sale_date"]),
        issuer=issuer,
        buyer=buyer,
        payment_terms=payload["payment_terms"],
        lines=lines,
    )


def issuer_from_model(model: Optional[InvoiceIssuerModel]) -> Optional[InvoiceIssuer]:
    if model is None:
        return None
    return InvoiceIssuer(
        name=model.name,
        address=model.address,
        nip=model.nip,
        bank_account=model.bank_account,
    )


def invoice_from_model(model: Optional[InvoiceModel]) -> Optional[Invoice]:
    if model is None:
        return None
    return invoice_from_payload(model.payload)


__all__ = [
    "load_company_costs",
    "project_to_budget",
    "offer_payload_from_breakdown",
    "offer_breakdown_from_model",
    "invoice_to_payload",
    "invoice_from_model",
    "issuer_from_model",
]
