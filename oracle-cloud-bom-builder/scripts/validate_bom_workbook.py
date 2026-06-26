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
EXPECTED_CUSTOMER_HEADERS = [
    "Part",
    "Description",
    "Billing Basis",
    "Unit List Price",
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


def read_sheet(path: Path, workbook_part: str = "xl/worksheets/sheet1.xml") -> dict[str, str]:
    with ZipFile(path) as workbook:
        root = ET.fromstring(workbook.read(workbook_part))
    cells: dict[str, str] = {}
    for cell in root.findall(".//x:c", NS):
        ref = cell.attrib.get("r")
        if ref:
            cells[ref] = cell_text(cell)
    return cells


def read_xml(path: Path, workbook_part: str) -> ET.Element:
    with ZipFile(path) as workbook:
        return ET.fromstring(workbook.read(workbook_part))


def workbook_parts(path: Path) -> set[str]:
    with ZipFile(path) as workbook:
        return set(workbook.namelist())


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

    parts = workbook_parts(args.workbook)
    if "xl/worksheets/sheet2.xml" not in parts:
        fail("Missing customer-facing BOM worksheet")

    customer_cells = read_sheet(args.workbook, "xl/worksheets/sheet2.xml")
    customer_headers = [customer_cells.get(f"{chr(65 + idx)}6", "") for idx in range(80)]
    if customer_headers[:4] != EXPECTED_CUSTOMER_HEADERS:
        fail(f"Customer BOM header row mismatch: {customer_headers}")
    if "Discount %" in customer_cells.values() or "Discounted Monthly Cost" in customer_cells.values():
        fail("Customer BOM should not expose discount columns")
    if not any(str(value).endswith(" Qty") for value in customer_headers):
        fail("Customer BOM missing environment quantity columns")
    if not any(str(value).endswith(" Monthly List") for value in customer_headers):
        fail("Customer BOM missing environment monthly list-price columns")
    if "Total Monthly List" not in customer_headers:
        fail("Customer BOM missing final total monthly list-price column")
    if "Total Annual List" not in customer_headers:
        fail("Customer BOM missing final total annual list-price column")
    if "Total One-Time List" not in customer_headers:
        fail("Customer BOM missing final total one-time list-price column")
    if "Customer Note" not in customer_headers:
        fail("Customer BOM missing customer note column")
    if not any(re.fullmatch(r"=SUM\([A-Z]+\d+:[A-Z]+\d+\)", value) for value in customer_cells.values()):
        fail("Customer BOM missing environment summary formulas")
    if "All Environments Total" not in customer_cells.values():
        fail("Customer BOM missing all-environments total row")

    workbook_root = read_xml(args.workbook, "xl/workbook.xml")
    workbook_xml_text = ""
    with ZipFile(args.workbook) as workbook:
        workbook_xml_text = workbook.read("xl/workbook.xml").decode("utf-8")
        rels_xml_text = workbook.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        content_types_text = workbook.read("[Content_Types].xml").decode("utf-8")
    if 'name="Customer BOM"' not in workbook_xml_text:
        fail("Workbook does not register the Customer BOM sheet")
    if 'Target="worksheets/sheet2.xml"' not in rels_xml_text:
        fail("Workbook relationships do not include the Customer BOM sheet")
    if 'PartName="/xl/worksheets/sheet2.xml"' not in content_types_text:
        fail("Content types do not include the Customer BOM sheet")

    calc_pr = workbook_root.find("x:calcPr", NS)
    if calc_pr is None:
        fail("Missing workbook calculation properties")
    if calc_pr.attrib.get("calcMode") != "auto":
        fail("Workbook calculation mode is not automatic")
    if calc_pr.attrib.get("fullCalcOnLoad") != "1" or calc_pr.attrib.get("forceFullCalc") != "1":
        fail("Workbook does not force recalculation on open")

    sheet_root = read_xml(args.workbook, "xl/worksheets/sheet1.xml")
    for ref in ["J" + ref[1:] for ref, value in cells.items() if value.startswith("=SUM(K")]:
        if ref not in cells:
            fail(f"Missing discounted monthly total paired with annual total at {ref}")
    for ref, value in cells.items():
        if ref.startswith(("J", "K")) and value.startswith("=SUM("):
            cell = sheet_root.find(f".//x:c[@r='{ref}']", NS)
            cached_value = cell.find("x:v", NS) if cell is not None else None
            if cached_value is None or cached_value.text in (None, ""):
                fail(f"Missing cached formula value for total cell {ref}")

    print(f"PASS: {args.workbook}")


if __name__ == "__main__":
    main()
