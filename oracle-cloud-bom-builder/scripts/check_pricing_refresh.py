#!/usr/bin/env python3
"""Check calculator and eSource pricing-source freshness before BOM generation."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import warnings
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = ROOT / "tmp" / "esource-price-list"
DEFAULT_METADATA = DEFAULT_CACHE_DIR / "oracle-paas-iaas-public-cloud-global-price-list.metadata.json"
DEFAULT_DOWNLOADS = Path.home() / "Downloads"
ESOURCE_URL = "https://esource.oraclecorp.com/sites/eSource/ContentAsset_1530207473152"
DATE_PATTERNS = [
    "%B %d, %Y",
    "%b %d, %Y",
    "%Y-%m-%d",
    "%m/%d/%Y",
]


@dataclass
class Finding:
    level: str
    message: str


def parse_date(value: str) -> date | None:
    cleaned = value.strip()
    cleaned = re.sub(r"^(last\s+updated|document\s+date)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    for pattern in DATE_PATTERNS:
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            pass
    return None


def date_label(value: date | None) -> str:
    return value.isoformat() if value else "unknown"


def load_metadata(path: Path) -> tuple[dict[str, object], list[Finding]]:
    findings: list[Finding] = []
    if not path.exists():
        return {}, [Finding("FAIL", f"Missing eSource cache metadata: {path}")]
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [Finding("FAIL", f"Invalid eSource cache metadata JSON: {path}: {exc}")]
    required = ["source_url", "document_title", "document_date", "retrieved_at", "cached_file"]
    for key in required:
        if not metadata.get(key):
            findings.append(Finding("FAIL", f"eSource metadata missing required field: {key}"))
    if metadata.get("source_url") != ESOURCE_URL:
        findings.append(Finding("WARN", f"eSource metadata source_url differs from expected URL: {metadata.get('source_url')}"))
    return metadata, findings


def extract_pdf_date(pdf_path: Path) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    if not pdf_path.exists():
        return "", [Finding("FAIL", f"Cached eSource PDF not found: {pdf_path}")]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", [Finding("WARN", "pypdf is unavailable; skipped cached PDF document-date extraction")]
    try:
        reader = PdfReader(str(pdf_path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:3])
    except Exception as exc:
        return "", [Finding("WARN", f"Could not extract cached PDF text: {exc}")]
    match = re.search(r"Last\s+updated\s*:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)
    if not match:
        return "", [Finding("WARN", "Could not find 'Last updated' date in cached eSource PDF text")]
    return match.group(1), findings


def row_text(row: dict[str, str]) -> str:
    return " ".join(str(value or "") for value in row.values()).lower()


def is_esource_priced_text(text: str) -> bool:
    esource_markers = [
        "pricing sourced from oracle esource",
        "pricing sourced from authenticated oracle esource",
        "oracle esource pdf pricing",
        "priced from oracle esource",
        "priced by oracle esource",
        "row came from the oracle esource",
        "source document date",
    ]
    price_list_markers = [
        "pricing sourced from oracle price-list",
        "pricing sourced from oracle price list",
        "price-list description and price fields",
        "price list description and price fields",
    ]
    return any(marker in text for marker in esource_markers + price_list_markers)


def scan_csv(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": str(path),
        "rows": 0,
        "calculator_rows": 0,
        "esource_rows": 0,
        "esource_dates": set(),
        "standard_exadata_esource_rows": 0,
    }
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            result["rows"] = int(result["rows"]) + 1
            text = row_text(row)
            if "calculator" in text or "cost estimator" in text:
                result["calculator_rows"] = int(result["calculator_rows"]) + 1
            has_esource_pricing = is_esource_priced_text(text)
            if has_esource_pricing:
                result["esource_rows"] = int(result["esource_rows"]) + 1
            for match in re.finditer(r"(?:document date|last updated)\s*:?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE):
                cast_dates = result["esource_dates"]
                assert isinstance(cast_dates, set)
                cast_dates.add(match.group(1))
            is_cloud_at_customer = "cloud@customer" in text or "cloud at customer" in text or "c@c" in text
            is_standard_exadata = (
                "dedicated infrastructure" in text
                or "database@azure" in text
                or "database@google" in text
                or "database@aws" in text
                or "cloud infrastructure" in text
            )
            if is_standard_exadata and not is_cloud_at_customer and has_esource_pricing:
                result["standard_exadata_esource_rows"] = int(result["standard_exadata_esource_rows"]) + 1
    return result


def recent_calculator_exports(downloads_dir: Path) -> list[Path]:
    if not downloads_dir.exists():
        return []
    candidates = []
    for path in downloads_dir.iterdir():
        if path.suffix.lower() not in {".csv", ".xlsx"}:
            continue
        name = path.name.lower()
        if any(token in name for token in ["cost", "estimate", "estimator", "oracle"]):
            candidates.append(path)
    return sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[:5]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Oracle BOM pricing-source freshness.")
    parser.add_argument("--input-csv", action="append", type=Path, default=[], help="BOM CSV input to inspect. Repeat for multiple files.")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA, help="eSource cache metadata JSON path.")
    parser.add_argument("--current-esource-date", default="", help="Live eSource PDF date read from authenticated browser, e.g. 'June 11, 2026'.")
    parser.add_argument("--downloads-dir", type=Path, default=DEFAULT_DOWNLOADS, help="Directory to inspect for recent calculator exports.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = parser.parse_args()

    findings: list[Finding] = []
    metadata, metadata_findings = load_metadata(args.metadata)
    findings.extend(metadata_findings)

    cached_pdf = None
    metadata_date = parse_date(str(metadata.get("document_date", ""))) if metadata else None
    if metadata.get("cached_file"):
        cached_pdf = args.metadata.parent / str(metadata["cached_file"])
        pdf_date_text, pdf_findings = extract_pdf_date(cached_pdf)
        findings.extend(pdf_findings)
        pdf_date = parse_date(pdf_date_text) if pdf_date_text else None
        if pdf_date and metadata_date and pdf_date != metadata_date:
            findings.append(Finding("FAIL", f"Cached PDF date {date_label(pdf_date)} does not match metadata date {date_label(metadata_date)}"))

    live_date = parse_date(args.current_esource_date) if args.current_esource_date else None
    if args.current_esource_date and not live_date:
        findings.append(Finding("FAIL", f"Could not parse --current-esource-date: {args.current_esource_date}"))
    if live_date and metadata_date:
        if live_date > metadata_date:
            findings.append(Finding("FAIL", f"Live eSource date {date_label(live_date)} is newer than cached metadata date {date_label(metadata_date)}; refresh the cached PDF before pricing."))
        else:
            findings.append(Finding("PASS", f"Live eSource date {date_label(live_date)} is not newer than cached metadata date {date_label(metadata_date)}."))

    csv_paths = args.input_csv
    if not csv_paths:
        csv_paths = sorted((ROOT / "inputs").glob("*.csv")) + sorted((ROOT / "tmp").glob("*.csv"))
    csv_reports = []
    for path in csv_paths:
        if not path.exists():
            findings.append(Finding("FAIL", f"Input CSV not found: {path}"))
            continue
        report = scan_csv(path)
        csv_reports.append(report)
        if int(report["esource_rows"]) and not live_date:
            findings.append(Finding("WARN", f"{path}: uses eSource-priced rows; provide --current-esource-date from the authenticated PDF before final pricing."))
        if int(report["standard_exadata_esource_rows"]):
            findings.append(Finding("WARN", f"{path}: standard Dedicated/Database@ Exadata rows mention eSource; prefer calculator export rows when calculator coverage exists."))
        dates = report["esource_dates"]
        assert isinstance(dates, set)
        for source_date in sorted(dates):
            parsed = parse_date(source_date)
            if parsed and metadata_date and parsed != metadata_date:
                findings.append(Finding("WARN", f"{path}: row source date {source_date} differs from cached metadata date {metadata.get('document_date')}"))

    downloads = recent_calculator_exports(args.downloads_dir)
    if downloads:
        findings.append(Finding("INFO", f"Recent possible calculator exports in {args.downloads_dir}: " + ", ".join(path.name for path in downloads[:3])))
    else:
        findings.append(Finding("INFO", f"No recent calculator/export candidates found in {args.downloads_dir}"))

    print("Pricing refresh check")
    print(f"Metadata: {args.metadata}")
    print(f"Cached PDF: {cached_pdf if cached_pdf else 'not recorded'}")
    print(f"Cached document date: {metadata.get('document_date', 'unknown') if metadata else 'unknown'}")
    print(f"Live eSource date supplied: {args.current_esource_date or 'not supplied'}")
    print()
    print("CSV source scan:")
    for report in csv_reports:
        dates = report["esource_dates"]
        assert isinstance(dates, set)
        date_text = ", ".join(sorted(dates)) if dates else "-"
        print(
            f"- {report['path']}: rows={report['rows']}, calculator_rows={report['calculator_rows']}, "
            f"esource_rows={report['esource_rows']}, esource_dates={date_text}"
        )
    print()
    print("Findings:")
    for finding in findings:
        print(f"{finding.level}: {finding.message}")

    has_fail = any(finding.level == "FAIL" for finding in findings)
    has_warn = any(finding.level == "WARN" for finding in findings)
    if has_fail or (args.strict and has_warn):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
