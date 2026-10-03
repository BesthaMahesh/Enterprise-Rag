from typing import List, Dict, Any, Union


def is_role_in_allowed_roles(user_role: str, allowed_roles: Union[List[str], str]) -> bool:
    """Check if the user's role is in the document's allowed roles or if user is ADMIN."""
    if not user_role:
        return False

    u_role = user_role.strip().upper()
    if u_role == "ADMIN":
        return True

    if isinstance(allowed_roles, str):
        allowed_list = [r.strip().upper() for r in allowed_roles.split(",")]
    elif isinstance(allowed_roles, list):
        allowed_list = [str(r).strip().upper() for r in allowed_roles]
    else:
        return False

    return u_role in allowed_list
