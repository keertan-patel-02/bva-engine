"""Tests for the variance engine.  
====================================================
test_load_pnl -> checks full pnl is loading
test_revenue_overage -> Checks signage of variance_fav is positive for revenue greater than budget
test_expense_overage -> Checks signage of variance_fav is negative for expense greater than budget
test_dollar_floor_flag_alone -> Checks that a variance that only breaks dollar floor does not flag as material
test_pct_floor_flag_alone -> Checks that a variance that only breaks pct floor does not flag as material
test_zero_budget_material_flag -> Checks that zero budget items flag only when they abide by the dollar floor 
test_summarize_profit_totals -> Checks that the sum of variance_fav of the two toatls lines shows the profit
====================================================
Run with:  python -m pytest -q
"""
import pandas as pd
import math
from bva.variance import load_pnl, build_variance, flag_material, summarize

def tiny(*rows):
    ## Build a minimal pnl frame that will be used for the tests. 
    out = []
    for section, line_item, budget, actual in rows:
        for scenario, amount in ("budget", budget), ("actual", actual):
            out.append({
                "period": "2026-01", "entity_id": "H",
                "section": section, "line_item": line_item,
                "scenario": scenario, "amount": float(amount),
            })
    return pd.DataFrame(out)
            

def test_load_pnl_reads_every_row():
    assert len(load_pnl()) == 720

def test_revenue_overage():
    df = build_variance(tiny(("Revenue", "Rooms Revenue", 100, 110)))
    row = df.iloc[0]
    assert row["favorable"]
    assert row["variance"] == 10
    assert row["variance_fav"] == 10


def test_expense_overage():
    df = build_variance(tiny(("Departmental Expenses", "Rooms Labor", 100, 110)))
    row = df.iloc[0]
    assert not row["favorable"]
    assert row["variance"] == 10
    assert row["variance_fav"] == -10

def test_dollar_floor_flag_alone():
    df = build_variance(tiny(("Departmental Expenses", "Rooms Labor", 100000, 103000)))
    df = flag_material(df)
    row = df.iloc[0]
    assert not row["material"]
    assert abs(row["variance"]) == 3000
    assert abs(row["variance_pct"]) <= 0.03

def test_pct_floor_flag_alone():
    df = build_variance(tiny(("Departmental Expenses", "Rooms Labor", 100, 150)))
    df = flag_material(df)
    row = df.iloc[0]
    assert not row["material"]
    assert abs(row["variance"]) == 50
    assert abs(row["variance_pct"]) == 0.5

def test_zero_budget_material_flag():
    df = build_variance(tiny(("Departmental Expenses", "Rooms Labor", 0, 50000)))
    df = flag_material(df)
    row = df.iloc[0]
    assert row["material"]
    assert abs(row["variance"]) == 50000
    assert math.isinf(row["variance_pct"])

def test_summarize_profit_totals():
    df = build_variance(tiny(("Revenue", "Rooms Revenue", 100, 110), ("Departmental Expenses", "Rooms Labor", 100, 130)))
    df = summarize(df)
    totals = df[df["section"].isin(["Total Revenue", "Total Expenses"])]
    profit = totals["variance_fav"].sum()
    assert abs(profit -(-20)) <= 0.01
    assert len(df) == 4