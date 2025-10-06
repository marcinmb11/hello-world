"""A simple Flask UI for the finance and project management toolkit."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, flash, redirect, render_template, request, url_for

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
    OfferBreakdown,
    OfferCalculator,
    OfficeCost,
    ProjectBudget,
    SocialBudget,
)

app = Flask(__name__)
app.secret_key = "finance-app-secret"

# Global state kept in memory for demo purposes.
company_costs = CompanyCosts()
project_budget = ProjectBudget(project_name="Nowy projekt")
invoice_generator: Optional[InvoiceGenerator] = None
last_invoice = None
hours_per_week_setting = 80.0
last_offer: Optional[OfferBreakdown] = None
last_offer_chart: Optional[str] = None


def _parse_float(value: str) -> float:
    value = value.replace(",", ".")
    return float(value)


def _parse_components(raw: str) -> Dict[str, float]:
    components: Dict[str, float] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError("Niepoprawny format składników wynagrodzenia.")
        key, amount = line.split(":", 1)
        components[key.strip()] = _parse_float(amount.strip())
    return components


def _get_offer_calculator() -> OfferCalculator:
    return OfferCalculator(company_costs)


@app.route("/")
def index():
    calculator = _get_offer_calculator()
    try:
        hourly_rate = calculator.base_hourly_rate(hours_per_week=hours_per_week_setting)
    except ValueError:
        hourly_rate = None

    summary = {
        "employee_costs": company_costs.total_employee_costs(),
        "office_costs": company_costs.total_office_costs(),
        "additional_costs": company_costs.total_additional_costs(),
        "leasing_costs": company_costs.total_leasing_costs(),
        "board_costs": company_costs.total_board_costs(),
        "monthly_total": company_costs.monthly_total(),
        "available_hours": company_costs.available_hours_per_month(hours_per_week=hours_per_week_setting)
        if company_costs.total_headcount()
        else 0.0,
        "hourly_rate": hourly_rate,
    }

    invoice_data = {
        "issuer": invoice_generator.issuer if invoice_generator else None,
        "invoice": last_invoice,
    }

    return render_template(
        "index.html",
        company_summary=summary,
        company_data=company_costs,
        hours_per_week=hours_per_week_setting,
        offer=last_offer,
        offer_chart=last_offer_chart,
        project=project_budget,
        invoice_data=invoice_data,
    )


@app.post("/add_employee")
def add_employee():
    try:
        components = _parse_components(request.form.get("components", ""))
        employee = EmployeeCompensation(
            name=request.form["name"],
            net_salary=_parse_float(request.form["net_salary"]),
            gross_salary=_parse_float(request.form["gross_salary"]),
            salary_components=components,
        )
        company_costs.employees.append(employee)
        flash("Dodano pracownika.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać pracownika.", "error")
    return redirect(url_for("index"))


@app.post("/add_office_cost")
def add_office_cost():
    try:
        office_cost = OfficeCost(
            description=request.form["description"],
            category=request.form["category"],
            amount=_parse_float(request.form["amount"]),
        )
        company_costs.office_costs.append(office_cost)
        flash("Dodano koszt biura.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać kosztu biura.", "error")
    return redirect(url_for("index"))


@app.post("/add_additional_cost")
def add_additional_cost():
    try:
        cost = AdditionalCost(
            description=request.form["description"],
            amount=_parse_float(request.form["amount"]),
        )
        company_costs.additional_costs.append(cost)
        flash("Dodano koszt dodatkowy.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać kosztu dodatkowego.", "error")
    return redirect(url_for("index"))


@app.post("/add_leasing_cost")
def add_leasing_cost():
    try:
        cost = LeasingCost(
            description=request.form["description"],
            amount=_parse_float(request.form["amount"]),
            deductible_ratio=_parse_float(request.form["deductible_ratio"]),
        )
        company_costs.leasing_costs.append(cost)
        flash("Dodano koszt leasingu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać leasingu.", "error")
    return redirect(url_for("index"))


@app.post("/add_board_member")
def add_board_member():
    try:
        member = BoardMemberCompensation(
            name=request.form["name"],
            gross_salary=_parse_float(request.form["gross_salary"]),
            social_security=_parse_float(request.form["social_security"]),
            health_insurance=_parse_float(request.form["health_insurance"]),
        )
        company_costs.board_compensations.append(member)
        flash("Dodano członka zarządu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać członka zarządu.", "error")
    return redirect(url_for("index"))


@app.post("/calculate_offer")
def calculate_offer():
    global last_offer, last_offer_chart, hours_per_week_setting  # noqa: PLW0603
    try:
        hours = _parse_float(request.form["hours"])
        material_cost = _parse_float(request.form["material_cost"])
        material_margin_pct = _parse_float(request.form.get("material_margin_pct", "0"))
        hourly_margin_pct = _parse_float(request.form.get("hourly_margin_pct", "0"))
        double_time_hours = _parse_float(request.form.get("double_time_hours", "0"))
        travel_cost = _parse_float(request.form.get("travel_cost", "0"))
        hotel_cost = _parse_float(request.form.get("hotel_cost", "0"))
        per_diem_cost = _parse_float(request.form.get("per_diem_cost", "0"))
        hours_per_week_setting = _parse_float(request.form.get("hours_per_week", str(hours_per_week_setting)))

        calculator = _get_offer_calculator()
        offer = calculator.calculate_offer(
            hours=hours,
            material_cost=material_cost,
            material_margin_pct=material_margin_pct,
            hourly_margin_pct=hourly_margin_pct,
            double_time_hours=double_time_hours,
            travel_cost=travel_cost,
            hotel_cost=hotel_cost,
            per_diem_cost=per_diem_cost,
            hours_per_week=hours_per_week_setting,
        )
        last_offer = offer

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        chart_relative = os.path.join("generated", f"offer_{timestamp}.png")
        chart_path = os.path.join("static", chart_relative)
        os.makedirs(os.path.dirname(chart_path), exist_ok=True)
        _get_offer_calculator().plot_offer_structure(offer, output_path=chart_path)
        last_offer_chart = chart_relative
        flash("Oferta została wyliczona.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        last_offer = None
        last_offer_chart = None
        flash(str(exc) or "Nie udało się wyliczyć oferty.", "error")
    return redirect(url_for("index"))


@app.post("/update_project_name")
def update_project_name():
    project_budget.project_name = request.form["project_name"]
    flash("Zaktualizowano nazwę projektu.", "success")
    return redirect(url_for("index"))


@app.post("/add_employee_assignment")
def add_employee_assignment():
    try:
        assignment = EmployeeAssignment(
            employee_name=request.form["employee_name"],
            hourly_rate=_parse_float(request.form["hourly_rate"]),
            planned_hours=_parse_float(request.form["planned_hours"]),
        )
        project_budget.employee_assignments.append(assignment)
        flash("Dodano pracownika do projektu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać pracownika do projektu.", "error")
    return redirect(url_for("index"))


@app.post("/set_social_budget")
def set_social_budget():
    try:
        social_budget = SocialBudget(
            hotel_budget=_parse_float(request.form["hotel_budget"]),
            per_diem_budget=_parse_float(request.form["per_diem_budget"]),
            container_rental_budget=_parse_float(request.form["container_rental_budget"]),
        )
        project_budget.social_budget = social_budget
        flash("Zapisano budżet socjalny.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się zapisać budżetu socjalnego.", "error")
    return redirect(url_for("index"))


@app.post("/add_material_item")
def add_material_item():
    try:
        if project_budget.material_budget is None:
            project_budget.material_budget = MaterialBudget()
        project_budget.material_budget.items[request.form["item_name"]] = _parse_float(request.form["item_cost"])
        flash("Dodano materiał do budżetu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać materiału.", "error")
    return redirect(url_for("index"))


@app.post("/add_acceptance_protocol")
def add_acceptance_protocol():
    try:
        protocol = AcceptanceProtocol(
            protocol_number=request.form["protocol_number"],
            project_name=project_budget.project_name,
            accepted_scope=request.form["accepted_scope"],
            date_signed=datetime.strptime(request.form["date_signed"], "%Y-%m-%d").date(),
            value=_parse_float(request.form["value"]),
            partial=request.form.get("partial", "true") == "true",
        )
        project_budget.acceptance_protocols.append(protocol)
        flash("Dodano protokół odbioru.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się dodać protokołu.", "error")
    return redirect(url_for("index"))


@app.post("/set_invoice_issuer")
def set_invoice_issuer():
    global invoice_generator  # noqa: PLW0603
    try:
        issuer = InvoiceIssuer(
            name=request.form["name"],
            address=request.form["address"],
            nip=request.form["nip"],
            bank_account=request.form["bank_account"],
        )
        invoice_generator = InvoiceGenerator(issuer)
        flash("Zapisano dane wystawcy.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się zapisać wystawcy.", "error")
    return redirect(url_for("index"))


@app.post("/generate_invoice")
def generate_invoice():
    global last_invoice  # noqa: PLW0603
    if invoice_generator is None:
        flash("Uzupełnij dane wystawcy faktury.", "error")
        return redirect(url_for("index"))

    try:
        protocol_number = request.form["protocol_number"]
        protocol = next(
            (proto for proto in project_budget.acceptance_protocols if proto.protocol_number == protocol_number),
            None,
        )
        if protocol is None:
            raise ValueError("Nie znaleziono wybranego protokołu.")

        buyer = InvoiceBuyer(
            name=request.form["buyer_name"],
            address=request.form["buyer_address"],
            nip=request.form["buyer_nip"],
        )
        invoice = invoice_generator.from_acceptance(
            protocol=protocol,
            buyer=buyer,
            invoice_number=request.form["invoice_number"],
            payment_terms=request.form.get("payment_terms", "14 dni"),
            tax_rate=_parse_float(request.form.get("tax_rate", "23")),
        )
        last_invoice = invoice
        flash("Wygenerowano fakturę.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        flash(str(exc) or "Nie udało się wygenerować faktury.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
