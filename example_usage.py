"""Example demonstrating the finance management modules."""
from datetime import date

from finance_app import (
    AcceptanceProtocol,
    AdditionalCost,
    BoardMemberCompensation,
    CompanyCosts,
    EmployeeAssignment,
    EmployeeCompensation,
    InvoiceBuyer,
    InvoiceGenerator,
    InvoiceIssuer,
    LeasingCost,
    MaterialBudget,
    OfferCalculator,
    OfficeCost,
    ProjectBudget,
    SocialBudget,
)


def build_company_costs() -> CompanyCosts:
    company_costs = CompanyCosts(
        employees=[
            EmployeeCompensation(
                name="Jan Kowalski",
                net_salary=6000,
                gross_salary=9000,
                salary_components={"wynagrodzenie zasadnicze": 7500, "premia": 1500},
            ),
            EmployeeCompensation(
                name="Anna Nowak",
                net_salary=5500,
                gross_salary=8500,
                salary_components={"wynagrodzenie zasadnicze": 7000, "premia": 1500},
            ),
        ],
        office_costs=[
            OfficeCost(description="Czynsz", amount=8000, category="czynsz"),
            OfficeCost(description="Media", amount=2000, category="media"),
            OfficeCost(description="Artykuły biurowe", amount=500, category="biuro"),
        ],
        additional_costs=[
            AdditionalCost(description="Ubezpieczenie firmy", amount=1200),
        ],
        leasing_costs=[
            LeasingCost(description="Leasing samochodu A", amount=2500, deductible_ratio=0.5),
            LeasingCost(description="Leasing samochodu B", amount=2200, deductible_ratio=1.0),
        ],
        board_compensations=[
            BoardMemberCompensation(
                name="Prezes",
                gross_salary=15000,
                social_security=1800,
                health_insurance=1200,
            ),
        ],
    )
    return company_costs


def build_offer(company_costs: CompanyCosts) -> None:
    calculator = OfferCalculator(company_costs)
    offer = calculator.calculate_offer(
        hours=160,
        material_cost=40_000,
        material_margin_pct=15,
        hourly_margin_pct=10,
        double_time_hours=16,
        travel_cost=1500,
        hotel_cost=2500,
        per_diem_cost=1200,
    )
    chart_path = calculator.plot_offer_structure(offer)
    print("Oferta:", offer.to_dict())
    print("Wykres zapisany w:", chart_path)


def build_project(company_costs: CompanyCosts) -> ProjectBudget:
    calculator = OfferCalculator(company_costs)
    hourly_rate = calculator.base_hourly_rate()
    project = ProjectBudget(
        project_name="Instalacja elektryczna",
        employee_assignments=[
            EmployeeAssignment("Jan Kowalski", hourly_rate, 80),
            EmployeeAssignment("Anna Nowak", hourly_rate, 90),
        ],
        social_budget=SocialBudget(hotel_budget=5000, per_diem_budget=2000, container_rental_budget=1000),
        material_budget=MaterialBudget(items={"Przewody": 10000, "Rozdzielnice": 5000}),
    )
    protocol = AcceptanceProtocol(
        protocol_number="P/01/2024",
        project_name=project.project_name,
        accepted_scope="Zakończony etap I",
        date_signed=date.today(),
        value=project.total_budget(),
        partial=True,
    )
    project.register_acceptance(protocol)
    return project


def build_invoice(project: ProjectBudget) -> None:
    issuer = InvoiceIssuer(
        name="ABC Sp. z o.o.",
        address="ul. Przykładowa 1, 00-000 Warszawa",
        nip="1234567890",
        bank_account="12 3456 7890 1234 5678 9012 3456",
    )
    buyer = InvoiceBuyer(
        name="Inwestor Sp. z o.o.",
        address="ul. Inna 2, 00-000 Warszawa",
        nip="0987654321",
    )
    generator = InvoiceGenerator(issuer)
    invoice = generator.from_acceptance(
        protocol=project.acceptance_protocols[0],
        buyer=buyer,
        invoice_number="1/2024",
    )
    print("Faktura netto:", invoice.total_net())
    print("Faktura VAT:", invoice.total_tax())
    print("Faktura brutto:", invoice.total_gross())


if __name__ == "__main__":
    company_costs = build_company_costs()
    build_offer(company_costs)
    project = build_project(company_costs)
    build_invoice(project)
