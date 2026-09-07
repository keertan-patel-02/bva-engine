"""
Synthetic P&L and revenue-driver data generator.

Produces two tidy CSVs under ``data/`` for a 12-month year across two hotel
properties, in both ``budget`` and ``actual`` scenarios:

  pnl.csv              period, entity_id, section, line_item, scenario, amount
  revenue_drivers.csv  period, entity_id, segment, scenario, room_nights, adr

The two files are consistent by construction: the Rooms Revenue line in
``pnl.csv`` equals ``sum(room_nights * adr)`` from ``revenue_drivers.csv`` for
the same period/entity/scenario. That invariant is what lets the volume/rate/mix
bridge (S3) reconcile to the reported revenue variance, and it is worth a test.

The chart of accounts follows the shape of USALI (the Uniform System of Accounts
for the Lodging Industry): revenue, departmental expenses, undistributed
operating expenses, fixed charges.

Actuals are budget plus bounded noise, plus four deliberately planted events so
the variance report has stories in it rather than just drift:

  1. HOTEL_A, Jun 2026 -- group segment collapses ~28%, transient partly fills
     the gap. Volume down, but mix shifts toward higher-rate transient, so the
     rate and mix components of the bridge pull in opposite directions.
  2. HOTEL_A, Jan 2026 -- utilities +24% on a cold snap.
  3. HOTEL_A, Mar 2026 -- F&B cost of sales +28% on food inflation and waste.
  4. HOTEL_B, Jul-Sep 2026 -- post-renovation rate push: ADR +6.5% while
     occupancy gives back 3%.

All randomness is seeded, so the dataset is reproducible.
"""

from __future__ import annotations

import calendar
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260907
YEAR = 2026
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

SEGMENTS = ["Transient", "Group", "Contract"]

# Monthly demand index for New England hospitality: soft winter, summer peak.
SEASONALITY = {
    1: 0.72, 2: 0.74, 3: 0.82, 4: 0.90, 5: 1.00, 6: 1.12,
    7: 1.20, 8: 1.18, 9: 1.05, 10: 0.98, 11: 0.82, 12: 0.78,
}

PROPERTIES = {
    "HOTEL_A": {
        "name": "Harborview Inn",
        "rooms": 120,
        "base_occupancy": 0.72,
        "adr": {"Transient": 189.0, "Group": 155.0, "Contract": 132.0},
        "mix": {"Transient": 0.55, "Group": 0.30, "Contract": 0.15},
        "fnb_spend_per_room_night": 38.0,
        "other_spend_per_room_night": 9.0,
    },
    "HOTEL_B": {
        "name": "Brookfield Suites",
        "rooms": 85,
        "base_occupancy": 0.65,
        "adr": {"Transient": 152.0, "Group": 128.0, "Contract": 110.0},
        "mix": {"Transient": 0.60, "Group": 0.22, "Contract": 0.18},
        "fnb_spend_per_room_night": 24.0,
        "other_spend_per_room_night": 6.0,
    },
}

# line_item -> (section, variable cost per occupied room night, fixed cost per
# available room per month). Management Fees is handled separately as a
# percentage of total revenue.
EXPENSE_MODEL = {
    "Rooms Labor":                       ("Departmental Expenses", 21.0, 42.0),
    "Rooms Other Expense":               ("Departmental Expenses",  8.5, 12.0),
    "F&B Labor":                         ("Departmental Expenses", 13.0, 28.0),
    "F&B Cost of Sales":                 ("Departmental Expenses", 11.5,  0.0),
    "F&B Other Expense":                 ("Departmental Expenses",  3.2,  6.0),
    "Administrative & General":          ("Undistributed Operating Expenses", 2.4, 55.0),
    "Sales & Marketing":                 ("Undistributed Operating Expenses", 3.1, 40.0),
    "Property Operations & Maintenance": ("Undistributed Operating Expenses", 2.8, 46.0),
    "Utilities":                         ("Undistributed Operating Expenses", 4.6, 52.0),
    "Property Insurance":                ("Fixed Charges", 0.0, 30.0),
    "Property Taxes":                    ("Fixed Charges", 0.0, 68.0),
}

MANAGEMENT_FEE_RATE = 0.03


def _period(month: int) -> str:
    return f"{YEAR}-{month:02d}"


def _driver_rows(entity_id: str, month: int, scenario: str, rng: np.random.Generator):
    """Build the per-segment room-night and ADR rows for one property-month."""
    p = PROPERTIES[entity_id]
    available = p["rooms"] * calendar.monthrange(YEAR, month)[1]

    occupancy = min(p["base_occupancy"] * SEASONALITY[month], 0.95)
    mix = dict(p["mix"])
    adr = dict(p["adr"])

    if scenario == "actual":
        occupancy *= 1 + rng.normal(0, 0.025)
        adr = {s: v * (1 + rng.normal(0, 0.015)) for s, v in adr.items()}

        # Event 1: group shortfall at HOTEL_A in June, partly filled by transient.
        if entity_id == "HOTEL_A" and month == 6:
            mix["Group"] *= 0.72
            mix["Transient"] *= 1.06

        # Event 4: HOTEL_B post-renovation rate push, at a small occupancy cost.
        if entity_id == "HOTEL_B" and month in (7, 8, 9):
            adr = {s: v * 1.065 for s, v in adr.items()}
            occupancy *= 0.97

        total = sum(mix.values())
        mix = {s: w / total for s, w in mix.items()}

    occupied = available * min(occupancy, 0.98)

    return [
        {
            "period": _period(month),
            "entity_id": entity_id,
            "segment": segment,
            "scenario": scenario,
            "room_nights": round(occupied * mix[segment], 1),
            "adr": round(adr[segment], 2),
        }
        for segment in SEGMENTS
    ]


def _pnl_rows(entity_id: str, month: int, scenario: str, drivers: list[dict],
              rng: np.random.Generator):
    """Build the P&L line items for one property-month from its driver rows."""
    p = PROPERTIES[entity_id]
    occupied = sum(d["room_nights"] for d in drivers)
    rooms_revenue = sum(d["room_nights"] * d["adr"] for d in drivers)

    noise = (lambda: 1 + rng.normal(0, 0.03)) if scenario == "actual" else (lambda: 1.0)

    fnb_revenue = occupied * p["fnb_spend_per_room_night"] * noise()
    other_revenue = occupied * p["other_spend_per_room_night"] * noise()
    total_revenue = rooms_revenue + fnb_revenue + other_revenue

    rows = [
        ("Revenue", "Rooms Revenue", rooms_revenue),
        ("Revenue", "Food & Beverage Revenue", fnb_revenue),
        ("Revenue", "Other Operating Revenue", other_revenue),
    ]

    for line_item, (section, var_rate, fixed_per_room) in EXPENSE_MODEL.items():
        amount = (var_rate * occupied + fixed_per_room * p["rooms"]) * noise()

        if scenario == "actual":
            # Event 2: cold-snap utilities spike.
            if entity_id == "HOTEL_A" and month == 1 and line_item == "Utilities":
                amount *= 1.24
            # Event 3: food inflation.
            if entity_id == "HOTEL_A" and month == 3 and line_item == "F&B Cost of Sales":
                amount *= 1.28

        rows.append((section, line_item, amount))

    rows.append(("Fixed Charges", "Management Fees", total_revenue * MANAGEMENT_FEE_RATE))

    return [
        {
            "period": _period(month),
            "entity_id": entity_id,
            "section": section,
            "line_item": line_item,
            "scenario": scenario,
            "amount": round(amount, 2),
        }
        for section, line_item, amount in rows
    ]


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    driver_rows, pnl_rows = [], []

    for entity_id in PROPERTIES:
        for month in range(1, 13):
            for scenario in ("budget", "actual"):
                d = _driver_rows(entity_id, month, scenario, rng)
                driver_rows.extend(d)
                pnl_rows.extend(_pnl_rows(entity_id, month, scenario, d, rng))

    return pd.DataFrame(pnl_rows), pd.DataFrame(driver_rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pnl, drivers = build()
    pnl.to_csv(DATA_DIR / "pnl.csv", index=False)
    drivers.to_csv(DATA_DIR / "revenue_drivers.csv", index=False)
    print(f"wrote {len(pnl):>4} rows -> {DATA_DIR / 'pnl.csv'}")
    print(f"wrote {len(drivers):>4} rows -> {DATA_DIR / 'revenue_drivers.csv'}")


if __name__ == "__main__":
    main()
