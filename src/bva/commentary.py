

MATERIAL_EFFECT = 2500.00

def material_lines_comment(detail_df):
    """
    One sentence per material line, biggest dollar swing first.
    Details dataframe that includes the data for variance, variance_fav, and materiality for all line items
    Returns list of strings
    """
    material_df = detail_df[detail_df["material"]]
    
    material_df = material_df.sort_values("variance", key=abs, ascending=False)

    comments = []

    for row in material_df.itertuples():
        direction = "above" if row.variance > 0 else "below"
        verdict = "favorable" if row.variance_fav > 0 else "unfavorable"

        comments.append(
            f"{row.line_item} came in ${abs(row.variance):,.0f} "
            f"({abs(row.variance_pct):.1%}) {direction} budget — {verdict}."
        )
    return comments

def bridge_comment(bridge_df, segment_df):
    amounts = bridge_df.set_index("component")["amount"]
    segments = segment_df.set_index("segment")

    total = amounts["Actual Revenue"] - amounts["Budget Revenue"]
    pct = total / amounts["Budget Revenue"]

    direction = "above" if total > 0 else "below"
    headline = f"Rooms revenue finished ${total:,.0f} ({abs(pct):.1%}) {direction} budget."
    ...


def _phrase(name, amount):
    ## volume' + 2213.215 -> 'volume added $2214' (verb from the signage)
    ...

def _volume_clause(segments):
    ## Toal nights actual vs budget. Sums two columns, names no segment
    ...

def _mix_clause(segments):
    ## Always two-sided: top gainer and bottom returner from 'mix_effect'
    ...

def _rate_clause(segments):
    ## Largest absolute'rate_effect' segment, with its ADR gap and its nights
    ...