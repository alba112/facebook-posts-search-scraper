thonimport csv
import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List

from xml.etree.ElementTree import Element, SubElement, ElementTree

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"
    HTML = "html"
    XML = "xml"

def export_posts(
    posts: List[Dict[str, Any]],
    output_path: Path,
    export_format: ExportFormat,
) -> None:
    """
    Export posts to the specified format at output_path.
    """
    if export_format == ExportFormat.JSON:
        _export_json(posts, output_path)
    elif export_format == ExportFormat.CSV:
        _export_csv(posts, output_path)
    elif export_format == ExportFormat.EXCEL:
        _export_excel(posts, output_path)
    elif export_format == ExportFormat.HTML:
        _export_html(posts, output_path)
    elif export_format == ExportFormat.XML:
        _export_xml(posts, output_path)
    else:
        raise ValueError(f"Unsupported export format: {export_format}")

def _normalize_rows(posts: Iterable[Dict[str, Any]]) -> (List[str], List[Dict[str, Any]]):
    rows: List[Dict[str, Any]] = list(posts)
    field_names: List[str] = sorted({key for row in rows for key in row.keys()})
    return field_names, rows

def _export_json(posts: List[Dict[str, Any]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def _export_csv(posts: List[Dict[str, Any]], output_path: Path) -> None:
    field_names, rows = _normalize_rows(posts)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def _export_excel(posts: List[Dict[str, Any]], output_path: Path) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError(
            "Excel export requires 'openpyxl'. Install it with 'pip install openpyxl'."
        ) from exc

    field_names, rows = _normalize_rows(posts)
    wb = Workbook()
    ws = wb.active
    ws.title = "FacebookPosts"

    ws.append(field_names)
    for row in rows:
        ws.append([row.get(field, "") for field in field_names])

    wb.save(output_path)

def _export_html(posts: List[Dict[str, Any]], output_path: Path) -> None:
    field_names, rows = _normalize_rows(posts)

    html_parts: List[str] = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>Facebook Posts Export</title>",
        "<style>",
        "table { border-collapse: collapse; width: 100%; }",
        "th, td { border: 1px solid #ddd; padding: 8px; font-family: sans-serif; font-size: 14px; }",
        "th { background-color: #f2f2f2; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Facebook Posts Export</h1>",
        "<table>",
        "<thead>",
        "<tr>",
    ]
    for field in field_names:
        html_parts.append(f"<th>{field}</th>")
    html_parts.extend(["</tr>", "</thead>", "<tbody>"])

    for row in rows:
        html_parts.append("<tr>")
        for field in field_names:
            value = row.get(field, "")
            html_parts.append(f"<td>{_escape_html(str(value))}</td>")
        html_parts.append("</tr>")

    html_parts.extend(["</tbody>", "</table>", "</body>", "</html>"])

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

def _export_xml(posts: List[Dict[str, Any]], output_path: Path) -> None:
    root = Element("posts")
    for row in posts:
        item = SubElement(root, "post")
        for key, value in row.items():
            child = SubElement(item, key)
            child.text = "" if value is None else str(value)

    tree = ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)