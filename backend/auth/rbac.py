from typing import List, Set
from backend.database.models import UserRole, DataClassification

# Role to Classifications mapping
ROLE_CLASSIFICATION_MAP = {
    UserRole.EMPLOYEE.value: {DataClassification.INTERNAL.value},
    UserRole.HR.value: {
        DataClassification.INTERNAL.value,
        DataClassification.CONFIDENTIAL.value,
        DataClassification.RESTRICTED.value
    },
    UserRole.FINANCE.value: {
        DataClassification.INTERNAL.value,
        DataClassification.CONFIDENTIAL.value,
        DataClassification.RESTRICTED.value
    },
    UserRole.ADMIN.value: {
        DataClassification.INTERNAL.value,
        DataClassification.CONFIDENTIAL.value,
        DataClassification.RESTRICTED.value,
        DataClassification.HIGHLY_RESTRICTED.value
    },
    UserRole.SECURITY.value: {
        DataClassification.INTERNAL.value,
        DataClassification.HIGHLY_RESTRICTED.value
    }
}

# Role permissions for UI / Admin endpoints
ROLE_PERMISSIONS = {
    UserRole.EMPLOYEE.value: {
        "chat:ask",
        "chat:history",
        "documents:read_public",
    },
    UserRole.HR.value: {
        "chat:ask",
        "chat:history",
        "documents:read_public",
        "documents:read_hr",
        "documents:upload",
        "documents:manage",
        "audit:read",
        "analytics:read",
        "evaluation:read",
    },
    UserRole.FINANCE.value: {
        "chat:ask",
        "chat:history",
        "documents:read_public",
        "documents:read_finance",
        "audit:read",
        "analytics:read",
    },
    UserRole.ADMIN.value: {
        "chat:ask",
        "chat:history",
        "documents:read_public",
        "documents:read_hr",
        "documents:read_finance",
        "documents:read_restricted",
        "documents:upload",
        "documents:manage",
        "documents:delete",
        "documents:reindex",
        "users:manage",
        "audit:read",
        "audit:export",
        "evaluation:read",
        "evaluation:run",
        "analytics:read",
        "system:manage"
    },
    UserRole.SECURITY.value: {
        "chat:ask",
        "chat:history",
        "documents:read_public",
        "documents:read_restricted",
        "audit:read",
        "evaluation:read",
    }
}


def has_permission(user_role: str, permission: str) -> bool:
    """Check if role has specific permission."""
    perms = ROLE_PERMISSIONS.get(user_role, set())
    return permission in perms


def get_allowed_classifications_for_role(user_role: str) -> Set[str]:
    """Get all classification levels accessible by role."""
    return ROLE_CLASSIFICATION_MAP.get(user_role, {DataClassification.INTERNAL.value})
