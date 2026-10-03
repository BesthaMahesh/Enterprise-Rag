from typing import Tuple, List
import numpy as np


class EmbeddingValidator:
    """Validates vector shapes, NaN, Inf, and non-zero magnitude."""

    @staticmethod
    def validate_vector(vec: np.ndarray, expected_dim: int = 384) -> Tuple[bool, str]:
        if vec is None:
            return False, "Vector is None"
        if not isinstance(vec, np.ndarray):
            return False, f"Expected np.ndarray, got {type(vec)}"
        if vec.shape[-1] != expected_dim:
            return False, f"Dimension mismatch: expected {expected_dim}, got {vec.shape[-1]}"
        if np.isnan(vec).any():
            return False, "Vector contains NaN values"
        if np.isinf(vec).any():
            return False, "Vector contains infinite values"
        norm = np.linalg.norm(vec)
        if norm == 0.0:
            return False, "Vector has zero magnitude"
        return True, "Valid"
