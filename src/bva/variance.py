"""
Core variance engine.  ***S2 -- YOU WRITE THIS.***

Everything below is a specification, not a hint. Delete the TODOs as you go.
Do not add the bridge here; that is S3 in bridge.py.

--------------------------------------------------------------------------
THE ONE THING THAT MAKES THIS FP&A AND NOT ARITHMETIC
--------------------------------------------------------------------------
A raw variance is `actual - budget`. That number alone is meaningless until
you know whether the line is revenue or expense:

    Revenue   actual 110 vs budget 100  ->  +10  ->  FAVORABLE
    Expense   actual 110 vs budget 100  ->  +10  ->  UNFAVORABLE

So you need TWO columns, and they are not the same column:
    variance      = actual - budget          (signed, always the same formula)
    variance_fav  = the same magnitude, signed so that positive == good

For expense lines, variance_fav = -(actual - budget). For revenue, they match.
Sections "Departmental Expenses", "Undistributed Operating Expenses" and
"Fixed Charges" are expenses; "Revenue" is revenue.

Be able to explain in an interview why you keep both columns rather than
collapsing to one. (Hint: one of them has to sum correctly down a P&L; the
other one is what a reader wants to see on a single line.)
--------------------------------------------------------------------------

FUNCTIONS TO IMPLEMENT
--------------------------------------------------------------------------

load_pnl(path="data/pnl.csv") -> pd.DataFrame
    Read the tidy CSV. Return it as-is; no reshaping here.

build_variance(pnl, period=None, entity_id=None) -> pd.DataFrame
    Pivot budget and actual into side-by-side columns keyed on
    (period, entity_id, section, line_item), then compute:
        variance       actual - budget
        variance_pct   variance / budget       -- guard divide-by-zero
        variance_fav   sign-corrected per the rule above
        favorable      bool, variance_fav > 0
    Optionally filter to one period and/or one entity.
    Watch out: a pivot can silently produce NaN if a line exists in one
    scenario and not the other. Decide what that should mean and handle it.

flag_material(df, dollar_floor=5000.0, pct_floor=0.05) -> pd.DataFrame
    Add a bool column `material`, True only when BOTH thresholds are breached:
        abs(variance) >= dollar_floor AND abs(variance_pct) >= pct_floor
    The "both" is the entire point. Either one alone gives you a useless
    report: a dollar-only threshold buries you in big-line noise, a
    percent-only threshold flags a $600 swing on a small line. Property
    Taxes moving 0.4% on a big number should not flag; Utilities moving
    26% on a small one should. Test exactly that.

summarize(df) -> pd.DataFrame
    Roll up to section level for the summary tab: budget, actual, variance,
    variance_fav per section, plus a Total Revenue and Total Expenses row.

TODO(S2): implement the four functions above.
TODO(S2): write tests/test_variance.py -- at minimum:
          - a revenue overage is favorable
          - an expense overage is unfavorable
          - a line breaching only the dollar floor does NOT flag
          - a line breaching only the percent floor does NOT flag
          - zero budget does not raise
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

REVENUE_SECTION = "Revenue"
EXPENSE_SECTIONS = (
    "Departmental Expenses",
    "Undistributed Operating Expenses",
    "Fixed Charges",
)

def load_pnl(path="data/pnl.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def build_variance(pnl, period=None, entity_id=None) -> pd.DataFrame:
    df = pnl
    pivoted_df = df.pivot(
        index=['period', 'entity_id', 'section', 'line_item'],
        columns='scenario',
        values='amount'
    )
    # Reseting Index for Pivoted Table
    pivoted_df = pivoted_df.reset_index()
    # Renaming Axis
    pivoted_df = pivoted_df.rename_axis(columns=None)

    # Calculating Variance
    pivoted_df['variance'] = pivoted_df['actual'] - pivoted_df['budget']
    pivoted_df['variance_pct'] = pivoted_df['variance'] / pivoted_df['budget']
    # Flip signs based on if variance is favorable or not based on section.
    pivoted_df['variance_fav'] = np.where(pivoted_df['section'].isin(EXPENSE_SECTIONS), pivoted_df['variance']*-1, pivoted_df['variance'])
    # Is the variance favorable or not
    pivoted_df['favorable'] = pivoted_df['variance_fav'] > 0
    return pivoted_df