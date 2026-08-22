"""Phase 6: Dice loss + Dice score + IoU for binary segmentation.

Conventions
-----------
* Inputs are torch tensors whose leading dim is the BATCH; trailing dims
  are flattened per sample. Shapes (N, H, W), (N, 1, H, W) both work.
* `dice_loss` is SOFT (differentiable): `pred` holds probabilities in
  [0, 1] (e.g. sigmoid outputs). A small `smooth` term keeps the division
  safe and gives sane gradients even when a sample has an empty mask.
* `dice_score` / `iou_score` are HARD evaluation metrics: predictions are
  binarized at 0.5 first. Exact empty-mask handling - no epsilon fudging:
      GT empty & pred empty -> perfect agreement -> value = `empty_value` (1.0)
      GT empty XOR pred empty -> no overlap possible -> 0.0

All functions return plain numerical tensors; nothing here trains anything.
"""

from __future__ import annotations

import torch


def _check_pair(pred: torch.Tensor, target: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    if pred.shape != target.shape:
        raise ValueError(f"shape mismatch: pred {tuple(pred.shape)} vs target {tuple(target.shape)}")
    if pred.dim() < 1:
        raise ValueError("inputs must have at least a batch dimension")
    return pred, target


def _reduce(per_sample: torch.Tensor, reduction: str):
    if reduction == "mean":
        return per_sample.mean()
    if reduction == "none":
        return per_sample
    raise ValueError(f"reduction must be 'mean' or 'none', got {reduction!r}")


def dice_loss(
    pred: torch.Tensor,
    target: torch.Tensor,
    smooth: float = 1.0,
    reduction: str = "mean",
) -> torch.Tensor:
    """Soft Dice loss on probabilities; differentiable and batch-ready.

    loss = 1 - (2*sum(p*g) + smooth) / (sum(p) + sum(g) + smooth)

    The `smooth` term guarantees the denominator is never zero:
      * both masks empty        -> ratio = 1 -> loss = 0   (perfect)
      * one mask empty          -> ratio ~ 0 -> loss ~ 1
    """
    p, g = _check_pair(pred.float(), target.float())
    n = p.shape[0]
    dims = tuple(range(1, p.dim()))

    p_flat = p.reshape(n, -1)
    g_flat = g.reshape(n, -1)

    inter = 2.0 * (p_flat * g_flat).sum(dim=1)
    denom = p_flat.sum(dim=1) + g_flat.sum(dim=1)

    # guard even against smooth == 0: an entirely empty sample counts as
    # perfect agreement instead of producing 0/0
    ratio = torch.where(
        (denom + smooth) > 0,
        (inter + smooth) / (denom + smooth).clamp_min(torch.finfo(torch.float32).tiny),
        torch.ones_like(inter),
    )

    return _reduce(1.0 - ratio, reduction)


def dice_score(
    pred: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    reduction: str = "mean",
    empty_value: float = 1.0,
) -> torch.Tensor:
    """Hard Dice coefficient per sample; NaN-free by construction."""
    p, g = _check_pair(pred, target)
    pb = (p.float() > threshold).reshape(p.shape[0], -1)
    gb = (g.float() > threshold).reshape(g.shape[0], -1)

    inter = (pb & gb).sum(dim=1).float()
    denom = pb.sum(dim=1).float() + gb.sum(dim=1).float()

    per_sample = torch.where(
        denom > 0,
        2.0 * inter / denom.clamp_min(1.0),
        torch.full_like(inter, float(empty_value)),
    )
    return _reduce(per_sample, reduction)


def iou_score(
    pred: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    reduction: str = "mean",
    empty_value: float = 1.0,
) -> torch.Tensor:
    """Hard Intersection-over-Union per sample; NaN-free by construction."""
    p, g = _check_pair(pred, target)
    pb = (p.float() > threshold).reshape(p.shape[0], -1)
    gb = (g.float() > threshold).reshape(g.shape[0], -1)

    inter = (pb & gb).sum(dim=1).float()
    union = (pb | gb).sum(dim=1).float()

    per_sample = torch.where(
        union > 0,
        inter / union.clamp_min(1.0),
        torch.full_like(inter, float(empty_value)),
    )
    return _reduce(per_sample, reduction)


def precision_score(
    pred: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    reduction: str = "mean",
    empty_value: float = 1.0,
) -> torch.Tensor:
    """Hard precision TP/(TP+FP) per sample; NaN-free by construction.

    Empty conventions: pred empty & gt empty -> `empty_value` (nothing
    predicted, nothing to find); pred empty & gt non-empty -> 0.0
    (everything missed); pred non-empty & gt empty -> 0.0 (pure FP).
    """
    p, g = _check_pair(pred, target)
    pb = (p.float() > threshold).reshape(p.shape[0], -1)
    gb = (g.float() > threshold).reshape(g.shape[0], -1)

    tp = (pb & gb).sum(dim=1).float()
    fp = (pb & ~gb).sum(dim=1).float()
    n_pred = tp + fp
    n_gt = gb.sum(dim=1).float()

    per_sample = torch.where(
        n_pred > 0,
        tp / n_pred.clamp_min(1.0),
        torch.where(n_gt == 0,
                    torch.full_like(tp, float(empty_value)),
                    torch.zeros_like(tp)),
    )
    return _reduce(per_sample, reduction)


def recall_score(
    pred: torch.Tensor,
    target: torch.Tensor,
    threshold: float = 0.5,
    reduction: str = "mean",
    empty_value: float = 1.0,
) -> torch.Tensor:
    """Hard recall TP/(TP+FN) per sample; NaN-free by construction.

    Empty conventions mirror precision: both empty -> `empty_value`;
    gt non-empty & pred empty -> 0.0; gt empty & pred non-empty -> 0.0.
    """
    p, g = _check_pair(pred, target)
    pb = (p.float() > threshold).reshape(p.shape[0], -1)
    gb = (g.float() > threshold).reshape(g.shape[0], -1)

    tp = (pb & gb).sum(dim=1).float()
    fn = (~pb & gb).sum(dim=1).float()
    n_gt = tp + fn
    n_pred = pb.sum(dim=1).float()

    per_sample = torch.where(
        n_gt > 0,
        tp / n_gt.clamp_min(1.0),
        torch.where(n_pred == 0,
                    torch.full_like(tp, float(empty_value)),
                    torch.zeros_like(tp)),
    )
    return _reduce(per_sample, reduction)
