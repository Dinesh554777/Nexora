"""Subject-level splitting utilities.

INTEGRATION NOTE (backend team): the ML branch's full nexora.data package
(dataset loaders, volume pairing, manifest building) was not included in the
pushed repository history. Only the filename parser required by the inference
path is reconstructed here, with behavior pinned by the ML team's own test
suite (tests/test_splitting.py::test_subject_id_parsing). Replace this module
with the original when the ML developer restores it.
"""

from __future__ import annotations

import re

_EXTENSION_RE = re.compile(r"\.(nii\.gz|nii|npy|npz)$", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[_\-]")


def extract_subject_id(filename: str) -> str:
    """Extracts the subject identifier from a dataset filename.

    Rule (matching tests/test_splitting.py):
      * strip a known data extension (.nii.gz / .nii / .npy / .npz);
      * if the first token (split on '_' or '-') is purely numeric,
        that token is the subject id;
      * otherwise the whole extension-stripped stem is the subject id.
    """
    stem = _EXTENSION_RE.sub("", filename)
    tokens = _TOKEN_RE.split(stem)
    if tokens and tokens[0].isdigit():
        return tokens[0]
    return stem
