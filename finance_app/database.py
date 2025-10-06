"""Database models and helpers for the finance application."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, scoped_session, sessionmaker


def _database_url() -> str:
    return os.environ.get("FINANCE_APP_DATABASE_URL", "sqlite:///finance_app.db")


engine = create_engine(_database_url(), future=True)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
)


class Base(DeclarativeBase):
    """Base declarative class."""


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    net_salary: Mapped[float] = mapped_column(Float, nullable=False)
    gross_salary: Mapped[float] = mapped_column(Float, nullable=False)
    salary_components: Mapped[dict] = mapped_column(JSON, default=dict)


class OfficeCost(Base):
    __tablename__ = "office_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)


class AdditionalCost(Base):
    __tablename__ = "additional_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)


class LeasingCost(Base):
    __tablename__ = "leasing_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    deductible_ratio: Mapped[float] = mapped_column(Float, nullable=False)


class BoardMember(Base):
    __tablename__ = "board_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gross_salary: Mapped[float] = mapped_column(Float, nullable=False)
    social_security: Mapped[float] = mapped_column(Float, nullable=False)
    health_insurance: Mapped[float] = mapped_column(Float, nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    employee_assignments: Mapped[list["ProjectEmployeeAssignment"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    social_budget: Mapped["ProjectSocialBudget | None"] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False
    )
    material_items: Mapped[list["ProjectMaterialItem"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    acceptance_protocols: Mapped[list["ProjectAcceptanceProtocol"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    offers: Mapped[list["OfferModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["InvoiceModel"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectEmployeeAssignment(Base):
    __tablename__ = "project_employee_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    employee_name: Mapped[str] = mapped_column(String, nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    planned_hours: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped[Project] = relationship(back_populates="employee_assignments")


class ProjectSocialBudget(Base):
    __tablename__ = "project_social_budgets"

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    hotel_budget: Mapped[float] = mapped_column(Float, default=0.0)
    per_diem_budget: Mapped[float] = mapped_column(Float, default=0.0)
    container_rental_budget: Mapped[float] = mapped_column(Float, default=0.0)

    project: Mapped[Project] = relationship(back_populates="social_budget")


class ProjectMaterialItem(Base):
    __tablename__ = "project_material_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    item_cost: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped[Project] = relationship(back_populates="material_items")


class ProjectAcceptanceProtocol(Base):
    __tablename__ = "project_acceptance_protocols"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    protocol_number: Mapped[str] = mapped_column(String, nullable=False)
    accepted_scope: Mapped[str] = mapped_column(String, nullable=False)
    date_signed: Mapped[Date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    partial: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship(back_populates="acceptance_protocols")


class OfferModel(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    hours: Mapped[float] = mapped_column(Float, nullable=False)
    material_cost: Mapped[float] = mapped_column(Float, nullable=False)
    material_margin_pct: Mapped[float] = mapped_column(Float, default=0.0)
    hourly_margin_pct: Mapped[float] = mapped_column(Float, default=0.0)
    double_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    travel_cost: Mapped[float] = mapped_column(Float, default=0.0)
    hotel_cost: Mapped[float] = mapped_column(Float, default=0.0)
    per_diem_cost: Mapped[float] = mapped_column(Float, default=0.0)
    hours_per_week: Mapped[float] = mapped_column(Float, default=80.0)
    result_payload: Mapped[dict] = mapped_column(JSON)
    chart_path: Mapped[str | None] = mapped_column(String)

    project: Mapped[Project | None] = relationship(back_populates="offers")


class InvoiceIssuerModel(Base):
    __tablename__ = "invoice_issuer"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    nip: Mapped[str] = mapped_column(String, nullable=False)
    bank_account: Mapped[str] = mapped_column(String, nullable=False)


class InvoiceModel(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    invoice_number: Mapped[str] = mapped_column(String, nullable=False)
    buyer_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON)

    project: Mapped[Project | None] = relationship(back_populates="invoices")


def init_db() -> None:
    """Create database tables if they do not yet exist."""

    Base.metadata.create_all(bind=engine)


__all__ = [
    "SessionLocal",
    "init_db",
    "Employee",
    "OfficeCost",
    "AdditionalCost",
    "LeasingCost",
    "BoardMember",
    "Project",
    "ProjectEmployeeAssignment",
    "ProjectSocialBudget",
    "ProjectMaterialItem",
    "ProjectAcceptanceProtocol",
    "OfferModel",
    "InvoiceIssuerModel",
    "InvoiceModel",
]
