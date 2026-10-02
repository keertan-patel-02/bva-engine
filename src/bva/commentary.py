

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
    ...