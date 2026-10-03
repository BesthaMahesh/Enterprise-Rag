import os
import json
import re
import hashlib
from typing import Dict, Any, Optional
from backend.metadata.schema import DocumentMetadata


class MetadataExtractor:
    """Extracts and merges metadata from file content, filenames, and companion JSON files."""

    @staticmethod
    def extract_from_file(file_path: str, default_classification: str = "INTERNAL") -> DocumentMetadata:
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        
        # Check if companion json exists in data/metadata/
        meta_json_path = os.path.join("data", "metadata", f"{base_name}.json")
        companion_data = {}
        if os.path.exists(meta_json_path):
            try:
                with open(meta_json_path, "r", encoding="utf-8") as f:
                    companion_data = json.load(f)
            except Exception:
                companion_data = {}

        # Compute checksum
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            hasher.update(f.read())
        checksum = hasher.hexdigest()

        # Deduce title from base_name if not provided
        title = companion_data.get("document") or companion_data.get("title") or base_name.replace("_", " ").title()
        doc_id = companion_data.get("document_id") or f"doc_{base_name}"
        
        # Deduce classification from directory structure if not in json
        classification = companion_data.get("classification")
        if not classification:
            if "admin_restricted" in file_path:
                classification = "HIGHLY_RESTRICTED"
            elif "hr_private" in file_path or "finance_private" in file_path:
                classification = "CONFIDENTIAL"
            else:
                classification = default_classification

        # Allowed roles
        allowed_roles = companion_data.get("allowed_roles")
        if not allowed_roles:
            if "admin_restricted" in file_path:
                allowed_roles = ["ADMIN", "SECURITY"]
            elif "hr_private" in file_path:
                allowed_roles = ["HR", "ADMIN"]
            elif "finance_private" in file_path:
                allowed_roles = ["HR", "FINANCE", "ADMIN"]
            else:
                allowed_roles = ["EMPLOYEE", "HR", "FINANCE", "ADMIN", "SECURITY"]

        return DocumentMetadata(
            document_id=doc_id,
            document=title,
            organization=companion_data.get("organization", "Acme Technologies"),
            domain=companion_data.get("domain", "HR/Enterprise"),
            classification=classification,
            allowed_roles=allowed_roles,
            version=companion_data.get("version", "1.0"),
            effective_date=companion_data.get("effective_date", "2026-01-01"),
            status=companion_data.get("status", "active"),
            language=companion_data.get("language", "en"),
            checksum=checksum
        )
