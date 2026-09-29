"""
Volume / rate / mix decomposition of rooms revenue variance.  ***S3.***

WHY THIS MODULE EXISTS -- read the dataset before you write a line of code:

    HOTEL_A, 2026-06, Rooms Revenue
        budget 494,252   actual 497,120   variance +2,868  (+0.6%)

On the P&L that month looks like nothing happened. Underneath:

        Group     room nights   871 -> 664   (-24%)
        Transient room nights 1,597 -> 1,792 (+12%)

A group block collapsed and transient walk-in partly backfilled it at a
higher rate. Volume down, rate up, mix richer -- three large effects that
nearly cancel. The P&L cannot show you that. The bridge can. This single
month is the reason the project is worth putting on a resume, and it is the
example you should walk an interviewer through.
"""
import pandas as pd
def build_segment_table(drivers, period, entity_id):
    """
    Creates a table using the drivers that is one segment per row for one property period
    Arguments: drivers, period, and entity_id
    Expects exactly one row per segment per scenario
    Pivot will raise if violated instead of silent averaging like pivot_table
    """
    drivers_df = drivers.copy()
    ## Filter for the entity_id and relevant period
    drivers_df = drivers_df[drivers_df["entity_id"] == entity_id]
    drivers_df = drivers_df[drivers_df["period"] == period]
    if drivers_df.empty:
        raise ValueError(
            f"No driver rows for entity_id={entity_id!r}, period={period!r}"
        )

    segment_table = drivers_df.pivot(index="segment", columns="scenario")

    segment_table.columns = ["_".join(col) for col in segment_table.columns]

    segment_table = segment_table[["room_nights_budget", "room_nights_actual", "adr_budget", "adr_actual"]]
    segment_table = segment_table.reset_index()
    return segment_table

def build_segment_effect(drivers, period, entity_id):
    """
    Calculates the effects of mix and rate and adds them to the segment table with one segment per row per period
    Arguments: drivers, period, entity_id
    """
    segment_table = build_segment_table(drivers, period, entity_id)

    quantity_budgeted_total = segment_table['room_nights_budget'].sum()
    quantity_actual_total = segment_table['room_nights_actual'].sum()
    budget_weights = segment_table["room_nights_budget"] / quantity_budgeted_total

    mix_series = (segment_table["room_nights_actual"] - (quantity_actual_total * budget_weights)) * segment_table["adr_budget"]
    
    rate_series = segment_table["room_nights_actual"] * (segment_table["adr_actual"] - segment_table["adr_budget"])

    segment_table["mix_effect"] = mix_series
    segment_table["rate_effect"] = rate_series
    return segment_table

def build_bridge(drivers, period, entity_id):
    """
    Returns a dataframe with one row per bridge step in waterfall order.
    Arguments: drivers, period, entity_id
    Sign Convention -> Positive is favorable since everything is revenue. No expenses in this table.
    Components sum to the total variance by construction. Construction is sequential and each effect is measured after the previous one is applied. 
    Volume is constructed on totals so there is no per-segment volume figure. 
    """
    segment_effect_table = build_segment_effect(drivers, period, entity_id)

    budget_rev_series = segment_effect_table["room_nights_budget"] * segment_effect_table["adr_budget"]
    budget_rev = budget_rev_series.sum()
    actual_rev_series = segment_effect_table["room_nights_actual"]* segment_effect_table["adr_actual"]
    actual_rev = actual_rev_series.sum()
    quantity_budgeted_total = segment_effect_table['room_nights_budget'].sum()
    quantity_actual_total = segment_effect_table['room_nights_actual'].sum()

    volume = (quantity_actual_total - quantity_budgeted_total) * (budget_rev/quantity_budgeted_total)
    mix = segment_effect_table["mix_effect"].sum()
    rate = segment_effect_table["rate_effect"].sum()

    output_data = {
        "period": [period]*5,
        "entity_id":[entity_id]*5,
        "component":["Budget Revenue", "Volume", "Mix", "Rate", "Actual Revenue"],
        "amount":[budget_rev, volume, mix, rate, actual_rev]
    }

    output_table = pd.DataFrame(output_data)
    return output_table

