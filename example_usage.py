"""Demonstrates populating the database and using the finance toolkit."""

from __future__ import annotations

import os
from datetime import date

os.environ.setdefault("FINANCE_APP_DATABASE_URL", "sqlite:///example_usage.db")

from finance_app.offer_module import OfferCalculator
from finance_app.invoicing import InvoiceBuyer, InvoiceGenerator
from finance_app.repository import (
    invoice_to_payload,
    load_company_costs,
    offer_payload_from_breakdown,
    project_to_budget,
    issuer_from_model,
)
from finance_app.database import (
    AdditionalCost as AdditionalCostModel,
    BoardMember as BoardMemberModel,
    Employee as EmployeeModel,
    InvoiceIssuerModel,
    InvoiceModel,
    LeasingCost as LeasingCostModel,
    OfferModel,
    OfficeCost as OfficeCostModel,
    Project as ProjectModel,
    ProjectAcceptanceProtocol as ProtocolModel,
    ProjectEmployeeAssignment as AssignmentModel,
    ProjectMaterialItem as MaterialItemModel,
    ProjectSocialBudget as SocialBudgetModel,
    SessionLocal,
    init_db,
)


def reset_database() -> None:
    session = SessionLocal()
    try:
        for model in (
            OfferModel,
            InvoiceModel,
            ProtocolModel,
            MaterialItemModel,
            AssignmentModel,
            SocialBudgetModel,
            ProjectModel,
            EmployeeModel,
            OfficeCostModel,
            AdditionalCostModel,
            LeasingCostModel,
            BoardMemberModel,
            InvoiceIssuerModel,
        ):
            session.query(model).delete()
        session.commit()
    finally:
        session.close()


def populate_company_data() -> None:
    session = SessionLocal()
    try:
        session.add_all(
            [
                EmployeeModel(
                    name="Jan Kowalski",
                    net_salary=6000,
                    gross_salary=9000,
                    salary_components={"wynagrodzenie": 7500, "premia": 1500},
                ),
                EmployeeModel(
                    name="Anna Nowak",
                    net_salary=5500,
                    gross_salary=8500,
                    salary_components={"wynagrodzenie": 7000, "premia": 1500},
                ),
            ]
        )
        session.add_all(
            [
                OfficeCostModel(description="Czynsz", category="czynsz", amount=8000),
                OfficeCostModel(description="Media", category="media", amount=2000),
                OfficeCostModel(description="Artykuły biurowe", category="biuro", amount=500),
            ]
        )
        session.add_all(
            [
                AdditionalCostModel(description="Ubezpieczenie firmy", amount=1200),
            ]
        )
        session.add_all(
            [
                LeasingCostModel(description="Leasing samochodu A", amount=2500, deductible_ratio=0.5),
                LeasingCostModel(description="Leasing samochodu B", amount=2200, deductible_ratio=1.0),
            ]
        )
        session.add(
            BoardMemberModel(
                name="Prezes",
                gross_salary=15000,
                social_security=1800,
                health_insurance=1200,
            )
        )
        session.commit()
    finally:
        session.close()


def create_project() -> ProjectModel:
    session = SessionLocal()
    try:
        project = ProjectModel(name="Instalacja elektryczna")
        session.add(project)
        session.commit()

        assignments = [
            AssignmentModel(project_id=project.id, employee_name="Jan Kowalski", hourly_rate=120, planned_hours=80),
            AssignmentModel(project_id=project.id, employee_name="Anna Nowak", hourly_rate=115, planned_hours=90),
        ]
        session.add_all(assignments)

        social_budget = SocialBudgetModel(
            project_id=project.id,
            hotel_budget=5000,
            per_diem_budget=2000,
            container_rental_budget=1000,
        )
        session.add(social_budget)

        materials = [
            MaterialItemModel(project_id=project.id, item_name="Przewody", item_cost=10000),
            MaterialItemModel(project_id=project.id, item_name="Rozdzielnice", item_cost=5000),
        ]
        session.add_all(materials)

        protocol = ProtocolModel(
            project_id=project.id,
            protocol_number="P/01/2024",
            accepted_scope="Zakończony etap I",
            date_signed=date.today(),
            value=25000,
            partial=True,
        )
        session.add(protocol)

        session.commit()
        return project
    finally:
        session.close()


def demonstrate_offer(project: ProjectModel) -> None:
    session = SessionLocal()
    try:
        company_costs = load_company_costs(session)
        calculator = OfferCalculator(company_costs)
        offer = calculator.calculate_offer(
            hours=160,
            material_cost=15000,
            material_margin_pct=15,
            hourly_margin_pct=10,
            double_time_hours=16,
            travel_cost=1500,
            hotel_cost=2500,
            per_diem_cost=1200,
            hours_per_week=80,
        )
        offer_model = OfferModel(
            project_id=project.id,
            hours=160,
            material_cost=15000,
            material_margin_pct=15,
            hourly_margin_pct=10,
            double_time_hours=16,
            travel_cost=1500,
            hotel_cost=2500,
            per_diem_cost=1200,
            hours_per_week=80,
            result_payload=offer_payload_from_breakdown(offer),
        )
        session.add(offer_model)
        session.commit()
        print(
            "Oferta zapisana w bazie:",
            f"koszt całkowity {offer.total_cost:.2f} PLN, zysk {offer.profit:.2f} PLN",
        )
    finally:
        session.close()


def demonstrate_invoice(project: ProjectModel) -> None:
    session = SessionLocal()
    try:
        issuer = session.query(InvoiceIssuerModel).first()
        if issuer is None:
            issuer = InvoiceIssuerModel(
                name="ABC Sp. z o.o.",
                address="ul. Przykładowa 1, 00-000 Warszawa",
                nip="1234567890",
                bank_account="12 3456 7890 1234 5678 9012 3456",
            )
            session.add(issuer)
            session.commit()

        invoice_generator = InvoiceGenerator(issuer_from_model(issuer))
        project_db = session.get(ProjectModel, project.id)
        if project_db is None:
            raise RuntimeError("Projekt nie został znaleziony w bazie danych")
        buyer = InvoiceBuyer(
            name="Inwestor Sp. z o.o.",
            address="ul. Inna 2, 00-000 Warszawa",
            nip="0987654321",
        )
        invoice = invoice_generator.from_acceptance(
            protocol=project_to_budget(project_db).acceptance_protocols[0],
            buyer=buyer,
            invoice_number="1/2024",
        )
        invoice_model = InvoiceModel(
            project_id=project.id,
            invoice_number=invoice.number,
            buyer_name=buyer.name,
            payload=invoice_to_payload(invoice),
        )
        session.add(invoice_model)
        session.commit()
        print("Faktura brutto:", invoice.total_gross())
    finally:
        session.close()


def main() -> None:
    init_db()
    reset_database()
    populate_company_data()
    project = create_project()
    demonstrate_offer(project)
    demonstrate_invoice(project)

    session = SessionLocal()
    try:
        project = session.get(ProjectModel, project.id)
        if project:
            budget = project_to_budget(project)
            print("Budżet całkowity projektu:", budget.total_budget())
    finally:
        session.close()


if __name__ == "__main__":
    main()
