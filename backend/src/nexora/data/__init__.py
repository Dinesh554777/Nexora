"""nexora.data — integration shim.

Only the pieces required by the inference path are provided: the subject-id
parser (pinned by tests/test_splitting.py) and the SliceSample container
(shape fixed by nexora.preprocessing's usage). The full training-time dataset
utilities (PairSlicesDataset, VolumePair, ...) were not part of the pushed ML
branch; restore them from the ML developer's original tree and delete this
shim.
"""

from nexora.data.loader import SliceSample
from nexora.data.splitting import extract_subject_id

__all__ = ["SliceSample", "extract_subject_id"]
