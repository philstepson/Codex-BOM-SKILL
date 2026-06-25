#!/usr/bin/env python3
"""Validate the Oracle Cloud BOM workbook structure produced by the builder."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
EXPECTED_HEADERS = [
    "Part",
    "Description",
    "Part Qty",
    "Instance Qty",
    "Usage Qty",
    "Unit Price",
    "Monthly Cost",
    "Custom Label",
    "Discount %",
    "Discounted Monthly Cost",
    "Discounted Annual Cost",
    "Custom Note",
]


def cell_text(cell: ET.Element) -> str:
    formula = cell.find("x:f", NS)
    if formula is not None and formula.text:
        return "=" + formula.text
    inline = cell.find("x:is/x:t", NS)
    if inline is not None and inline.text is not None:
        return inline.text
    value = cell.find("x:v", NS)
    return value.text if value is not None and value.text is not None else ""


def read_sheet(path: Path) -> dict[str, str]:
    with ZipFile(path) as workbook:
        root = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    cells: dict[str, str] = {}
    for cell in root.findall(".//x:c", NS):
        ref = cell.attrib.get("r")
        if ref:
            cells[ref] = cell_text(cell)
    return cells


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an Oracle Cloud BOM workbook.")
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()

    if not args.workbook.exists():
        fail(f"Workbook not found: {args.workbook}")

    cells = read_sheet(args.workbook)
    headers = [cells.get(f"{chr(65 + idx)}6", "") for idx in range(len(EXPECTED_HEADERS))]
    if headers != EXPECTED_HEADERS:
        fail(f"Header row mismatch: {headers}")

    if cells.get("J3") != "Discount %":
        fail("Missing discount label in J3")
    if not cells.get("K3"):
        fail("Missing discount value in K3")
    if not any(value.startswith("=IF(G") and "*(1-IF($K$3>1,$K$3/100,$K$3))" in value for value in cells.values()):
        fail("Missing discounted monthly formula")
    if not any(value.startswith("=IF(J") and "*12" in value for value in cells.values()):
        fail("Missing discounted annual formula")
    if not any(re.fullmatch(r"=SUM\(J\d+:J\d+\)", value) for value in cells.values()):
        fail("Missing discounted monthly total formula")
    if not any(re.fullmatch(r"=SUM\(K\d+:K\d+\)", value) for value in cells.values()):
        fail("Missing discounted annual total formula")
    if "Disclaimer:" not in " ".join(cells.values()):
        fail("Missing estimate disclaimer")

    print(f"PASS: {args.workbook}")


if __name__ == "__main__":
    main()
