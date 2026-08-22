"""Phase 5 model test: dummy input -> forward pass -> dims -> probability mask.

Run:  python tests/test_unet_model.py
"""

from __future__ import annotations

import os
import sys
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)

import torch  # noqa: E402

from ml.models import UNet2D, count_parameters  # noqa: E402

MAX_PARAMS_LIGHTWEIGHT = 8_000_000


def test_dummy_input_forward_output_dims():
    torch.manual_seed(0)
    model = UNet2D(in_channels=1, out_channels=1, base=32, depth=4,
                   input_size=(256, 256))
    model.eval()

    dummy = torch.randn(2, 1, 256, 256)
    with torch.no_grad():
        logits = model(dummy)

    assert logits.shape == (2, 1, 256, 256), f"unexpected output shape {tuple(logits.shape)}"
    assert logits.dtype == torch.float32
    assert torch.isfinite(logits).all(), "non-finite values in output"
    return model


def test_probability_mask_conversion(model):
    dummy = torch.randn(1, 1, 256, 256)
    probs = model.predict_proba(dummy)

    assert probs.shape == (1, 1, 256, 256)
    pmin, pmax = float(probs.min()), float(probs.max())
    assert 0.0 <= pmin <= pmax <= 1.0, f"invalid probability range [{pmin}, {pmax}]"

    binary = (probs > 0.5).to(torch.uint8)
    assert set(torch.unique(binary).tolist()).issubset({0, 1})
    assert binary.dtype == torch.uint8


def test_configurable_input_size():
    for size in [(128, 128), (192, 192), (384, 384)]:
        m = UNet2D(input_size=size, base=16)
        out = m(torch.randn(1, 1, *size))
        assert tuple(out.shape[-2:]) == size

    try:
        UNet2D(input_size=(250, 250))
        raise AssertionError("250 not divisible by 16 - should raise")
    except ValueError:
        pass

    m = UNet2D(input_size=(256, 256))
    try:
        m(torch.randn(1, 1, 128, 128))
        raise AssertionError("mismatched input size - should raise")
    except ValueError:
        pass


def test_lightweight_budget():
    default = count_parameters(UNet2D(base=32))
    small = count_parameters(UNet2D(base=16))
    assert default < MAX_PARAMS_LIGHTWEIGHT, f"too large: {default:,} params"
    assert small < default
    print(f"        params: base=32 -> {default:,} | base=16 -> {small:,}")


def main() -> int:
    failures = []
    model_ref = None

    try:
        model_ref = test_dummy_input_forward_output_dims()
        print("PASS  dummy input -> forward pass -> output dims")
    except Exception:
        failures.append("forward")
        print(f"FAIL  forward\n{traceback.format_exc()}")

    if model_ref is not None:
        try:
            test_probability_mask_conversion(model_ref)
            print("PASS  probability mask conversion")
        except Exception:
            failures.append("proba")
            print(f"FAIL  proba\n{traceback.format_exc()}")

    for name, fn in [
        ("configurable input size", test_configurable_input_size),
        ("lightweight budget", test_lightweight_budget),
    ]:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception:
            failures.append(name)
            print(f"FAIL  {name}\n{traceback.format_exc()}")

    print("\n" + ("ALL PHASE 5 MODEL TESTS PASSED" if not failures
                  else f"{len(failures)} TEST(S) FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
