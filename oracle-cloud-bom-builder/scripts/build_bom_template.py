#!/usr/bin/env python3
"""Build an Oracle Cloud BOM workbook from estimator-style line items.

This script intentionally uses only the Python standard library. It starts from
the Oracle Cost Estimator sample workbook asset and replaces the worksheet XML
with a discount-enabled BOM layout.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = ROOT / "assets" / "oracle-cost-estimator-sample.xlsx"
DEFAULT_OUTPUT = ROOT / "outputs" / "sample-oracle-cloud-bom.xlsx"


@dataclass(frozen=True)
class BomRow:
    part: str
    description: str
    part_qty: str | int | float = ""
    instance_qty: str | int | float = ""
    usage_qty: str | int | float = ""
    unit_price: str | int | float = ""
    monthly_cost: str | int | float = ""
    custom_label: str = ""
    custom_note: str = ""


@dataclass(frozen=True)
class SupplementalPrice:
    part: str = ""
    description: str = ""
    part_qty: str | int | float = ""
    instance_qty: str | int | float = ""
    usage_qty: str | int | float = ""
    unit_price: str | int | float = ""
    monthly_cost: str | int | float = ""
    source_date: str = ""
    source_note: str = ""


SAMPLE_ROWS = [
    BomRow("", "Exadata Database Service"),
    BomRow(
        "B110629",
        "Exadata Cloud Infrastructure - Storage Server - X11M (Hosted Environment Per Hour)",
        4,
        1,
        744,
        2.9032,
        8639.9232,
    ),
    BomRow(
        "B110627",
        "Exadata Cloud Infrastructure - Database Server - X11M (Hosted Environment Per Hour)",
        3,
        1,
        744,
        2.9032,
        6479.9424,
    ),
    BomRow(
        "B110631",
        "Exadata Database ECPU - Dedicated Infrastructure (ECPU Per Hour)",
        24,
        1,
        744,
        0.336,
        5999.616,
    ),
]


def normalize_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def is_number(value: object) -> bool:
    if value == "":
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def cell(ref: str, value: object = "", formula: str | None = None, style: int | None = None) -> str:
    style_attr = f' s="{style}"' if style is not None else ""
    if formula is not None:
        return f'<c r="{ref}"{style_attr}><f>{html.escape(formula)}</f></c>'
    if value == "":
        return f'<c r="{ref}"{style_attr}/>'
    if is_number(value):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    escaped = html.escape(str(value))
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t>{escaped}</t></is></c>'


def row_xml(row_num: int, values: Iterable[object], styles: dict[int, int] | None = None) -> str:
    styles = styles or {}
    cells = []
    for idx, value in enumerate(values, start=1):
        ref = f"{column_name(idx)}{row_num}"
        cells.append(cell(ref, value, style=styles.get(idx)))
    return f'<row r="{row_num}">{"".join(cells)}</row>'


def load_rows(csv_path: Path | None) -> list[BomRow]:
    if not csv_path:
        return SAMPLE_ROWS

    rows: list[BomRow] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            rows.append(
                BomRow(
                    item.get("Part", ""),
                    item.get("Description", ""),
                    item.get("Part Qty", ""),
                    item.get("Instance Qty", ""),
                    item.get("Usage Qty", ""),
                    item.get("Unit Price", ""),
                    item.get("Monthly Cost", ""),
                    item.get("Custom Label", ""),
                    item.get("Custom Note", ""),
                )
            )
    return rows


def load_supplemental_prices(csv_path: Path | None) -> list[SupplementalPrice]:
    if not csv_path:
        return []

    prices: list[SupplementalPrice] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for item in reader:
            prices.append(
                SupplementalPrice(
                    item.get("Part", ""),
                    item.get("Description", ""),
                    item.get("Part Qty", ""),
                    item.get("Instance Qty", ""),
                    item.get("Usage Qty", ""),
                    item.get("Unit Price", ""),
                    item.get("Monthly Cost", ""),
                    item.get("Source Document Date", "") or item.get("Document Date", ""),
                    item.get("Source Note", ""),
                )
            )
    return prices


def find_supplemental_price(row: BomRow, prices: list[SupplementalPrice]) -> SupplementalPrice | None:
    if row.part:
        row_part = normalize_key(row.part)
        for price in prices:
            if normalize_key(price.part) == row_part:
                return price

    row_desc = normalize_key(row.description)
    if not row_desc:
        return None

    for price in prices:
        price_desc = normalize_key(price.description)
        if price_desc and price_desc == row_desc:
            return price

    for price in prices:
        price_desc = normalize_key(price.description)
        if price_desc and (price_desc in row_desc or row_desc in price_desc):
            return price

    return None


def with_supplemental_pricing(
    rows: list[BomRow],
    prices: list[SupplementalPrice],
    default_source_date: str = "",
) -> list[BomRow]:
    if not prices:
        return rows

    enriched: list[BomRow] = []
    for row in rows:
        has_calculator_price = any(row_value != "" for row_value in [row.unit_price, row.monthly_cost])
        price = find_supplemental_price(row, prices) if not has_calculator_price else None
        if price is None:
            enriched.append(row)
            continue

        source_date = price.source_date or default_source_date
        footnote_parts = ["Pricing sourced from Oracle eSource PDF"]
        if source_date:
            footnote_parts.append(f"document date {source_date}")
        if price.source_note:
            footnote_parts.append(price.source_note)
        source_footnote = "; ".join(footnote_parts) + "."
        custom_note = f"{row.custom_note} {source_footnote}".strip()

        enriched.append(
            BomRow(
                part=row.part or price.part,
                description=row.description or price.description,
                part_qty=row.part_qty or price.part_qty,
                instance_qty=row.instance_qty or price.instance_qty,
                usage_qty=row.usage_qty or price.usage_qty,
                unit_price=price.unit_price,
                monthly_cost=price.monthly_cost,
                custom_label=row.custom_label,
                custom_note=custom_note,
            )
        )
    return enriched


def build_sheet(rows: list[BomRow], discount: float, reference_label: str, currency: str, realm: str, service_type: str) -> str:
    today = date.today().strftime("%m/%d/%Y")
    data_start = 7
    data_end = data_start + len(rows) - 1
    total_row = data_end + 1
    disclaimer_row = total_row + 4

    sheet_rows: list[str] = [
        row_xml(1, [f"Oracle Investment Proposal (as of {today})"]),
        row_xml(2, [f"Reference label: {reference_label}"]),
        row_xml(3, [f"Currency: {currency}", "", "", "", "", "", "", "", "", "Discount %", discount]),
        row_xml(4, [f"Realm: {realm}"]),
        row_xml(5, [f"Service Type: {service_type}"]),
        row_xml(
            6,
            [
                "Part",
                "Description",
                "Part Qty",
                "Instance Qty",
                "Usage Qty",
                "Unit Price",
                "Monthly Cost",
                "Custom Label",
                "Custom Note",
                "Discount %",
                "Discounted Monthly Cost",
                "Discounted Annual Cost",
            ],
        ),
    ]

    for offset, bom in enumerate(rows):
        row_num = data_start + offset
        monthly_formula = None
        monthly_value = bom.monthly_cost
        if monthly_value == "" and all(is_number(v) for v in [bom.part_qty, bom.instance_qty, bom.usage_qty, bom.unit_price]):
            monthly_formula = f'IF(OR(C{row_num}="",D{row_num}="",E{row_num}="",F{row_num}=""),"",C{row_num}*D{row_num}*E{row_num}*F{row_num})'
        cells = [
            cell(f"A{row_num}", bom.part),
            cell(f"B{row_num}", bom.description),
            cell(f"C{row_num}", bom.part_qty),
            cell(f"D{row_num}", bom.instance_qty),
            cell(f"E{row_num}", bom.usage_qty),
            cell(f"F{row_num}", bom.unit_price),
            cell(f"G{row_num}", monthly_value, formula=monthly_formula),
            cell(f"H{row_num}", bom.custom_label),
            cell(f"I{row_num}", bom.custom_note),
            cell(f"J{row_num}", formula="$K$3"),
            cell(f"K{row_num}", formula=f'IF(G{row_num}="","",G{row_num}*(1-$K$3))'),
            cell(f"L{row_num}", formula=f'IF(K{row_num}="","",K{row_num}*12)'),
        ]
        sheet_rows.append(f'<row r="{row_num}">{"".join(cells)}</row>')

    sheet_rows.extend(
        [
            f'<row r="{total_row}">'
            f'{cell(f"B{total_row}", "Monthly Total")}'
            f'{cell(f"G{total_row}", formula=f"SUM(G{data_start}:G{data_end})")}'
            f'{cell(f"J{total_row}", formula="$K$3")}'
            f'{cell(f"K{total_row}", formula=f"SUM(K{data_start}:K{data_end})")}'
            f'{cell(f"L{total_row}", formula=f"SUM(L{data_start}:L{data_end})")}'
            "</row>",
            row_xml(total_row + 2, ["Quote is for investment proposal only."]),
            row_xml(
                disclaimer_row,
                [
                    "Disclaimer: Pricing is an estimate based on Oracle Cost Estimator or user-provided list-price inputs. "
                    "It is not a formal Oracle quote. Validate pricing, terms, discounts, and availability with Oracle before procurement."
                ],
            ),
        ]
    )

    cols = "".join(
        f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>'
        for idx, width in enumerate([16, 72, 12, 14, 12, 12, 14, 20, 28, 12, 22, 22], start=1)
    )
    dimension = f"A1:L{disclaimer_row}"
    sheet_data = "".join(sheet_rows)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="6" topLeftCell="A7" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{cols}</cols>
  <sheetData>{sheet_data}</sheetData>
  <autoFilter ref="A6:L{total_row}"/>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>'''


def write_workbook(template: Path, output: Path, sheet_xml: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(template, "r") as src, ZipFile(output, "w", ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                data = sheet_xml.encode("utf-8")
            dst.writestr(info, data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an Oracle Cloud BOM workbook.")
    parser.add_argument("--input-csv", type=Path, help="Optional CSV with Oracle estimator headers.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--discount", type=float, default=0.15, help="Discount as decimal, e.g. 0.15 for 15%%.")
    parser.add_argument("--reference-label", default="Oracle Cloud BOM")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--realm", default="PUBLIC")
    parser.add_argument("--service-type", default="PAAS")
    parser.add_argument(
        "--supplemental-pricing-csv",
        type=Path,
        help="Optional runtime CSV extracted from the current authenticated Oracle eSource pricing PDF.",
    )
    parser.add_argument(
        "--supplemental-source-date",
        default="",
        help="Document date from the front page of the supplemental Oracle eSource pricing PDF.",
    )
    args = parser.parse_args()

    rows = load_rows(args.input_csv)
    supplemental_prices = load_supplemental_prices(args.supplemental_pricing_csv)
    rows = with_supplemental_pricing(rows, supplemental_prices, args.supplemental_source_date)
    sheet_xml = build_sheet(rows, args.discount, args.reference_label, args.currency, args.realm, args.service_type)
    write_workbook(args.template, args.output, sheet_xml)
    print(args.output)


if __name__ == "__main__":
    main()
