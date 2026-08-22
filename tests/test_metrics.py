"""Phase 6 verification: loss/metrics on the five required regimes.

Run:  python tests/test_metrics.py

Every expected value below is hand-derived from the definitions - no
benchmark numbers are invented.
"""

from __future__ import annotations

import os
import sys
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import torch  # noqa: E402

from ml.metrics import (  # noqa: E402
    dice_loss,
    dice_score,
    iou_score,
    precision_score,
    recall_score,
)


def mask_from_coords(shape, coords):
    m = torch.zeros(shape)
    for r0, r1, c0, c1 in coords:
        m[..., r0:r1, c0:c1] = 1.0
    return m


def test_perfect_prediction():
    g = mask_from_coords((1, 32, 32), [(8, 16, 8, 16)])
    d = dice_score(g, g).item()
    i = iou_score(g, g).item()
    l = dice_loss(g, g).item()
    assert abs(d - 1.0) < 1e-7, d
    assert abs(i - 1.0) < 1e-7, i
    assert abs(l - 0.0) < 1e-6, l


def test_completely_wrong():
    gt = mask_from_coords((1, 32, 32), [(2, 10, 2, 10)])
    pred = mask_from_coords((1, 32, 32), [(20, 28, 20, 28)])   # disjoint
    d = dice_score(pred, gt).item()
    i = iou_score(pred, gt).item()
    # soft loss with default smooth=1: (2*0 + 1)/(64+64+1)
    expected_loss = 1.0 - 1.0 / (64 + 64 + 1)
    l = dice_loss(pred, gt).item()
    assert d == 0.0, d
    assert i == 0.0, i
    assert abs(l - expected_loss) < 1e-6, (l, expected_loss)


def test_partial_overlap():
    gt = mask_from_coords((1, 32, 32), [(4, 14, 4, 14)])       # 100 px
    pred = mask_from_coords((1, 32, 32), [(9, 19, 4, 14)])     # overlap 50 px
    inter, union = 50.0, 150.0
    expected_dice = 2 * inter / (100.0 + 100.0)
    expected_iou = inter / union
    d = dice_score(pred, gt).item()
    i = iou_score(pred, gt).item()
    assert abs(d - expected_dice) < 1e-7, (d, expected_dice)
    assert abs(i - expected_iou) < 1e-7, (i, expected_iou)


def test_empty_ground_truth():
    gt = torch.zeros(1, 32, 32)
    pred = mask_from_coords((1, 32, 32), [(5, 12, 5, 12)])

    d = dice_score(pred, gt).item()
    i = iou_score(pred, gt).item()
    assert d == 0.0 and i == 0.0, (d, i)

    # smooth keeps the soft loss finite: (0+s)/(sum_p+0+s)
    l = dice_loss(pred, gt, smooth=1.0).item()
    s_p = float(pred.sum())
    assert abs(l - (1.0 - 1.0 / (s_p + 1.0))) < 1e-6
    assert torch.isfinite(torch.tensor(l))


def test_empty_prediction():
    gt = mask_from_coords((1, 32, 32), [(5, 12, 5, 12)])
    pred = torch.zeros(1, 32, 32)

    d = dice_score(pred, gt).item()
    i = iou_score(pred, gt).item()
    assert d == 0.0 and i == 0.0, (d, i)

    l = dice_loss(pred, gt, smooth=1.0).item()
    s_g = float(gt.sum())
    assert abs(l - (1.0 - 1.0 / (s_g + 1.0))) < 1e-6


def test_both_empty_is_safe_and_agrees():
    gt = torch.zeros(2, 16, 16)
    pred = torch.zeros(2, 16, 16)
    d = dice_score(pred, gt).item()
    i = iou_score(pred, gt).item()
    l = dice_loss(pred, gt).item()
    assert d == 1.0 and i == 1.0, (d, i)
    assert abs(l - 0.0) < 1e-7, l
    assert not torch.isnan(dice_loss(pred, gt, smooth=0.0)).any(), \
        "smooth=0 on empty-empty must still be division-safe"


def test_batch_processing_matches_single_samples():
    g1 = mask_from_coords((1, 32, 32), [(4, 12, 4, 12)])
    p1 = mask_from_coords((1, 32, 32), [(6, 14, 4, 12)])
    g2 = mask_from_coords((1, 32, 32), [(2, 8, 2, 8)])
    p2 = g2.clone()

    batch_g = torch.cat([g1, g2])
    batch_p = torch.cat([p1, p2])

    for fn in (dice_score, iou_score):
        per = fn(batch_p, batch_g, reduction="none")
        assert per.shape == (2,), f"{fn.__name__} reduction='none' shape {per.shape}"
        assert abs(per[0].item() - fn(p1, g1).item()) < 1e-7
        assert abs(per[1].item() - fn(p2, g2).item()) < 1e-7
        assert abs(fn(batch_p, batch_g).item() - per.mean().item()) < 1e-7

    per_l = dice_loss(batch_p, batch_g, reduction="none")
    assert per_l.shape == (2,)
    assert abs(per_l[0].item() - dice_loss(p1, g1).item()) < 1e-6


def test_returns_numerical_values_and_shapes():
    g = mask_from_coords((3, 64, 64), [(10, 30, 10, 30)])
    p = g.clone()
    for fn in (dice_score, iou_score, dice_loss):
        out = fn(p, g)
        assert out.dim() == 0, f"{fn.__name__} mean-reduction should be scalar"
        assert torch.is_tensor(out) and torch.isfinite(out).all()


def test_gradient_flows_through_loss():
    g = mask_from_coords((1, 32, 32), [(8, 20, 8, 20)])
    logits = torch.randn(1, 32, 32, requires_grad=True)
    probs = torch.sigmoid(logits)
    loss = dice_loss(probs, g, smooth=1.0)
    loss.backward()
    assert logits.grad is not None and torch.isfinite(logits.grad).all()


def test_precision_recall():
    # asymmetric overlap: GT 100 px, pred 60 px, inter 40
    gt = mask_from_coords((1, 32, 32), [(4, 14, 4, 14)])
    pred = mask_from_coords((1, 32, 32), [(4, 10, 9, 15)])   # rows 4-9 x cols 9-15
    inter = float(((pred > 0.5) & (gt > 0.5)).sum())
    n_pred, n_gt = float((pred > 0.5).sum()), float((gt > 0.5).sum())
    exp_p, exp_r = inter / n_pred, inter / n_gt
    assert abs(precision_score(pred, gt).item() - exp_p) < 1e-7
    assert abs(recall_score(pred, gt).item() - exp_r) < 1e-7

    g2 = mask_from_coords((1, 32, 32), [(2, 10, 2, 10)])
    p2 = mask_from_coords((1, 32, 32), [(20, 28, 20, 28)])
    assert precision_score(p2, g2).item() == 0.0
    assert recall_score(p2, g2).item() == 0.0

    empty = torch.zeros(1, 32, 32)
    assert precision_score(empty, empty).item() == 1.0     # both empty -> agree
    assert recall_score(empty, empty).item() == 1.0
    assert precision_score(mask_from_coords((1, 32, 32), [(3, 8, 3, 8)]), empty).item() == 0.0
    assert recall_score(mask_from_coords((1, 32, 32), [(3, 8, 3, 8)]), empty).item() == 0.0
    assert precision_score(empty, mask_from_coords((1, 32, 32), [(3, 8, 3, 8)])).item() == 0.0
    assert recall_score(empty, mask_from_coords((1, 32, 32), [(3, 8, 3, 8)])).item() == 0.0


def main() -> int:
    tests = [
        ("perfect", test_perfect_prediction),
        ("completely_wrong", test_completely_wrong),
        ("partial_overlap", test_partial_overlap),
        ("empty_gt", test_empty_ground_truth),
        ("empty_pred", test_empty_prediction),
        ("both_empty_safe", test_both_empty_is_safe_and_agrees),
        ("batch_consistency", test_batch_processing_matches_single_samples),
        ("numerical_outputs", test_returns_numerical_values_and_shapes),
        ("loss_gradients_finite", test_gradient_flows_through_loss),
        ("precision_recall", test_precision_recall),
    ]
    failures = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception:
            failures.append(name)
            print(f"FAIL  {name}\n{traceback.format_exc()}")

    print("\n" + ("ALL PHASE 6 METRIC TESTS PASSED" if not failures
                  else f"{len(failures)} TEST(S) FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
