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
EXPECTED_WIDE_HEADERS = [
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


def read_text(path: Path, workbook_part: str) -> str:
    with ZipFile(path) as workbook:
        return workbook.read(workbook_part).decode("utf-8")


def workbook_parts(path: Path) -> set[str]:
    with ZipFile(path) as workbook:
        return set(workbook.namelist())


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def is_number(value: object) -> bool:
    if value == "":
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def find_wide_header_row(cells: dict[str, str]) -> int | None:
    for row_num in range(1, 80):
        candidate = [cells.get(f"{chr(65 + idx)}{row_num}", "") for idx in range(4)]
        if candidate == EXPECTED_WIDE_HEADERS:
            return row_num
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an Oracle Cloud BOM workbook.")
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()

    if not args.workbook.exists():
        fail(f"Workbook not found: {args.workbook}")

    cells = read_sheet(args.workbook)
    paas_header_row = find_wide_header_row(cells)
    if paas_header_row is None:
        fail("PAAS wide header row mismatch")
    paas_headers = [cells.get(f"{chr(65 + idx)}{paas_header_row}", "") for idx in range(120)]
    if cells.get("J3") != "Discount %":
        fail("Missing discount label in J3")
    if not cells.get("K3"):
        fail("Missing discount value in K3")
    if "Disc Price" not in paas_headers:
        fail("PAAS sheet missing environment discount columns")
    if "Total Disc Price" not in paas_headers:
        fail("PAAS sheet missing total discount column")
    has_priced_paas_rows = any(
        ref.startswith("D") and ref[1:].isdigit() and int(ref[1:]) > paas_header_row and is_number(value)
        for ref, value in cells.items()
    )
    if has_priced_paas_rows and not any("*(1-IF($K$3>1,$K$3/100,$K$3))" in value for value in cells.values()):
        fail("Missing PAAS discount formula")
    if "Environment Summary" not in cells.values():
        fail("PAAS sheet missing environment summary block")
    if "Disclaimer:" not in " ".join(cells.values()):
        fail("Missing estimate disclaimer")

    parts = workbook_parts(args.workbook)
    if "xl/worksheets/sheet2.xml" not in parts:
        fail("Missing customer-facing BOM worksheet")
    if "xl/worksheets/sheet3.xml" not in parts:
        fail("Missing configured-system summary worksheet")

    customer_cells = read_sheet(args.workbook, "xl/worksheets/sheet2.xml")
    customer_values = set(customer_cells.values())
    customer_header_row = find_wide_header_row(customer_cells)
    if customer_header_row is None:
        fail("Customer BOM header row mismatch")
    customer_headers = [customer_cells.get(f"{chr(65 + idx)}{customer_header_row}", "") for idx in range(80)]
    if "Discount %" in customer_cells.values() or "Disc Price" in customer_cells.values():
        fail("Customer BOM should not expose discount columns")
    if "Customer Note" in customer_cells.values():
        fail("Customer BOM should not expose customer note column")
    if "Environment Summary" not in customer_values:
        fail("Customer BOM missing environment summary block")
    if not any(value == "Qty" for value in customer_headers):
        fail("Customer BOM missing environment quantity columns")
    if not any(value == "List Price" for value in customer_headers):
        fail("Customer BOM missing environment list-price columns")
    if "Total List Price" not in customer_headers:
        fail("Customer BOM missing final total list-price column")
    if "Total One-Time List" not in customer_headers:
        fail("Customer BOM missing final total one-time list-price column")
    if not any(re.fullmatch(r"=SUM\([A-Z]+\d+:[A-Z]+\d+\)", value) for value in customer_cells.values()):
        fail("Customer BOM missing environment summary formulas")
    if "All Environments" not in customer_cells.values():
        fail("Customer BOM missing all-environments total row")
    sheet2_xml = read_text(args.workbook, "xl/worksheets/sheet2.xml")
    auto_filter_index = sheet2_xml.find("<autoFilter")
    merge_cells_index = sheet2_xml.find("<mergeCells")
    page_margins_index = sheet2_xml.find("<pageMargins")
    if merge_cells_index != -1 and auto_filter_index != -1 and merge_cells_index < auto_filter_index:
        fail("Customer BOM XML has mergeCells before autoFilter; Excel may repair sheet2.xml")
    if merge_cells_index != -1 and page_margins_index != -1 and page_margins_index < merge_cells_index:
        fail("Customer BOM XML has pageMargins before mergeCells; Excel may repair sheet2.xml")

    workbook_root = read_xml(args.workbook, "xl/workbook.xml")
    workbook_xml_text = ""
    with ZipFile(args.workbook) as workbook:
        workbook_xml_text = workbook.read("xl/workbook.xml").decode("utf-8")
        rels_xml_text = workbook.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        content_types_text = workbook.read("[Content_Types].xml").decode("utf-8")
    if 'name="Customer BOM"' not in workbook_xml_text:
        fail("Workbook does not register the Customer BOM sheet")
    if 'name="System Summary"' not in workbook_xml_text:
        fail("Workbook does not register the System Summary sheet")
    if 'activeTab="1"' not in workbook_xml_text:
        fail("Workbook does not open on the Customer BOM sheet")
    if 'Target="worksheets/sheet2.xml"' not in rels_xml_text:
        fail("Workbook relationships do not include the Customer BOM sheet")
    if 'Target="worksheets/sheet3.xml"' not in rels_xml_text:
        fail("Workbook relationships do not include the System Summary sheet")
    if 'PartName="/xl/worksheets/sheet2.xml"' not in content_types_text:
        fail("Content types do not include the Customer BOM sheet")
    if 'PartName="/xl/worksheets/sheet3.xml"' not in content_types_text:
        fail("Content types do not include the System Summary sheet")

    summary_cells = read_sheet(args.workbook, "xl/worksheets/sheet3.xml")
    summary_values = set(summary_cells.values())
    required_summary_labels = {
        "Description",
        "Value",
        "Platform",
        "Database servers",
        "Storage servers",
        "Requested ECPUs",
        "Configured ECPU capacity",
        "VM memory GB",
        "Usable storage TB",
        "Basis / notes",
    }
    missing_summary_labels = required_summary_labels - summary_values
    if missing_summary_labels:
        fail(f"System Summary missing labels: {', '.join(sorted(missing_summary_labels))}")
    if "Configured System Summary" not in " ".join(summary_values):
        fail("System Summary missing title")
    if not any(
        summary_cells.get(f"A{row_num}") not in {"", "Description"}
        and summary_cells.get(f"B{row_num}") == ""
        and summary_cells.get(f"A{row_num + 1}") == "Description"
        and summary_cells.get(f"B{row_num + 1}") == "Value"
        for row_num in range(5, 120)
    ):
        fail("System Summary missing vertical environment sections")
    if "Exadata Cloud@Customer X11M" in " ".join(customer_values) and "Exadata Cloud@Customer X11M" not in summary_values:
        fail("System Summary missing Cloud@Customer platform row")
    if "OCI Exadata Dedicated Infrastructure X11M" in " ".join(customer_values) and "OCI Exadata Dedicated Infrastructure X11M" not in summary_values:
        fail("System Summary missing Dedicated Infrastructure platform row")

    calc_pr = workbook_root.find("x:calcPr", NS)
    if calc_pr is None:
        fail("Missing workbook calculation properties")
    if calc_pr.attrib.get("calcMode") != "auto":
        fail("Workbook calculation mode is not automatic")
    if calc_pr.attrib.get("fullCalcOnLoad") != "1" or calc_pr.attrib.get("forceFullCalc") != "1":
        fail("Workbook does not force recalculation on open")

    if not any(re.fullmatch(r"=SUM\([A-Z]+\d+:[A-Z]+\d+\)", value) for value in cells.values()):
        fail("PAAS sheet missing environment summary formulas")

    print(f"PASS: {args.workbook}")


if __name__ == "__main__":
    main()
