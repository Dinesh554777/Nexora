# INTEGRATION NOTE (backend team): the training-time dataset utilities were
# not part of the pushed ML branch. The guarded import keeps the inference
# path working; restore the plain import once nexora.data is fully pushed.
try:
    from nexora.data import (
        PairSlicesDataset,
        SliceSample,
        VolumePair,
        discover_pairs,
        extract_slices,
        load_volume_pair,
    )
    _DATA_EXPORTS = [
        "PairSlicesDataset",
        "SliceSample",
        "VolumePair",
        "discover_pairs",
        "extract_slices",
        "load_volume_pair",
    ]
except ImportError:  # pragma: no cover - restored when ML pushes nexora.data
    _DATA_EXPORTS = ["extract_subject_id"]
    from nexora.data import extract_subject_id  # noqa: F401

from nexora.preprocessing import (
    PreprocessedSample,
    PreprocessConfig,
    check_binary,
    derive_resized_spacing,
    normalize_intensity,
    preprocess_slice,
    resize_image,
    resize_mask,
)

__version__ = "0.1.0"

__all__ = _DATA_EXPORTS + [
    "PreprocessedSample",
    "PreprocessConfig",
    "check_binary",
    "derive_resized_spacing",
    "normalize_intensity",
    "preprocess_slice",
    "resize_image",
    "resize_mask",
]
