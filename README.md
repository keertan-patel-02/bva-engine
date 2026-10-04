# BvA Engine

Budget-vs-actual variance analysis for multi-property hotel P&L. Reads a month
of budget and actual figures, applies FP&A sign conventions, flags the variances
that are genuinely material, decomposes rooms revenue into a volume / mix / rate
bridge that ties to the cent, and writes a formatted Excel pack.

## Why this exists

A raw variance is `actual - budget`. That number is meaningless on its own:

| | actual | budget | variance | verdict |
|---|---|---|---|---|
| Rooms Revenue | 110 | 100 | +10 | favorable |
| Utilities | 110 | 100 | +10 | **unfavorable** |

So the engine carries two columns, not one. `variance` is what reads correctly
on a single line; `variance_fav` is sign-corrected so that positive means good,
and it's the one that sums down the P&L to the actual profit impact.

Everything else in the tool follows from taking that distinction seriously.

## Install

```bash
git clone https://github.com/keertan-patel-02/bva-engine.git
cd bva-engine
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Python 3.10+.

## Usage

```bash
python -m bva report --month 2026-06
```

Writes `output/bva_pack_2026-06.xlsx` and prints the path. Any month in
`2026-01` … `2026-12`; an unrecognised month fails before anything is written
and lists the months that are available.

## What you get

Five tabs:

| tab | contents |
|---|---|
| `Summary` | section-level roll-up with Total Revenue and Total Expenses |
| `HOTEL_A` | all 15 line items — budget, actual, variance, variance %, favourable |
| `HOTEL_A_bridge` | the 5-row volume/mix/rate bridge plus a waterfall chart |
| `HOTEL_B` | as above |
| `HOTEL_B_bridge` | as above |

Money formatted `#,##0.00` with negatives in parentheses, percentages to one
decimal, headers frozen, and every column sized to its widest value. Material
lines are filled amber with a count legend below the table.

## Materiality: two thresholds, not one

A line flags only when it breaches **both** `$2,500` and `5%`.

Either floor alone is useless on a real chart of accounts. The line items here
span 117× — Rooms Revenue runs ~$422k a month, Property Insurance ~$3.6k — so a
dollar-only threshold buries you in noise from the big lines, and a percent-only
threshold flags a $600 swing on a small one. Property Taxes moving 0.4% on a
large base should not flag. Utilities moving 26% on a small one should.

The floors were calibrated against a full year of data rather than guessed:
`$5,000 / 5%` surfaced 2 lines out of 360 and caught none of the planted
events. `$2,500 / 5%` surfaces 8, including the ones that matter.

## The bridge, and why it's the point

Materiality finds lines that moved. The bridge finds lines that *didn't move but
should have*.

HOTEL_A, June 2026 — rooms revenue came in **+$2,868 on $494,252, up 0.58%**.
Nothing flags. Nothing on the P&L looks interesting. Underneath:

```
Budget Revenue    494,251.80
  Volume           +2,213.25     total room nights roughly on plan
  Mix              +5,840.75     Group 871 -> 664 nights (-24%),
                                 Transient 1,597 -> 1,792 (+12%)
  Rate             -5,186.20     Transient ADR 189.00 -> 186.02
Actual Revenue    497,119.60
```

A group block collapsed and transient demand backfilled it at a lower rate. Two
large offsetting effects and a rate concession, netting to a rounding error on
the P&L. That is the month a variance report should have caught and a
threshold never will.

### How the decomposition works

Notation, since the formulas need it:

| | meaning |
|---|---|
| `Qb`, `Qa` | total room nights — budget, actual |
| `Qb_i`, `Qa_i` | room nights in segment *i* (Transient, Group, Contract) |
| `Pb_i`, `Pa_i` | ADR in segment *i* — budget, actual |
| `B`, `A` | rooms revenue — budget, actual |
| `w_i` | segment *i*'s share of total budget room nights, `Qb_i / Qb` |
| `P̄` | blended budget rate, `B / Qb` — what one room night was budgeted to earn on average |

Each effect is measured *after* the previous one is applied, which is why the
formulas are asymmetric:

```
volume = (Qa - Qb) x P̄                        more or fewer nights, priced at
                                              the blended budget rate

mix    = Σ_i (Qa_i - Qa x w_i) x Pb_i         nights landing in a different
                                              segment than budgeted, priced at
                                              that segment's budget ADR

rate   = Σ_i Qa_i x (Pa_i - Pb_i)             the price actually achieved vs
                                              budget, on the nights that
                                              actually happened
```

Each one holds the later variables at budget and lets only its own move. That
ordering is a choice — volume first, then mix, then rate — and it's why the three
numbers reconcile instead of overlapping.

**Why it ties.** One step first: the budget-weighted average of segment ADRs
*is* the blended budget rate, because `Σ_i w_i x Pb_i = Σ_i (Qb_i x Pb_i) / Qb
= B / Qb = P̄`. With that:

```
volume = Qa x P̄ - Qb x P̄        =  Qa x P̄ - B
mix    = Σ_i Qa_i x Pb_i - Qa x P̄
rate   = A - Σ_i Qa_i x Pb_i
```

Add them. The `Qa x P̄` terms cancel, the `Σ_i Qa_i x Pb_i` terms cancel, and
what survives is `A - B` — the total variance. Verified to the cent across all
24 property-months, largest residual ~4e-11.

**Volume deliberately has no per-segment figure.** The formula that looks right,
`(Qa_i - Qb_i) x Pb_i` — each segment's own night change at its own budget ADR —
sums to volume **plus** mix. On HOTEL_A June it gives +$8,054, which is exactly
`$2,213 + $5,841`. It's the combined volume-and-mix effect, so publishing it as
volume alongside a separate mix figure double-counts and breaks the tie-out.
Volume stays a property-level number.
## Tests

```bash
pip install -e ".[dev]"
python -m pytest -q
```

10 tests. The ones worth reading:

- `test_bridge_ties_to_total` — asserts all three components against a
  hand-verified fixture *and* the tie-out. A tie-out alone would pass for
  `volume=0, mix=0, rate=total`, so it pins the decomposition, not just the
  arithmetic identity.
- `test_bridge_ties_to_pnl` — reads the real CSVs on purpose. A fixture cannot
  test whether two files agree with each other.
- `test_dollar_floor_flag_alone` / `test_pct_floor_flag_alone` — the "both
  thresholds" rule in both directions.
- `test_zero_budget_material_flag` — unbudgeted lines produce `inf`, which is
  left in place rather than coerced to `NaN`. An unbudgeted $48k line is the
  most important row in the report; silently suppressing it would be the worst
  possible default.

## Data

The repo ships synthetic, seeded data (`SEED = 20260907`) so the numbers are
identical on every clone and the tests assert against fixed values.

It is not arbitrary, though. The structure is a real one: a USALI chart of
accounts — the hospitality industry standard — across two properties with three
demand segments, which is the shape an actual hotel P&L arrives in.

- Harborview Inn — 120 rooms, $6.49M FY revenue
- Brookfield Suites — 85 rooms, $3.20M FY revenue
- 15 line items, FY2026 monthly: 720 P&L rows, 144 driver rows
- Segments: Transient, Group, Contract

Four variance events are planted deliberately so the engine has something real
to find, including the June group-displacement case above.

An invariant the test suite enforces: Rooms Revenue in `pnl.csv` equals
`Σ room_nights × ADR` from the drivers file, to the cent, in both scenarios.
The two files cannot drift apart silently.

Regenerate with `python -m bva.generate_data`.

### Running it on your own data

Point it at any P&L in the same tidy shape:

```
pnl.csv             period, entity_id, section, line_item, scenario, amount
revenue_drivers.csv period, entity_id, segment, scenario, room_nights, adr
```

Nothing in the engine is tied to these two properties or to twelve months —
tabs are generated from whatever `entity_id` values appear, so a third property
needs no code change. A different chart of accounts does need one edit:
`REVENUE_SECTION` and `EXPENSE_SECTIONS` in `variance.py` are what decide which
lines get their variance sign flipped, so new section names go there. The bridge
assumes a quantity × rate revenue line, which is general to hotels but not to
every industry.

## Roadmap

- Drafted commentary written into a `Commentary` tab — material-line sentences
  are built, the per-segment bridge paragraph is in progress
- Dataset moved to SQLite with the CSV loader replaced by queries