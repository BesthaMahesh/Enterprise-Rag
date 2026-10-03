from typing import List, Dict, Any, Tuple


class DatabaseLoader:
    """Loads enterprise records from SQL databases and formats them into structured text."""

    @staticmethod
    def load_table_records(table_name: str, records: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        lines = [f"# Table: {table_name}\n"]
        for idx, row in enumerate(records, start=1):
            row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
            lines.append(f"Row {idx}: {row_str}")

        content = "\n".join(lines)
        metadata = {
            "source_type": "database",
            "table_name": table_name,
            "record_count": len(records)
        }
        return content, metadata
