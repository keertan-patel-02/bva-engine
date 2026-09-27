"""Tests for the variance engine.  ***S2 -- YOU WRITE THESE.***

See the TODO list at the bottom of src/bva/variance.py for the minimum set.
Run with:  python -m pytest -q
"""
import pandas as pd
from bva.variance import load_pnl, build_variance, flag_material, summarize

def tiny(*rows):
    ## Build a minimal pnl frame that will be used for the tests. 
    out = []
    for section, line_item, budget, actual in rows:
        for scenario, amount in (("budget", budget)), (("actual", actual)):
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
