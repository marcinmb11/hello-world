"""A Flask UI for the finance and project management toolkit backed by a database."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, flash, g, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from finance_app import AcceptanceProtocol, OfferBreakdown, OfferCalculator, ProjectBudget
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
from finance_app.invoicing import InvoiceBuyer, InvoiceGenerator
from finance_app.repository import (
    invoice_from_model,
    invoice_to_payload,
    issuer_from_model,
    load_company_costs,
    offer_breakdown_from_model,
    offer_payload_from_breakdown,
    project_to_budget,
)


app = Flask(__name__)
app.secret_key = "finance-app-secret"

init_db()


def _parse_float(value: str) -> float:
    value = value.replace(",", ".")
    return float(value)


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value in (None, ""):
        return None
    return int(value)


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


def get_db() -> Session:
    if "db_session" not in g:
        g.db_session = SessionLocal()  # type: ignore[attr-defined]
    return g.db_session


@app.teardown_appcontext
def close_db(_: Optional[BaseException]) -> None:
    session: Optional[Session] = g.pop("db_session", None)
    if session is not None:
        session.close()


def _redirect_with_project(project_id: Optional[int]):
    if project_id:
        return redirect(url_for("index", project_id=project_id))
    return redirect(url_for("index"))


def _selected_project(session: Session, project_id: Optional[int]) -> Optional[ProjectModel]:
    if project_id:
        project = session.get(ProjectModel, project_id)
        if project is not None:
            return project
        flash("Wybrany projekt nie istnieje.", "error")
    return session.query(ProjectModel).order_by(ProjectModel.name).first()


def _latest_offer(session: Session, project_id: Optional[int]) -> Optional[OfferModel]:
    query = session.query(OfferModel).order_by(OfferModel.created_at.desc())
    if project_id:
        query = query.filter(OfferModel.project_id == project_id)
    return query.first()


def _latest_invoice(session: Session, project_id: Optional[int]) -> Optional[InvoiceModel]:
    query = session.query(InvoiceModel).order_by(InvoiceModel.created_at.desc())
    if project_id:
        query = query.filter(InvoiceModel.project_id == project_id)
    return query.first()


def _hours_per_week_from_offer(offer_model: Optional[OfferModel]) -> float:
    return offer_model.hours_per_week if offer_model else 80.0


@app.route("/")
def index():
    session = get_db()
    requested_project_id = _parse_int(request.args.get("project_id"))
    selected_project = _selected_project(session, requested_project_id)
    project_id = selected_project.id if selected_project else None

    company_costs = load_company_costs(session)
    last_offer_model = _latest_offer(session, project_id)
    hours_per_week_setting = _hours_per_week_from_offer(last_offer_model)
    calculator = OfferCalculator(company_costs)

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

    last_offer: Optional[OfferBreakdown] = (
        offer_breakdown_from_model(last_offer_model) if last_offer_model else None
    )
    last_offer_chart = last_offer_model.chart_path if last_offer_model else None

    invoice_issuer_model = session.query(InvoiceIssuerModel).first()
    invoice_generator = (
        InvoiceGenerator(issuer_from_model(invoice_issuer_model))
        if invoice_issuer_model
        else None
    )

    last_invoice = invoice_from_model(_latest_invoice(session, project_id))

    projects = session.query(ProjectModel).order_by(ProjectModel.name).all()
    project_budget: Optional[ProjectBudget] = (
        project_to_budget(selected_project) if selected_project else None
    )

    invoice_data = {
        "issuer": invoice_generator.issuer if invoice_generator else issuer_from_model(invoice_issuer_model),
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
        projects=projects,
        selected_project_id=project_id,
        invoice_data=invoice_data,
    )


@app.post("/add_employee")
def add_employee():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        components = _parse_components(request.form.get("components", ""))
        employee = EmployeeModel(
            name=request.form["name"],
            net_salary=_parse_float(request.form["net_salary"]),
            gross_salary=_parse_float(request.form["gross_salary"]),
            salary_components=components,
        )
        session.add(employee)
        session.commit()
        flash("Dodano pracownika.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać pracownika.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_office_cost")
def add_office_cost():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        office_cost = OfficeCostModel(
            description=request.form["description"],
            category=request.form["category"],
            amount=_parse_float(request.form["amount"]),
        )
        session.add(office_cost)
        session.commit()
        flash("Dodano koszt biura.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać kosztu biura.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_additional_cost")
def add_additional_cost():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        cost = AdditionalCostModel(
            description=request.form["description"],
            amount=_parse_float(request.form["amount"]),
        )
        session.add(cost)
        session.commit()
        flash("Dodano koszt dodatkowy.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać kosztu dodatkowego.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_leasing_cost")
def add_leasing_cost():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        cost = LeasingCostModel(
            description=request.form["description"],
            amount=_parse_float(request.form["amount"]),
            deductible_ratio=_parse_float(request.form["deductible_ratio"]),
        )
        session.add(cost)
        session.commit()
        flash("Dodano koszt leasingu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać leasingu.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_board_member")
def add_board_member():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        member = BoardMemberModel(
            name=request.form["name"],
            gross_salary=_parse_float(request.form["gross_salary"]),
            social_security=_parse_float(request.form["social_security"]),
            health_insurance=_parse_float(request.form["health_insurance"]),
        )
        session.add(member)
        session.commit()
        flash("Dodano członka zarządu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać członka zarządu.", "error")
    return _redirect_with_project(project_id)


@app.post("/create_project")
def create_project():
    session = get_db()
    project = ProjectModel(name=request.form["name"])
    session.add(project)
    try:
        session.commit()
        flash("Utworzono projekt.", "success")
        return _redirect_with_project(project.id)
    except IntegrityError:
        session.rollback()
        flash("Projekt o tej nazwie już istnieje.", "error")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się utworzyć projektu.", "error")
    return redirect(url_for("index"))


@app.post("/update_project_name")
def update_project_name():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    if not project_id:
        flash("Wybierz projekt, aby zaktualizować nazwę.", "error")
        return redirect(url_for("index"))
    project = session.get(ProjectModel, project_id)
    if project is None:
        flash("Wybrany projekt nie istnieje.", "error")
        return redirect(url_for("index"))
    project.name = request.form["project_name"]
    session.commit()
    flash("Zaktualizowano nazwę projektu.", "success")
    return _redirect_with_project(project_id)


@app.post("/add_employee_assignment")
def add_employee_assignment():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    project = session.get(ProjectModel, project_id) if project_id else None
    if project is None:
        flash("Wybierz projekt, aby dodać pracownika.", "error")
        return redirect(url_for("index"))
    try:
        assignment = AssignmentModel(
            project_id=project.id,
            employee_name=request.form["employee_name"],
            hourly_rate=_parse_float(request.form["hourly_rate"]),
            planned_hours=_parse_float(request.form["planned_hours"]),
        )
        session.add(assignment)
        session.commit()
        flash("Dodano pracownika do projektu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać pracownika do projektu.", "error")
    return _redirect_with_project(project_id)


@app.post("/set_social_budget")
def set_social_budget():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    project = session.get(ProjectModel, project_id) if project_id else None
    if project is None:
        flash("Wybierz projekt, aby zapisać budżet socjalny.", "error")
        return redirect(url_for("index"))
    try:
        social_budget = project.social_budget or SocialBudgetModel(project_id=project.id)
        social_budget.hotel_budget = _parse_float(request.form["hotel_budget"])
        social_budget.per_diem_budget = _parse_float(request.form["per_diem_budget"])
        social_budget.container_rental_budget = _parse_float(request.form["container_rental_budget"])
        session.add(social_budget)
        session.commit()
        flash("Zapisano budżet socjalny.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się zapisać budżetu socjalnego.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_material_item")
def add_material_item():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    project = session.get(ProjectModel, project_id) if project_id else None
    if project is None:
        flash("Wybierz projekt, aby dodać materiał.", "error")
        return redirect(url_for("index"))
    try:
        item = MaterialItemModel(
            project_id=project.id,
            item_name=request.form["item_name"],
            item_cost=_parse_float(request.form["item_cost"]),
        )
        session.add(item)
        session.commit()
        flash("Dodano materiał do budżetu.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać materiału.", "error")
    return _redirect_with_project(project_id)


@app.post("/add_acceptance_protocol")
def add_acceptance_protocol():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    project = session.get(ProjectModel, project_id) if project_id else None
    if project is None:
        flash("Wybierz projekt, aby dodać protokół.", "error")
        return redirect(url_for("index"))
    try:
        protocol = ProtocolModel(
            project_id=project.id,
            protocol_number=request.form["protocol_number"],
            accepted_scope=request.form["accepted_scope"],
            date_signed=datetime.strptime(request.form["date_signed"], "%Y-%m-%d").date(),
            value=_parse_float(request.form["value"]),
            partial=request.form.get("partial", "true") == "true",
        )
        session.add(protocol)
        session.commit()
        flash("Dodano protokół odbioru.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się dodać protokołu.", "error")
    return _redirect_with_project(project_id)


@app.post("/calculate_offer")
def calculate_offer():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        hours = _parse_float(request.form["hours"])
        material_cost = _parse_float(request.form["material_cost"])
        material_margin_pct = _parse_float(request.form.get("material_margin_pct", "0"))
        hourly_margin_pct = _parse_float(request.form.get("hourly_margin_pct", "0"))
        double_time_hours = _parse_float(request.form.get("double_time_hours", "0"))
        travel_cost = _parse_float(request.form.get("travel_cost", "0"))
        hotel_cost = _parse_float(request.form.get("hotel_cost", "0"))
        per_diem_cost = _parse_float(request.form.get("per_diem_cost", "0"))
        hours_per_week_setting = _parse_float(
            request.form.get("hours_per_week", "80")
        )

        calculator = OfferCalculator(load_company_costs(session))
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

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        chart_relative = os.path.join("generated", f"offer_{timestamp}.png")
        chart_path = os.path.join("static", chart_relative)
        os.makedirs(os.path.dirname(chart_path), exist_ok=True)
        calculator.plot_offer_structure(offer, output_path=chart_path)

        offer_model = OfferModel(
            project_id=project_id,
            hours=hours,
            material_cost=material_cost,
            material_margin_pct=material_margin_pct,
            hourly_margin_pct=hourly_margin_pct,
            double_time_hours=double_time_hours,
            travel_cost=travel_cost,
            hotel_cost=hotel_cost,
            per_diem_cost=per_diem_cost,
            hours_per_week=hours_per_week_setting,
            result_payload=offer_payload_from_breakdown(offer),
            chart_path=chart_relative,
        )
        session.add(offer_model)
        session.commit()
        flash("Oferta została wyliczona i zapisana.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się wyliczyć oferty.", "error")
    return _redirect_with_project(project_id)


@app.post("/set_invoice_issuer")
def set_invoice_issuer():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    try:
        issuer = session.query(InvoiceIssuerModel).first()
        if issuer is None:
            issuer = InvoiceIssuerModel(
                name=request.form["name"],
                address=request.form["address"],
                nip=request.form["nip"],
                bank_account=request.form["bank_account"],
            )
        else:
            issuer.name = request.form["name"]
            issuer.address = request.form["address"]
            issuer.nip = request.form["nip"]
            issuer.bank_account = request.form["bank_account"]
        session.add(issuer)
        session.commit()
        flash("Zapisano dane wystawcy.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się zapisać wystawcy.", "error")
    return _redirect_with_project(project_id)


@app.post("/generate_invoice")
def generate_invoice():
    session = get_db()
    project_id = _parse_int(request.form.get("project_id"))
    project = session.get(ProjectModel, project_id) if project_id else None
    if project is None:
        flash("Wybierz projekt, aby wygenerować fakturę.", "error")
        return redirect(url_for("index"))

    issuer_model = session.query(InvoiceIssuerModel).first()
    if issuer_model is None:
        flash("Uzupełnij dane wystawcy faktury.", "error")
        return _redirect_with_project(project_id)

    try:
        protocol_number = request.form["protocol_number"]
        protocol_model = next(
            (proto for proto in project.acceptance_protocols if proto.protocol_number == protocol_number),
            None,
        )
        if protocol_model is None:
            raise ValueError("Nie znaleziono wybranego protokołu.")

        protocol = AcceptanceProtocol(
            protocol_number=protocol_model.protocol_number,
            project_name=project.name,
            accepted_scope=protocol_model.accepted_scope,
            date_signed=protocol_model.date_signed,
            value=protocol_model.value,
            partial=protocol_model.partial,
        )

        buyer = InvoiceBuyer(
            name=request.form["buyer_name"],
            address=request.form["buyer_address"],
            nip=request.form["buyer_nip"],
        )
        invoice_generator = InvoiceGenerator(issuer_from_model(issuer_model))
        invoice = invoice_generator.from_acceptance(
            protocol=protocol,
            buyer=buyer,
            invoice_number=request.form["invoice_number"],
            payment_terms=request.form.get("payment_terms", "14 dni"),
            tax_rate=_parse_float(request.form.get("tax_rate", "23")),
        )

        invoice_model = InvoiceModel(
            project_id=project_id,
            invoice_number=invoice.number,
            buyer_name=buyer.name,
            payload=invoice_to_payload(invoice),
        )
        session.add(invoice_model)
        session.commit()
        flash("Wygenerowano fakturę i zapisano w bazie.", "success")
    except Exception as exc:  # pylint: disable=broad-except
        session.rollback()
        flash(str(exc) or "Nie udało się wygenerować faktury.", "error")
    return _redirect_with_project(project_id)


if __name__ == "__main__":
    app.run(debug=True)
