"""
Tests for the bridge.
--------------------------------------------
test_bridge_ties_to_total() -> Check that Volume, Mix, and Rate values add up to Actual Revenue - Budget Revenue
test_missing_slice_raises() -> Makes sure that when asking for property-month that isn't in the data raises instead of a confusing KeyError
test_bridge_ties_to_pnl() -> Check to make sure that the bridge revnue values match pnl revenue values.


"""
import pandas as pd
import pytest
from bva.bridge import build_bridge
from bva.variance import load_pnl, load_drivers
def test_bridge_ties_to_total():
    data = [
        {"period": "2026-01","entity_id": "TEST","segment": "Group","scenario": "budget", "room_nights": 400, "adr": 120.00},
        {"period": "2026-01","entity_id": "TEST","segment": "Group","scenario": "actual", "room_nights": 310, "adr": 126.50},
        {"period": "2026-01","entity_id": "TEST","segment": "Transient","scenario": "budget", "room_nights": 600, "adr": 200.00},
        {"period": "2026-01","entity_id": "TEST","segment": "Transient","scenario": "actual", "room_nights": 745, "adr": 193.75}
    ]
    df = pd.DataFrame(data)
    bridge = build_bridge(df, "2026-01", "TEST")
    amounts = bridge.set_index("component")["amount"]

    assert amounts["Volume"] == pytest.approx(9240.00, abs= 0.01)
    assert amounts["Mix"] == pytest.approx(8960.00, abs= 0.01)
    assert amounts["Rate"] == pytest.approx(-2641.25, abs= 0.01)
    assert (amounts["Volume"] + amounts["Mix"] + amounts["Rate"]) == pytest.approx(amounts["Actual Revenue"] - amounts["Budget Revenue"], abs=0.01)

def test_missing_slice_raises():
    data = [
            {"period": "2026-01","entity_id": "TEST","segment": "Group","scenario": "budget", "room_nights": 400, "adr": 120.00},
            {"period": "2026-01","entity_id": "TEST","segment": "Group","scenario": "actual", "room_nights": 310, "adr": 126.50},
            {"period": "2026-01","entity_id": "TEST","segment": "Transient","scenario": "budget", "room_nights": 600, "adr": 200.00},
            {"period": "2026-01","entity_id": "TEST","segment": "Transient","scenario": "actual", "room_nights": 745, "adr": 193.75}
        ]
    df = pd.DataFrame(data)
    with pytest.raises(ValueError):
        build_bridge(df, "2026-01", "NOPE")

def test_bridge_ties_to_pnl():
    """
    Reads real data instead of using constructed data. The test is check that revenue_drivers.csv and pnl.csv describe the same reality.
    A synthetic fixture can't test this since the data itself is what is being tested. 
    If the dataset is regenerated with a broken invariant, this test failing is the right outcome.
    """
    pnl = load_pnl()
    drivers = load_drivers()


    pnl = pnl[pnl["entity_id"] == "HOTEL_A"]
    pnl = pnl[pnl["period"] == "2026-06"]
    pnl = pnl[pnl["section"] == "Revenue"]
    pnl = pnl[pnl["line_item"] == "Rooms Revenue"]

    bridge_df = build_bridge(drivers, "2026-06", "HOTEL_A")


    rooms_revenue_pnl_amounts = pnl.set_index("scenario")["amount"]
    bridge_amounts = bridge_df.set_index("component")["amount"]

    assert rooms_revenue_pnl_amounts["budget"] == pytest.approx(bridge_amounts["Budget Revenue"], abs= 0.01)
    assert rooms_revenue_pnl_amounts["actual"] == pytest.approx(bridge_amounts["Actual Revenue"], abs= 0.01)
    