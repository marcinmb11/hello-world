"""Offer calculation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import matplotlib.pyplot as plt

from .company_costs import CompanyCosts


@dataclass
class OfferBreakdown:
    """Structure describing all components of an offer."""

    base_hourly_rate: float
    hours: float
    material_cost: float
    material_margin_amount: float
    hourly_margin_amount: float
    double_time_hours: float
    double_time_cost: float
    travel_cost: float
    hotel_cost: float
    per_diem_cost: float
    total_cost: float
    profit: float

    def to_dict(self) -> Dict[str, float]:
        """Return a serialisable representation."""
        return {
            "base_hourly_rate": self.base_hourly_rate,
            "hours": self.hours,
            "material_cost": self.material_cost,
            "material_margin_amount": self.material_margin_amount,
            "hourly_margin_amount": self.hourly_margin_amount,
            "double_time_hours": self.double_time_hours,
            "double_time_cost": self.double_time_cost,
            "travel_cost": self.travel_cost,
            "hotel_cost": self.hotel_cost,
            "per_diem_cost": self.per_diem_cost,
            "total_cost": self.total_cost,
            "profit": self.profit,
        }


class OfferCalculator:
    """Calculate offers based on company costs and project assumptions."""

    def __init__(self, company_costs: CompanyCosts) -> None:
        self.company_costs = company_costs

    def base_hourly_rate(self, hours_per_week: float = 80.0) -> float:
        return self.company_costs.hourly_rate(hours_per_week=hours_per_week)

    def calculate_double_time_cost(self, base_rate: float, double_time_hours: float) -> float:
        return base_rate * 2 * double_time_hours

    def calculate_offer(
        self,
        hours: float,
        material_cost: float,
        material_margin_pct: float = 0.0,
        hourly_margin_pct: float = 0.0,
        double_time_hours: float = 0.0,
        travel_cost: float = 0.0,
        hotel_cost: float = 0.0,
        per_diem_cost: float = 0.0,
        hours_per_week: float = 80.0,
    ) -> OfferBreakdown:
        base_rate = self.base_hourly_rate(hours_per_week=hours_per_week)
        base_labor_cost = base_rate * hours
        material_margin_amount = material_cost * material_margin_pct / 100
        hourly_margin_amount = base_labor_cost * hourly_margin_pct / 100
        double_time_cost = self.calculate_double_time_cost(base_rate, double_time_hours)

        total_cost = (
            base_labor_cost
            + material_cost
            + material_margin_amount
            + hourly_margin_amount
            + double_time_cost
            + travel_cost
            + hotel_cost
            + per_diem_cost
        )

        profit = material_margin_amount + hourly_margin_amount + double_time_cost + travel_cost + hotel_cost + per_diem_cost
        return OfferBreakdown(
            base_hourly_rate=base_rate,
            hours=hours,
            material_cost=material_cost,
            material_margin_amount=material_margin_amount,
            hourly_margin_amount=hourly_margin_amount,
            double_time_hours=double_time_hours,
            double_time_cost=double_time_cost,
            travel_cost=travel_cost,
            hotel_cost=hotel_cost,
            per_diem_cost=per_diem_cost,
            total_cost=total_cost,
            profit=profit,
        )

    def plot_offer_structure(
        self,
        offer: OfferBreakdown,
        output_path: Optional[str] = None,
    ) -> str:
        """Create a pie chart showing cost distribution and return the path."""
        labels = [
            "Koszty materiałów",
            "Marża materiałowa",
            "Marża roboczogodziny",
            "Roboczogodziny 200%",
            "Koszt podróży",
            "Koszt hotelu",
            "Diety",
        ]
        sizes = [
            offer.material_cost,
            offer.material_margin_amount,
            offer.hourly_margin_amount,
            offer.double_time_cost,
            offer.travel_cost,
            offer.hotel_cost,
            offer.per_diem_cost,
        ]
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct="%1.1f%%")
        plt.title("Struktura oferty")
        if not output_path:
            output_path = "images/offer_pie_chart.png"
        plt.savefig(output_path, bbox_inches="tight")
        plt.close()
        return output_path
