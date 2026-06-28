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
CURRENCY_NUM_FMT_ID = 164
CURRENCY_NUM_FMT_CODE = '$#,##0'
PERCENT_STYLE_ID = 9
ENVIRONMENT_FILL_COLORS = [
    "C94938",
    "9C918A",
    "6D8F8D",
    "2F5D6B",
    "000000",
    "6F6F6F",
]
SUMMARY_FILL_COLOR = "1F4E79"
DETAIL_FILL_COLOR = "305496"


def discount_formula() -> str:
    return 'IF($K$3>1,$K$3/100,$K$3)'


def sum_formula(refs: Iterable[str]) -> str:
    return f"SUM({','.join(refs)})"


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
    environment: str = ""


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
    BomRow(
        "",
        "Exadata Database Service on Cloud@Customer X11M",
        custom_note="Test BOM baseline: single rack; High redundancy default; license model TBD - choose BYOL or License Included.",
    ),
    BomRow(
        "",
        "Exadata Cloud@Customer X11M Rack - single rack baseline",
        1,
        1,
        "",
        "",
        "",
        "",
        "Each rack should be modeled as prepopulated with 2 database servers.",
    ),
    BomRow(
        "",
        "Exadata Database Service on Cloud@Customer X11M - Database Server",
        2,
        1,
        "",
        "",
        "",
        "",
        "Baseline single-rack configuration includes 2 database servers. Additional database servers increase usable memory and database cores/ECPUs.",
    ),
    BomRow(
        "",
        "Exadata Database Service on Cloud@Customer X11M - Storage Server",
        3,
        1,
        "",
        "",
        "",
        "",
        "Minimum storage-server count is 3. Assumes High redundancy unless Normal redundancy is explicitly specified.",
    ),
    BomRow(
        "",
        "Exadata Database ECPU - Dedicated Infrastructure",
        "",
        1,
        744,
        "",
        "",
        "",
        "Software license model TBD - choose BYOL or License Included before final pricing.",
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


def number_or_none(value: object) -> float | None:
    if not is_number(value):
        return None
    return float(value)


def cached_value(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.10f}".rstrip("0").rstrip(".")


def is_one_time_row(row: BomRow) -> bool:
    text = normalize_key(f"{row.custom_label} {row.custom_note}")
    return "one time" in text or "non metered" in text


def row_monthly_cost(row: BomRow) -> tuple[str | int | float, str | None, float | None]:
    """Return displayed monthly value, optional formula, and initial cached value."""
    monthly_value = row.monthly_cost
    monthly_formula = None
    monthly_cache = number_or_none(monthly_value)
    if monthly_value == "" and all(is_number(v) for v in [row.part_qty, row.instance_qty, row.usage_qty, row.unit_price]):
        monthly_formula = "{part_qty}*{instance_qty}*{usage_qty}*{unit_price}"
        monthly_cache = (
            number_or_none(row.part_qty)
            * number_or_none(row.instance_qty)
            * number_or_none(row.usage_qty)
            * number_or_none(row.unit_price)
        )
    return monthly_value, monthly_formula, monthly_cache


def row_one_time_cost(row: BomRow) -> float | None:
    if is_one_time_row(row) and all(is_number(v) for v in [row.part_qty, row.instance_qty, row.unit_price]):
        return number_or_none(row.part_qty) * number_or_none(row.instance_qty) * number_or_none(row.unit_price)
    return None


def row_customer_quantity(row: BomRow) -> float | str:
    part_qty = number_or_none(row.part_qty)
    instance_qty = number_or_none(row.instance_qty)
    if part_qty is not None and instance_qty is not None:
        return part_qty * instance_qty
    return row.part_qty


def safe_sheet_text(value: object) -> str:
    return str(value).replace('"', '""')


def cell(
    ref: str,
    value: object = "",
    formula: str | None = None,
    style: int | None = None,
    formula_value: object = "",
) -> str:
    style_attr = f' s="{style}"' if style is not None else ""
    if formula is not None:
        value_xml = f"<v>{formula_value}</v>" if formula_value != "" else ""
        return f'<c r="{ref}"{style_attr}><f>{html.escape(formula)}</f>{value_xml}</c>'
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


def currency_style_id(template: Path) -> int:
    with ZipFile(template, "r") as workbook:
        styles = workbook.read("xl/styles.xml").decode("utf-8")
    match = re.search(r'<cellXfs count="(\d+)">', styles)
    if not match:
        raise ValueError(f"Unable to find cellXfs count in template styles: {template}")
    return int(match.group(1))


def workbook_styles_xml(template: Path) -> bytes:
    """Return template styles plus generated BOM presentation styles."""
    with ZipFile(template, "r") as workbook:
        styles = workbook.read("xl/styles.xml").decode("utf-8")

    if f'numFmtId="{CURRENCY_NUM_FMT_ID}"' not in styles:
        num_fmt = (
            f'<numFmts count="1"><numFmt numFmtId="{CURRENCY_NUM_FMT_ID}" '
            f'formatCode="{html.escape(CURRENCY_NUM_FMT_CODE)}"/></numFmts>'
        )
        styles = styles.replace("<fonts ", f"{num_fmt}<fonts ", 1)

    thin_border_id = 0
    if "customerBomStyleFills" not in styles:
        font_match = re.search(r'<fonts count="(\d+)"', styles)
        if not font_match:
            raise ValueError(f"Unable to find fonts count in template styles: {template}")
        white_bold_font_id = int(font_match.group(1))
        white_bold_font = '<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>'
        styles = styles.replace("</fonts>", f"{white_bold_font}</fonts>", 1)
        styles = re.sub(
            r'<fonts count="(\d+)"',
            lambda match: f'<fonts count="{int(match.group(1)) + 1}"',
            styles,
            count=1,
        )
        border_match = re.search(r'<borders count="(\d+)">', styles)
        if not border_match:
            raise ValueError(f"Unable to find borders count in template styles: {template}")
        thin_border_id = int(border_match.group(1))
        thin_border = (
            '<border>'
            '<left style="thin"><color rgb="FFD9E2F3"/></left>'
            '<right style="thin"><color rgb="FFD9E2F3"/></right>'
            '<top style="thin"><color rgb="FFD9E2F3"/></top>'
            '<bottom style="thin"><color rgb="FFD9E2F3"/></bottom>'
            '<diagonal/>'
            '</border>'
        )
        styles = styles.replace("</borders>", f"{thin_border}</borders>", 1)
        styles = re.sub(
            r'<borders count="(\d+)">',
            lambda match: f'<borders count="{int(match.group(1)) + 1}">',
            styles,
            count=1,
        )

    if f'numFmtId="{CURRENCY_NUM_FMT_ID}" fontId="0"' not in styles:
        styles = re.sub(
            r'<cellXfs count="(\d+)">',
            lambda match: f'<cellXfs count="{int(match.group(1)) + 1}">',
            styles,
            count=1,
        )
        currency_xf = (
            f'<xf numFmtId="{CURRENCY_NUM_FMT_ID}" fontId="0" fillId="0" borderId="{thin_border_id}" '
            'xfId="0" applyNumberFormat="1" applyBorder="1"/>'
        )
        styles = styles.replace("</cellXfs>", f"{currency_xf}</cellXfs>", 1)

    if "customerBomStyleFills" not in styles:
        fill_colors = [SUMMARY_FILL_COLOR, DETAIL_FILL_COLOR, *ENVIRONMENT_FILL_COLORS]
        fill_xml = "".join(
            f'<fill><patternFill patternType="solid"><fgColor rgb="FF{color}"/><bgColor indexed="64"/></patternFill></fill>'
            for color in fill_colors
        )
        styles = styles.replace("</fills>", f"{fill_xml}</fills>", 1)
        styles = re.sub(
            r'<fills count="(\d+)">',
            lambda match: f'<fills count="{int(match.group(1)) + len(fill_colors)}">',
            styles,
            count=1,
        )
        existing_fill_count = 2
        summary_fill_id = existing_fill_count
        detail_fill_id = existing_fill_count + 1
        env_fill_start = existing_fill_count + 2
        customer_xfs = [
            f'<xf numFmtId="0" fontId="{white_bold_font_id}" fillId="{summary_fill_id}" borderId="{thin_border_id}" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>',
            f'<xf numFmtId="0" fontId="{white_bold_font_id}" fillId="{detail_fill_id}" borderId="{thin_border_id}" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>',
        ]
        for fill_id in range(env_fill_start, env_fill_start + len(ENVIRONMENT_FILL_COLORS)):
            customer_xfs.append(
                f'<xf numFmtId="0" fontId="{white_bold_font_id}" fillId="{fill_id}" borderId="{thin_border_id}" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>'
            )
        customer_xfs.extend(
            [
                f'<xf numFmtId="{CURRENCY_NUM_FMT_ID}" fontId="{white_bold_font_id}" fillId="{summary_fill_id}" borderId="{thin_border_id}" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1"/>',
                f'<xf numFmtId="0" fontId="0" fillId="0" borderId="{thin_border_id}" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>',
            ]
        )
        styles = re.sub(
            r'<cellXfs count="(\d+)">',
            lambda match: f'<cellXfs count="{int(match.group(1)) + len(customer_xfs)}">',
            styles,
            count=1,
        )
        styles = styles.replace("</cellXfs>", f"{''.join(customer_xfs)}</cellXfs>", 1)
        styles = styles.replace("</styleSheet>", "<!-- customerBomStyleFills --></styleSheet>", 1)

    return styles.encode("utf-8")


def workbook_xml(template: Path) -> bytes:
    with ZipFile(template, "r") as workbook:
        workbook_xml_text = workbook.read("xl/workbook.xml").decode("utf-8")

    calc_pr = '<calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/>'
    if "<calcPr" in workbook_xml_text:
        workbook_xml_text = re.sub(r"<calcPr[^>]*/>", calc_pr, workbook_xml_text, count=1)
    else:
        workbook_xml_text = workbook_xml_text.replace("</workbook>", f"{calc_pr}</workbook>", 1)

    return workbook_xml_text.encode("utf-8")


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
                    item.get("Environment", "") or item.get("Env", ""),
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
                environment=row.environment,
            )
        )
    return enriched


def build_wide_environment_sheet(
    rows: list[BomRow],
    discount: float,
    reference_label: str,
    currency: str,
    realm: str,
    currency_style: int,
    include_discount: bool,
    selected: bool = False,
) -> str:
    today = date.today().strftime("%m/%d/%Y")
    normalized_discount = discount / 100 if discount > 1 else discount
    customer_rows = [row for row in rows if row.part]
    environments: list[str] = []
    for row in customer_rows:
        environment = row.environment or "General"
        if environment not in environments:
            environments.append(environment)
    if not environments:
        environments = ["General"]

    def billing_basis(row: BomRow) -> str:
        if row_one_time_cost(row) is not None and row_monthly_cost(row)[2] is None:
            return "One-time"
        if row_monthly_cost(row)[2] is not None or row_monthly_cost(row)[1] is not None:
            return "Recurring usage"
        return ""

    grouped: dict[tuple[str, str, str, str], dict[str, BomRow]] = {}
    order: list[tuple[str, str, str, str]] = []
    for row in customer_rows:
        key = (row.part, row.description, str(row.unit_price), billing_basis(row))
        if key not in grouped:
            grouped[key] = {}
            order.append(key)
        grouped[key][row.environment or "General"] = row

    summary_style = currency_style + 1
    detail_style = currency_style + 2
    env_style_start = currency_style + 3
    total_style = env_style_start + len(ENVIRONMENT_FILL_COLORS) - 1
    summary_currency_style = total_style + 1
    body_style = summary_currency_style + 1
    base_cols = 4
    env_width = 8 if include_discount else 5
    total_width = 7 if include_discount else 4
    group_header_row = 5
    table_header_row = 6
    data_start = 7
    data_end = data_start + len(order) - 1
    summary_header_row = data_end + 2
    summary_start = summary_header_row + 1
    all_summary_row = summary_start + len(environments)
    note_row = all_summary_row + 2
    disclaimer_row = note_row + 2
    total_col_start = base_cols + 1 + (len(environments) * env_width)
    last_col = total_col_start + total_width - 1

    title = "Oracle Investment Proposal" if include_discount else "Customer BOM"
    top_rows = [
        row_xml(1, [f"{title} (as of {today})"]),
        row_xml(2, [f"Reference label: {reference_label}"]),
        row_xml(3, [f"Currency: {currency}", "", "", "", "", "", "", "", "", "Discount %", discount] if include_discount else [f"Currency: {currency}"], {11: PERCENT_STYLE_ID} if include_discount else None),
        row_xml(4, [f"Realm: {realm}"]),
    ]

    group_cells = [
        cell(f"A{group_header_row}", "SKU Detail", style=detail_style),
        cell(f"B{group_header_row}", "", style=detail_style),
        cell(f"C{group_header_row}", "", style=detail_style),
        cell(f"D{group_header_row}", "", style=detail_style),
    ]
    header_cells = [
        cell(f"A{table_header_row}", "Part", style=detail_style),
        cell(f"B{table_header_row}", "Description", style=detail_style),
        cell(f"C{table_header_row}", "Billing Basis", style=detail_style),
        cell(f"D{table_header_row}", "Unit List Price", style=detail_style),
    ]
    for env_index, environment in enumerate(environments):
        start_col = base_cols + 1 + (env_index * env_width)
        env_style = env_style_start + (env_index % (len(ENVIRONMENT_FILL_COLORS) - 1))
        group_cells.append(cell(f"{column_name(start_col)}{group_header_row}", environment, style=env_style))
        group_cells.extend(cell(f"{column_name(start_col + offset)}{group_header_row}", "", style=env_style) for offset in range(1, env_width))
        labels = ["Qty", "Hrs", "Monthly List", "Annual List"]
        if include_discount:
            labels.extend(["Monthly Disc", "Annual Disc"])
        labels.extend(["One-Time List", "One-Time Disc"] if include_discount else ["One-Time List"])
        for offset, label in enumerate(labels):
            header_cells.append(cell(f"{column_name(start_col + offset)}{table_header_row}", label, style=env_style))
    group_cells.append(cell(f"{column_name(total_col_start)}{group_header_row}", "All Environments", style=total_style))
    group_cells.extend(cell(f"{column_name(total_col_start + offset)}{group_header_row}", "", style=total_style) for offset in range(1, total_width))
    total_labels = ["Total Qty", "Total Monthly List", "Total Annual List"]
    if include_discount:
        total_labels.extend(["Total Monthly Disc", "Total Annual Disc"])
    total_labels.extend(["Total One-Time List", "Total One-Time Disc"] if include_discount else ["Total One-Time List"])
    for offset, label in enumerate(total_labels):
        header_cells.append(cell(f"{column_name(total_col_start + offset)}{table_header_row}", label, style=total_style))

    env_totals = {
        env: {"monthly": 0.0, "annual": 0.0, "monthly_disc": 0.0, "annual_disc": 0.0, "one_list": 0.0, "one_disc": 0.0}
        for env in environments
    }
    all_totals = {"monthly": 0.0, "annual": 0.0, "monthly_disc": 0.0, "annual_disc": 0.0, "one_list": 0.0, "one_disc": 0.0}
    data_rows: list[str] = []

    for offset, key in enumerate(order):
        row_num = data_start + offset
        part, description, unit_price, basis = key
        cells = [
            cell(f"A{row_num}", part, style=body_style),
            cell(f"B{row_num}", description, style=body_style),
            cell(f"C{row_num}", basis, style=body_style),
            cell(f"D{row_num}", unit_price, style=body_style),
        ]
        qty_cols: list[str] = []
        monthly_cols: list[str] = []
        annual_cols: list[str] = []
        monthly_disc_cols: list[str] = []
        annual_disc_cols: list[str] = []
        one_list_cols: list[str] = []
        one_disc_cols: list[str] = []
        row_totals = {"qty": 0.0, "monthly": 0.0, "annual": 0.0, "monthly_disc": 0.0, "annual_disc": 0.0, "one_list": 0.0, "one_disc": 0.0}

        for env_index, environment in enumerate(environments):
            env_row = grouped[key].get(environment)
            start_col = base_cols + 1 + (env_index * env_width)
            qty_col = column_name(start_col)
            hrs_col = column_name(start_col + 1)
            monthly_col = column_name(start_col + 2)
            annual_col = column_name(start_col + 3)
            monthly_disc_col = column_name(start_col + 4) if include_discount else ""
            annual_disc_col = column_name(start_col + 5) if include_discount else ""
            one_list_col = column_name(start_col + (6 if include_discount else 4))
            one_disc_col = column_name(start_col + 7) if include_discount else ""
            qty_cols.append(qty_col)
            monthly_cols.append(monthly_col)
            annual_cols.append(annual_col)
            if include_discount:
                monthly_disc_cols.append(monthly_disc_col)
                annual_disc_cols.append(annual_disc_col)
            one_list_cols.append(one_list_col)
            if include_discount:
                one_disc_cols.append(one_disc_col)

            if env_row is None:
                empty_count = env_width
                cells.extend(cell(f"{column_name(start_col + i)}{row_num}", "", style=currency_style if i >= 2 else body_style) for i in range(empty_count))
                continue

            quantity = row_customer_quantity(env_row)
            qty_num = number_or_none(quantity)
            if qty_num is not None:
                row_totals["qty"] += qty_num
            monthly_value, monthly_formula_template, monthly_cache = row_monthly_cost(env_row)
            annual_cache = monthly_cache * 12 if monthly_cache is not None else None
            one_time_cache = row_one_time_cost(env_row)
            is_one_time = one_time_cache is not None and monthly_cache is None
            monthly_formula = None
            if monthly_formula_template is not None:
                monthly_formula = f'IF(OR({qty_col}{row_num}="",{hrs_col}{row_num}="",$D{row_num}=""),"",{qty_col}{row_num}*{hrs_col}{row_num}*$D{row_num})'
            annual_formula = f'IF({monthly_col}{row_num}="","",{monthly_col}{row_num}*12)' if monthly_cache is not None or monthly_formula is not None else None
            monthly_disc_formula = f'IF({monthly_col}{row_num}="","",{monthly_col}{row_num}*(1-{discount_formula()}))' if include_discount else None
            annual_disc_formula = f'IF({annual_col}{row_num}="","",{annual_col}{row_num}*(1-{discount_formula()}))' if include_discount else None
            monthly_disc_cache = monthly_cache * (1 - normalized_discount) if monthly_cache is not None else None
            annual_disc_cache = annual_cache * (1 - normalized_discount) if annual_cache is not None else None
            one_list_formula = None
            one_disc_formula = None
            if is_one_time:
                one_list_formula = f'IF(OR({qty_col}{row_num}="",$D{row_num}=""),"",{qty_col}{row_num}*$D{row_num})'
                if include_discount:
                    one_disc_formula = f'IF({one_list_col}{row_num}="","",{one_list_col}{row_num}*(1-{discount_formula()}))'
            else:
                one_time_cache = None
            one_disc_cache = one_time_cache * (1 - normalized_discount) if one_time_cache is not None else None

            row_totals["monthly"] += monthly_cache or 0.0
            row_totals["annual"] += annual_cache or 0.0
            row_totals["monthly_disc"] += monthly_disc_cache or 0.0
            row_totals["annual_disc"] += annual_disc_cache or 0.0
            row_totals["one_list"] += one_time_cache or 0.0
            row_totals["one_disc"] += one_disc_cache or 0.0
            env_totals[environment]["monthly"] += monthly_cache or 0.0
            env_totals[environment]["annual"] += annual_cache or 0.0
            env_totals[environment]["monthly_disc"] += monthly_disc_cache or 0.0
            env_totals[environment]["annual_disc"] += annual_disc_cache or 0.0
            env_totals[environment]["one_list"] += one_time_cache or 0.0
            env_totals[environment]["one_disc"] += one_disc_cache or 0.0
            cells.extend(
                [
                    cell(f"{qty_col}{row_num}", quantity, style=body_style),
                    cell(f"{hrs_col}{row_num}", env_row.usage_qty, style=body_style),
                    cell(f"{monthly_col}{row_num}", monthly_value if monthly_formula is None else "", formula=monthly_formula, style=currency_style, formula_value=cached_value(monthly_cache)),
                    cell(f"{annual_col}{row_num}", formula=annual_formula, style=currency_style, formula_value=cached_value(annual_cache)),
                ]
            )
            if include_discount:
                cells.append(cell(f"{monthly_disc_col}{row_num}", formula=monthly_disc_formula, style=currency_style, formula_value=cached_value(monthly_disc_cache)))
                cells.append(cell(f"{annual_disc_col}{row_num}", formula=annual_disc_formula, style=currency_style, formula_value=cached_value(annual_disc_cache)))
            cells.append(cell(f"{one_list_col}{row_num}", formula=one_list_formula, style=currency_style, formula_value=cached_value(one_time_cache)))
            if include_discount:
                cells.append(cell(f"{one_disc_col}{row_num}", formula=one_disc_formula, style=currency_style, formula_value=cached_value(one_disc_cache)))

        total_cells = [
            cell(f"{column_name(total_col_start)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in qty_cols), style=body_style, formula_value=cached_value(row_totals["qty"])),
            cell(f"{column_name(total_col_start + 1)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in monthly_cols), style=currency_style, formula_value=cached_value(row_totals["monthly"])),
            cell(f"{column_name(total_col_start + 2)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in annual_cols), style=currency_style, formula_value=cached_value(row_totals["annual"])),
        ]
        next_offset = 3
        if include_discount:
            total_cells.append(cell(f"{column_name(total_col_start + next_offset)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in monthly_disc_cols), style=currency_style, formula_value=cached_value(row_totals["monthly_disc"])))
            next_offset += 1
            total_cells.append(cell(f"{column_name(total_col_start + next_offset)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in annual_disc_cols), style=currency_style, formula_value=cached_value(row_totals["annual_disc"])))
            next_offset += 1
        total_cells.append(cell(f"{column_name(total_col_start + next_offset)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in one_list_cols), style=currency_style, formula_value=cached_value(row_totals["one_list"])))
        next_offset += 1
        if include_discount:
            total_cells.append(cell(f"{column_name(total_col_start + next_offset)}{row_num}", formula=sum_formula(f"{col}{row_num}" for col in one_disc_cols), style=currency_style, formula_value=cached_value(row_totals["one_disc"])))
        cells.extend(total_cells)
        all_totals["monthly"] += row_totals["monthly"]
        all_totals["annual"] += row_totals["annual"]
        all_totals["monthly_disc"] += row_totals["monthly_disc"]
        all_totals["annual_disc"] += row_totals["annual_disc"]
        all_totals["one_list"] += row_totals["one_list"]
        all_totals["one_disc"] += row_totals["one_disc"]
        data_rows.append(f'<row r="{row_num}">{"".join(cells)}</row>')

    summary_rows = [
        f'<row r="{summary_header_row}">{cell(f"A{summary_header_row}", "Environment Summary", style=summary_style)}</row>'
    ]
    for env_index, environment in enumerate(environments):
        row_num = summary_start + env_index
        start_col = base_cols + 1 + (env_index * env_width)
        monthly_col = column_name(start_col + 2)
        annual_col = column_name(start_col + 3)
        monthly_disc_col = column_name(start_col + 4) if include_discount else ""
        annual_disc_col = column_name(start_col + 5) if include_discount else ""
        one_list_col = column_name(start_col + (6 if include_discount else 4))
        one_disc_col = column_name(start_col + 7) if include_discount else ""
        cells = [cell(f"A{row_num}", f"{environment} Total", style=summary_style)]
        cells.append(cell(f"{monthly_col}{row_num}", formula=f"SUM({monthly_col}{data_start}:{monthly_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["monthly"])))
        cells.append(cell(f"{annual_col}{row_num}", formula=f"SUM({annual_col}{data_start}:{annual_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["annual"])))
        if include_discount:
            cells.append(cell(f"{monthly_disc_col}{row_num}", formula=f"SUM({monthly_disc_col}{data_start}:{monthly_disc_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["monthly_disc"])))
            cells.append(cell(f"{annual_disc_col}{row_num}", formula=f"SUM({annual_disc_col}{data_start}:{annual_disc_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["annual_disc"])))
        cells.append(cell(f"{one_list_col}{row_num}", formula=f"SUM({one_list_col}{data_start}:{one_list_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["one_list"])))
        if include_discount:
            cells.append(cell(f"{one_disc_col}{row_num}", formula=f"SUM({one_disc_col}{data_start}:{one_disc_col}{data_end})", style=summary_currency_style, formula_value=cached_value(env_totals[environment]["one_disc"])))
        summary_rows.append(f'<row r="{row_num}">{"".join(cells)}</row>')
    all_cells = [cell(f"A{all_summary_row}", "All Environments Total", style=total_style)]
    all_cells.append(cell(f"{column_name(total_col_start + 1)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + 1)}{data_start}:{column_name(total_col_start + 1)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["monthly"])))
    all_cells.append(cell(f"{column_name(total_col_start + 2)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + 2)}{data_start}:{column_name(total_col_start + 2)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["annual"])))
    offset = 3
    if include_discount:
        all_cells.append(cell(f"{column_name(total_col_start + offset)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + offset)}{data_start}:{column_name(total_col_start + offset)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["monthly_disc"])))
        offset += 1
        all_cells.append(cell(f"{column_name(total_col_start + offset)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + offset)}{data_start}:{column_name(total_col_start + offset)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["annual_disc"])))
        offset += 1
    all_cells.append(cell(f"{column_name(total_col_start + offset)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + offset)}{data_start}:{column_name(total_col_start + offset)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["one_list"])))
    offset += 1
    if include_discount:
        all_cells.append(cell(f"{column_name(total_col_start + offset)}{all_summary_row}", formula=f"SUM({column_name(total_col_start + offset)}{data_start}:{column_name(total_col_start + offset)}{data_end})", style=summary_currency_style, formula_value=cached_value(all_totals["one_disc"])))
    summary_rows.append(f'<row r="{all_summary_row}">{"".join(all_cells)}</row>')

    sheet_rows = [
        *top_rows,
        f'<row r="{group_header_row}">{"".join(group_cells)}</row>',
        f'<row r="{table_header_row}">{"".join(header_cells)}</row>',
        *data_rows,
        *summary_rows,
        row_xml(note_row, ["Customer-facing view shows list prices only." if not include_discount else "Working view includes discount calculations."]),
        row_xml(disclaimer_row, ["Disclaimer: Pricing is an estimate based on Oracle Cost Estimator or user-provided list-price inputs. It is not a formal Oracle quote. Validate pricing, terms, discounts, and availability with Oracle before procurement."]),
    ]
    widths = [16, 72, 18, 16] + (([12, 12, 18, 18, 18, 18, 18, 18] if include_discount else [12, 12, 18, 18, 18]) * len(environments)) + ([12, 20, 20, 20, 20, 20, 20] if include_discount else [12, 20, 20, 20])
    cols = "".join(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>' for idx, width in enumerate(widths, start=1))
    dimension = f"A1:{column_name(last_col)}{disclaimer_row}"
    sheet_data = "".join(sheet_rows)
    merge_refs = [f"A{group_header_row}:D{group_header_row}"]
    for env_index in range(len(environments)):
        start_col = base_cols + 1 + (env_index * env_width)
        merge_refs.append(f"{column_name(start_col)}{group_header_row}:{column_name(start_col + env_width - 1)}{group_header_row}")
    merge_refs.append(f"{column_name(total_col_start)}{group_header_row}:{column_name(total_col_start + total_width - 1)}{group_header_row}")
    merges = f'<mergeCells count="{len(merge_refs)}">' + "".join(f'<mergeCell ref="{ref}"/>' for ref in merge_refs) + "</mergeCells>"
    tab_selected = ' tabSelected="1"' if selected else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews><sheetView workbookViewId="0"{tab_selected}><pane ySplit="{table_header_row}" topLeftCell="A{data_start}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{cols}</cols>
  <sheetData>{sheet_data}</sheetData>
  <autoFilter ref="A{table_header_row}:{column_name(last_col)}{data_end}"/>
  {merges}
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>'''


def build_sheet(
    rows: list[BomRow],
    discount: float,
    reference_label: str,
    currency: str,
    realm: str,
    service_type: str,
    currency_style: int,
) -> str:
    return build_wide_environment_sheet(
        rows,
        discount,
        reference_label,
        currency,
        realm,
        currency_style,
        include_discount=True,
    )

    today = date.today().strftime("%m/%d/%Y")
    normalized_discount = discount / 100 if discount > 1 else discount
    data_start = 7
    data_end = data_start + len(rows) - 1
    total_row = data_end + 1
    disclaimer_row = total_row + 4
    monthly_caches: list[float | None] = []
    discounted_monthly_caches: list[float | None] = []
    annual_caches: list[float | None] = []

    sheet_rows: list[str] = [
        row_xml(1, [f"Oracle Investment Proposal (as of {today})"]),
        row_xml(2, [f"Reference label: {reference_label}"]),
        row_xml(3, [f"Currency: {currency}", "", "", "", "", "", "", "", "", "Discount %", discount], {11: PERCENT_STYLE_ID}),
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
                "Discount %",
                "Discounted Monthly Cost",
                "Discounted Annual Cost",
                "Custom Note",
            ],
        ),
    ]

    for offset, bom in enumerate(rows):
        row_num = data_start + offset
        monthly_value, monthly_formula_template, monthly_cache = row_monthly_cost(bom)
        monthly_formula = None
        if monthly_formula_template is not None:
            monthly_formula = f'IF(OR(C{row_num}="",D{row_num}="",E{row_num}="",F{row_num}=""),"",C{row_num}*D{row_num}*E{row_num}*F{row_num})'
        discounted_monthly_cache = (
            monthly_cache * (1 - normalized_discount) if monthly_cache is not None else None
        )
        annual_formula = f'IF(J{row_num}="","",J{row_num}*12)'
        annual_cache = (
            discounted_monthly_cache * 12 if discounted_monthly_cache is not None else None
        )
        if (
            monthly_value == ""
            and monthly_formula is None
            and is_one_time_row(bom)
            and all(is_number(v) for v in [bom.part_qty, bom.instance_qty, bom.unit_price])
        ):
            annual_formula = (
                f'IF(OR(C{row_num}="",D{row_num}="",F{row_num}=""),"",'
                f"C{row_num}*D{row_num}*F{row_num}*(1-{discount_formula()}))"
            )
            annual_cache = (
                row_one_time_cost(bom)
                * (1 - normalized_discount)
            )
        monthly_caches.append(monthly_cache)
        discounted_monthly_caches.append(discounted_monthly_cache)
        annual_caches.append(annual_cache)
        cells = [
            cell(f"A{row_num}", bom.part),
            cell(f"B{row_num}", bom.description),
            cell(f"C{row_num}", bom.part_qty),
            cell(f"D{row_num}", bom.instance_qty),
            cell(f"E{row_num}", bom.usage_qty),
            cell(f"F{row_num}", bom.unit_price),
            cell(f"G{row_num}", monthly_value, formula=monthly_formula, style=currency_style, formula_value=cached_value(monthly_cache)),
            cell(f"H{row_num}", bom.custom_label),
            cell(f"I{row_num}", formula=discount_formula(), style=PERCENT_STYLE_ID, formula_value=cached_value(normalized_discount)),
            cell(f"J{row_num}", formula=f'IF(G{row_num}="","",G{row_num}*(1-{discount_formula()}))', style=currency_style, formula_value=cached_value(discounted_monthly_cache)),
            cell(f"K{row_num}", formula=annual_formula, style=currency_style, formula_value=cached_value(annual_cache)),
            cell(f"L{row_num}", bom.custom_note),
        ]
        sheet_rows.append(f'<row r="{row_num}">{"".join(cells)}</row>')

    monthly_total_cache = sum(value for value in monthly_caches if value is not None)
    discounted_monthly_total_cache = sum(value for value in discounted_monthly_caches if value is not None)
    annual_total_cache = sum(value for value in annual_caches if value is not None)

    sheet_rows.extend(
        [
            f'<row r="{total_row}">'
            f'{cell(f"B{total_row}", "Monthly Total")}'
            f'{cell(f"G{total_row}", formula=f"SUM(G{data_start}:G{data_end})", style=currency_style, formula_value=cached_value(monthly_total_cache))}'
            f'{cell(f"I{total_row}", formula=discount_formula(), style=PERCENT_STYLE_ID, formula_value=cached_value(normalized_discount))}'
            f'{cell(f"J{total_row}", formula=f"SUM(J{data_start}:J{data_end})", style=currency_style, formula_value=cached_value(discounted_monthly_total_cache))}'
            f'{cell(f"K{total_row}", formula=f"SUM(K{data_start}:K{data_end})", style=currency_style, formula_value=cached_value(annual_total_cache))}'
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

    col_xml = []
    for idx, width in enumerate([16, 72, 12, 14, 12, 12, 14, 20, 12, 22, 22, 28], start=1):
        hidden_attr = ' hidden="1"' if idx == 12 else ""
        col_xml.append(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"{hidden_attr}/>')
    cols = "".join(col_xml)
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


def build_customer_sheet(
    rows: list[BomRow],
    reference_label: str,
    currency: str,
    realm: str,
    currency_style: int,
) -> str:
    return build_wide_environment_sheet(
        rows,
        0,
        reference_label,
        currency,
        realm,
        currency_style,
        include_discount=False,
        selected=True,
    )


def env_row_groups(rows: list[BomRow]) -> dict[str, list[BomRow]]:
    groups: dict[str, list[BomRow]] = {}
    for row in rows:
        environment = row.environment or "General"
        groups.setdefault(environment, []).append(row)
    return groups


def row_quantity(row: BomRow) -> float | None:
    part_qty = number_or_none(row.part_qty)
    instance_qty = number_or_none(row.instance_qty)
    if part_qty is None:
        return None
    if instance_qty is None:
        return part_qty
    return part_qty * instance_qty


def configured_system_summary_rows(rows: list[BomRow]) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    for environment, env_rows in env_row_groups(rows).items():
        text = " ".join(
            f"{row.part} {row.description} {row.custom_label} {row.custom_note}".lower()
            for row in env_rows
        )
        is_cac = "cloud@customer" in text or "cloud at customer" in text or "c@c" in text
        is_dedicated = "dedicated infrastructure" in text or "cloud infrastructure" in text
        is_autonomous = "autonomous" in text
        if not is_cac and not is_dedicated:
            continue

        rack_count = 0.0
        db_servers = 0.0
        storage_servers = 0.0
        requested_ecpus = 0.0
        license_model = ""
        storage_type = "High Capacity" if "high capacity" in text or "storage server - x11m" in text else ""
        db_type = "Base" if is_cac and "base system" in text else "X11M"
        if is_cac:
            platform = "Exadata Cloud@Customer X11M"
        elif is_autonomous:
            platform = "Autonomous Database on Dedicated Exadata Infrastructure X11M"
        else:
            platform = "OCI Exadata Dedicated Infrastructure X11M"

        for row in env_rows:
            description = row.description.lower()
            note = row.custom_note.lower()
            qty = row_quantity(row) or 0.0
            if "base system rack" in description:
                rack_count += qty or 1.0
            if "database server" in description and row.part:
                db_servers += qty
            if "storage server" in description and row.part:
                storage_servers += qty
            if "ecpu" in description and row.part:
                requested_ecpus += qty
                custom_label = row.custom_label.lower()
                if "byol" in description or "byol" in note or custom_label == "byol":
                    license_model = "BYOL"
                elif "license included" in description or "license included" in note or custom_label == "license included":
                    license_model = "License Included"

        if is_cac and rack_count and not db_servers:
            db_servers = rack_count * 2
        if not rack_count and (db_servers or storage_servers):
            rack_count = 1.0

        if is_cac:
            db_cores_per_server = 30 if db_type == "Base" else 190
            ecpu_capacity_per_server = 120 if db_type == "Base" else 760
            memory_per_server_gb = 660 if db_type == "Base" else 1390
            max_vm_clusters = 12 if db_servers <= 2 else 24
            redundancy = "High"
            platform_note = "Cloud@Customer summary uses datasheet values; Base DB servers assumed when Base System Rack is present."
        else:
            db_cores_per_server = 190
            ecpu_capacity_per_server = 760
            memory_per_server_gb = 1390
            max_vm_clusters = 8
            redundancy = "High"
            platform_note = "Dedicated Infrastructure summary uses X11M elastic datasheet values and calculator row counts."
            if is_autonomous:
                platform_note = "Autonomous Database dedicated deployment uses Dedicated Exadata X11M infrastructure sizing values and calculator row counts."

        storage_usable_tb = 80.0 if storage_type == "High Capacity" or is_dedicated else 0.0
        xrmem_per_storage_tb = 1.25 if storage_usable_tb else 0.0
        flash_cache_per_storage_tb = 27.2 if storage_usable_tb else 0.0

        summaries.append(
            {
                "environment": environment,
                "platform": platform,
                "racks": rack_count,
                "db_type": db_type,
                "db_servers": db_servers,
                "storage_type": storage_type or "X11M Storage",
                "storage_servers": storage_servers,
                "requested_ecpus": requested_ecpus,
                "configured_ecpus": db_servers * ecpu_capacity_per_server,
                "db_cores": db_servers * db_cores_per_server,
                "memory_gb": db_servers * memory_per_server_gb,
                "usable_storage_tb": storage_servers * storage_usable_tb,
                "xrmem_tb": storage_servers * xrmem_per_storage_tb,
                "flash_cache_tb": storage_servers * flash_cache_per_storage_tb,
                "max_vm_clusters": max_vm_clusters,
                "redundancy": redundancy,
                "license_model": license_model or "TBD",
                "notes": platform_note,
            }
        )
    return summaries


def build_system_summary_sheet(
    rows: list[BomRow],
    reference_label: str,
    currency_style: int,
) -> str:
    today = date.today().strftime("%m/%d/%Y")
    summary_style = currency_style + 1
    detail_style = currency_style + 2
    body_style = currency_style + len(ENVIRONMENT_FILL_COLORS) + 4
    summaries = configured_system_summary_rows(rows)
    sheet_rows = [
        row_xml(1, [f"Configured System Summary (as of {today})"]),
        row_xml(2, [f"Reference label: {reference_label}"]),
        row_xml(3, ["Source: generated from BOM rows plus Exadata X11M datasheet reference values. Pricing fields remain on PAAS and Customer BOM sheets."]),
    ]

    current_row = 5
    first_heading_row = current_row
    characteristic_rows = [
        ("Platform", "platform"),
        ("Racks", "racks"),
        ("Database server type", "db_type"),
        ("Database servers", "db_servers"),
        ("Storage server type", "storage_type"),
        ("Storage servers", "storage_servers"),
        ("Requested ECPUs", "requested_ecpus"),
        ("Configured ECPU capacity", "configured_ecpus"),
        ("Usable database cores", "db_cores"),
        ("VM memory GB", "memory_gb"),
        ("Usable storage TB", "usable_storage_tb"),
        ("XRMEM TB", "xrmem_tb"),
        ("Flash cache TB", "flash_cache_tb"),
        ("Max VM clusters", "max_vm_clusters"),
        ("Storage redundancy", "redundancy"),
        ("License model", "license_model"),
        ("Basis / notes", "notes"),
    ]
    if summaries:
        for item in summaries:
            sheet_rows.append(
                f'<row r="{current_row}">'
                f'{cell(f"A{current_row}", item["environment"], style=summary_style)}'
                f'{cell(f"B{current_row}", "", style=summary_style)}'
                "</row>"
            )
            current_row += 1
            sheet_rows.append(
                f'<row r="{current_row}">'
                f'{cell(f"A{current_row}", "Description", style=detail_style)}'
                f'{cell(f"B{current_row}", "Value", style=detail_style)}'
                "</row>"
            )
            current_row += 1
            for label, key in characteristic_rows:
                sheet_rows.append(
                    f'<row r="{current_row}">'
                    f'{cell(f"A{current_row}", label, style=body_style)}'
                    f'{cell(f"B{current_row}", item[key], style=body_style)}'
                    "</row>"
                )
                current_row += 1
            current_row += 1
    else:
        sheet_rows.append(row_xml(current_row, ["No configured Exadata system rows were detected in the BOM input."], {1: body_style}))
        current_row += 1

    note_row = current_row + 1
    sheet_rows.append(
        row_xml(
            note_row,
            [
                "Capacity values are technical sizing references, not prices. Validate server model, redundancy, local-backup assumptions, and workload requirements before procurement."
            ],
        )
    )

    last_col = 2
    widths = [34, 88]
    cols = "".join(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>' for idx, width in enumerate(widths, start=1))
    dimension = f"A1:{column_name(last_col)}{note_row}"
    sheet_data = "".join(sheet_rows)
    merge_refs = []
    if summaries:
        row_num = first_heading_row
        for _item in summaries:
            merge_refs.append(f"A{row_num}:B{row_num}")
            row_num += len(characteristic_rows) + 3
    merges = f'<mergeCells count="{len(merge_refs)}">' + "".join(f'<mergeCell ref="{ref}"/>' for ref in merge_refs) + "</mergeCells>" if merge_refs else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="4" topLeftCell="A5" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{cols}</cols>
  <sheetData>{sheet_data}</sheetData>
  {merges}
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>'''


def drawio_label(value: object) -> str:
    return html.escape(str(value), quote=True).replace("\n", "&#xa;")


def drawio_cell(
    cell_id: str,
    value: object,
    x: float,
    y: float,
    width: float,
    height: float,
    style: str,
    parent: str = "1",
) -> str:
    return (
        f'<mxCell id="{cell_id}" value="{drawio_label(value)}" style="{style}" vertex="1" parent="{parent}">'
        f'<mxGeometry x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" as="geometry"/>'
        "</mxCell>"
    )


def drawio_edge(edge_id: str, source: str, target: str) -> str:
    style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#6B7280;"
    return (
        f'<mxCell id="{edge_id}" value="" style="{style}" edge="1" parent="1" source="{source}" target="{target}">'
        '<mxGeometry relative="1" as="geometry"/>'
        "</mxCell>"
    )


def build_drawio_diagram(rows: list[BomRow], reference_label: str) -> str:
    summaries = configured_system_summary_rows(rows)
    if not summaries:
        summaries = [
            {
                "environment": "General",
                "platform": "No configured Exadata system rows detected",
                "racks": "",
                "db_type": "",
                "db_servers": "",
                "storage_type": "",
                "storage_servers": "",
                "requested_ecpus": "",
                "configured_ecpus": "",
                "db_cores": "",
                "memory_gb": "",
                "usable_storage_tb": "",
                "xrmem_tb": "",
                "flash_cache_tb": "",
                "max_vm_clusters": "",
                "redundancy": "",
                "license_model": "",
                "notes": "Add Exadata BOM rows to generate a configured-system diagram.",
            }
        ]

    title_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#1F4E79;fontColor=#FFFFFF;fontStyle=1;strokeColor=#1F4E79;"
    section_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#305496;fontColor=#FFFFFF;fontStyle=1;strokeColor=#1F4E79;"
    db_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#EAF2F8;strokeColor=#6D8F8D;fontColor=#111827;"
    storage_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F4F7F6;strokeColor=#6D8F8D;fontColor=#111827;"
    vm_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#F7F7F7;strokeColor=#9C918A;fontColor=#111827;"
    note_style = "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF7ED;strokeColor=#C94938;fontColor=#111827;"

    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    today = date.today().strftime("%m/%d/%Y")
    title_id = "title"
    diagram_width = max(520, 420 * len(summaries) + 40)
    cells.append(
        drawio_cell(
            title_id,
            f"{reference_label}\nConfigured System Diagram\nGenerated {today}",
            40,
            30,
            diagram_width,
            70,
            title_style,
        )
    )

    for idx, item in enumerate(summaries):
        x = 40 + (idx * 420)
        y = 140
        env_id = f"env_{idx}"
        db_id = f"db_{idx}"
        storage_id = f"storage_{idx}"
        vm_id = f"vm_{idx}"
        note_id = f"note_{idx}"
        cells.append(
            drawio_cell(
                env_id,
                f"{item['environment']}\n{item['platform']}\nRacks: {item['racks']} | License: {item['license_model']}",
                x,
                y,
                380,
                78,
                section_style,
            )
        )
        cells.append(
            drawio_cell(
                db_id,
                "Database servers\n"
                f"Type: {item['db_type']} | Count: {item['db_servers']}\n"
                f"Requested ECPUs: {item['requested_ecpus']}\n"
                f"Configured ECPU capacity: {item['configured_ecpus']}\n"
                f"Usable DB cores: {item['db_cores']}\n"
                f"VM memory: {item['memory_gb']} GB",
                x,
                y + 115,
                180,
                135,
                db_style,
            )
        )
        cells.append(
            drawio_cell(
                storage_id,
                "Storage servers\n"
                f"Type: {item['storage_type']} | Count: {item['storage_servers']}\n"
                f"Usable storage: {item['usable_storage_tb']} TB\n"
                f"XRMEM: {item['xrmem_tb']} TB\n"
                f"Flash cache: {item['flash_cache_tb']} TB\n"
                f"Redundancy: {item['redundancy']}",
                x + 200,
                y + 115,
                180,
                135,
                storage_style,
            )
        )
        cells.append(
            drawio_cell(
                vm_id,
                f"VM clusters\nMaximum VM clusters: {item['max_vm_clusters']}\nECPUs are allocated to VM clusters and can scale online.",
                x,
                y + 280,
                380,
                70,
                vm_style,
            )
        )
        cells.append(
            drawio_cell(
                note_id,
                f"Basis\n{item['notes']}",
                x,
                y + 375,
                380,
                70,
                note_style,
            )
        )
        cells.append(drawio_edge(f"edge_env_db_{idx}", env_id, db_id))
        cells.append(drawio_edge(f"edge_env_storage_{idx}", env_id, storage_id))
        cells.append(drawio_edge(f"edge_db_vm_{idx}", db_id, vm_id))
        cells.append(drawio_edge(f"edge_storage_vm_{idx}", storage_id, vm_id))

    source_note = (
        "Source note: sizing values come from BOM rows and active Exadata X11M reference values. "
        "Diagram is a proposal-level view, not a formal Oracle quote."
    )
    cells.append(drawio_cell("source_note", source_note, 40, 620, diagram_width, 54, note_style))
    root = "".join(cells)
    return (
        '<mxfile host="app.diagrams.net" type="device">'
        '<diagram id="oracle-cloud-bom-diagram" name="Configured System">'
        f'<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
        f'fold="1" page="1" pageScale="1" pageWidth="{diagram_width + 80:g}" pageHeight="720" math="0" shadow="0">'
        f"<root>{root}</root>"
        "</mxGraphModel>"
        "</diagram>"
        "</mxfile>"
    )


def write_drawio_diagram(rows: list[BomRow], reference_label: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_drawio_diagram(rows, reference_label), encoding="utf-8")
    return


def workbook_rels_xml(template: Path) -> bytes:
    with ZipFile(template, "r") as workbook:
        rels = workbook.read("xl/_rels/workbook.xml.rels").decode("utf-8")

    if 'Target="worksheets/sheet2.xml"' not in rels:
        customer_rel = (
            '<Relationship Id="rId5" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet2.xml"/>'
        )
        rels = rels.replace("</Relationships>", f"{customer_rel}</Relationships>", 1)
    if 'Target="worksheets/sheet3.xml"' not in rels:
        summary_rel = (
            '<Relationship Id="rId6" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet3.xml"/>'
        )
        rels = rels.replace("</Relationships>", f"{summary_rel}</Relationships>", 1)
    return rels.encode("utf-8")


def content_types_xml(template: Path) -> bytes:
    with ZipFile(template, "r") as workbook:
        content_types = workbook.read("[Content_Types].xml").decode("utf-8")

    if 'PartName="/xl/worksheets/sheet2.xml"' not in content_types:
        override = (
            '<Override PartName="/xl/worksheets/sheet2.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        content_types = content_types.replace("</Types>", f"{override}</Types>", 1)
    if 'PartName="/xl/worksheets/sheet3.xml"' not in content_types:
        override = (
            '<Override PartName="/xl/worksheets/sheet3.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        content_types = content_types.replace("</Types>", f"{override}</Types>", 1)
    return content_types.encode("utf-8")


def workbook_with_customer_sheet_xml(template: Path) -> bytes:
    workbook_xml_text = workbook_xml(template).decode("utf-8")
    if 'name="Customer BOM"' not in workbook_xml_text:
        customer_sheet = '<sheet sheetId="2" name="Customer BOM" state="visible" r:id="rId5"/>'
        workbook_xml_text = workbook_xml_text.replace("</sheets>", f"{customer_sheet}</sheets>", 1)
    if 'name="System Summary"' not in workbook_xml_text:
        summary_sheet = '<sheet sheetId="3" name="System Summary" state="visible" r:id="rId6"/>'
        workbook_xml_text = workbook_xml_text.replace("</sheets>", f"{summary_sheet}</sheets>", 1)
    if "<bookViews>" not in workbook_xml_text:
        if re.search(r"<workbookPr[^>]*/>", workbook_xml_text):
            workbook_xml_text = re.sub(
                r"(<workbookPr[^>]*/>)",
                r'\1<bookViews><workbookView activeTab="1" firstSheet="1"/></bookViews>',
                workbook_xml_text,
                count=1,
            )
        else:
            workbook_xml_text = workbook_xml_text.replace(
                "</workbookPr>",
                '</workbookPr><bookViews><workbookView activeTab="1" firstSheet="1"/></bookViews>',
                1,
            )
    elif "activeTab=" not in workbook_xml_text:
        workbook_xml_text = workbook_xml_text.replace("<workbookView", '<workbookView activeTab="1" firstSheet="1"', 1)
    else:
        workbook_xml_text = re.sub(r'activeTab="\d+"', 'activeTab="1"', workbook_xml_text, count=1)
    return workbook_xml_text.encode("utf-8")


def write_workbook(template: Path, output: Path, sheet_xml: str, customer_sheet_xml: str, system_summary_xml: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(template, "r") as src, ZipFile(output, "w", ZIP_DEFLATED) as dst:
        wrote_customer_sheet = False
        wrote_system_summary_sheet = False
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                data = sheet_xml.encode("utf-8")
            elif info.filename == "xl/worksheets/sheet2.xml":
                data = customer_sheet_xml.encode("utf-8")
                wrote_customer_sheet = True
            elif info.filename == "xl/worksheets/sheet3.xml":
                data = system_summary_xml.encode("utf-8")
                wrote_system_summary_sheet = True
            elif info.filename == "xl/styles.xml":
                data = workbook_styles_xml(template)
            elif info.filename == "xl/workbook.xml":
                data = workbook_with_customer_sheet_xml(template)
            elif info.filename == "xl/_rels/workbook.xml.rels":
                data = workbook_rels_xml(template)
            elif info.filename == "[Content_Types].xml":
                data = content_types_xml(template)
            elif info.filename == "xl/calcChain.xml":
                continue
            dst.writestr(info, data)
        if not wrote_customer_sheet:
            dst.writestr("xl/worksheets/sheet2.xml", customer_sheet_xml.encode("utf-8"))
        if not wrote_system_summary_sheet:
            dst.writestr("xl/worksheets/sheet3.xml", system_summary_xml.encode("utf-8"))


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
    parser.add_argument(
        "--diagram-output",
        type=Path,
        help="Optional Draw.io-compatible .drawio block diagram output path.",
    )
    args = parser.parse_args()

    rows = load_rows(args.input_csv)
    supplemental_prices = load_supplemental_prices(args.supplemental_pricing_csv)
    rows = with_supplemental_pricing(rows, supplemental_prices, args.supplemental_source_date)
    currency_style = currency_style_id(args.template)
    sheet_xml = build_sheet(
        rows,
        args.discount,
        args.reference_label,
        args.currency,
        args.realm,
        args.service_type,
        currency_style,
    )
    customer_sheet_xml = build_customer_sheet(
        rows,
        args.reference_label,
        args.currency,
        args.realm,
        currency_style,
    )
    system_summary_xml = build_system_summary_sheet(rows, args.reference_label, currency_style)
    write_workbook(args.template, args.output, sheet_xml, customer_sheet_xml, system_summary_xml)
    if args.diagram_output:
        write_drawio_diagram(rows, args.reference_label, args.diagram_output)
    print(args.output)


if __name__ == "__main__":
    main()
