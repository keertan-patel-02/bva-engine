"""Command-line entry point for the BvA engine.

    python -m bva report --month 2026-06
"""

from __future__ import annotations

import argparse

from bva.excel import output_excel


def build_parser() -> argparse.ArgumentParser:
    """Define the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="bva",
        description="Budget-vs-actual variance packs for multi-property hotel P&L.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    report = subcommands.add_parser(
        "report", help="Build the Excel variance pack for one month."
    )
    report.add_argument(
        "--month",
        required=True,
        metavar="YYYY-MM",
        help="Period to report on, e.g. 2026-06.",
    )

    return parser


def main() -> None:
    """Run the requested command. Exit non-zero if it fails."""
    args = build_parser().parse_args()

    if args.command == "report":
        try:
            path = output_excel(args.month)
        except ValueError as error:
            raise SystemExit(f"bva: {error}")
        print(path)


if __name__ == "__main__":
    main()