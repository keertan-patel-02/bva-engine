
import pandas as pd
from pathlib import Path
from openpyxl.styles import Font, PatternFill, Alignment
from bva.variance import load_pnl, build_variance, flag_material, summarize, load_drivers
from bva.bridge import build_bridge


OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
MONEY = "#,##0.00;(#,##0.00)"
PERCENT = "0.0%"

def output_excel(period):
    """
    Creates an excel file with a summary table for the property portfolio and variance tables and bridge tables per property for a given period.
    Arguments -> period
    Requires that period be in the PNL.
    """
    pnl = load_pnl()
    available = sorted(pnl["period"].unique())
    if not (pnl["period"] == period).any():
        raise ValueError(f"{period!r} not in the P&L. Available periods: {', '.join(available)}")
    drivers = load_drivers()
    summary_df = summarize(build_variance(pnl, period))

    with pd.ExcelWriter(path=OUTPUT_DIR/f"bva_pack_{period}.xlsx", engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        format_sheet(writer.sheets["Summary"])

        for entity in sorted(pnl["entity_id"].unique()):
            entity_df = flag_material(build_variance(pnl, period, entity))
            entity_bridge_df = build_bridge(drivers, period, entity)
            entity_df.to_excel(writer, sheet_name=entity, index=False)
            format_sheet(writer.sheets[entity])
            entity_bridge_df.to_excel(writer, sheet_name=f"{entity}_bridge", index=False)
            format_sheet(writer.sheets[f"{entity}_bridge"])
        

def format_sheet(ws):
    ws.freeze_panes ="A2"
    ## row 1 holds the headers
    for header_cell in ws[1]:
        name = header_cell.value
        letter = header_cell.column_letter

        header_cell.font = Font(bold=True)

        if name in ("budget", "actual", "variance", "variance_fav", "amount"):
            fmt = MONEY
            ws.column_dimensions[letter].width = 14
        elif name == "variance_pct":
            fmt = PERCENT
            ws.column_dimensions[letter].width = 10
        else:
            ws.column_dimensions[letter].width = max(len(str(cell.value)) for cell in ws[letter]) + 2
            continue

        for cell in ws[letter][1:]:
            cell.number_format = fmt