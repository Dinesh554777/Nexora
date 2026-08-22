"""Phase 5: lightweight 2D U-Net for medial meniscus segmentation (PyTorch).

Structure: Encoder -> Bottleneck -> Decoder with skip connections ->
1-channel segmentation output (raw logits; sigmoid is applied externally or
via `predict_proba`).

Design notes
------------
* Configurable `input_size`: spatial dims must be divisible by 2**depth so
  pooling/upsampling stay exactly invertible; validated at construction.
* Lightweight by default: base=32, depth=4 => ~1.9M params. Drop base to 16
  (~0.5M params) for very constrained training setups.
* No training logic in this file.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    """(Conv3x3 -> BN -> ReLU) x2 - the workhorse of encoder/decoder levels."""

    def __init__(self, c_in: int, c_out: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(c_in, c_out, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c_out),
            nn.ReLU(inplace=True),
            nn.Conv2d(c_out, c_out, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c_out),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class UNet2D(nn.Module):
    """Configurable lightweight U-Net.

    Parameters
    ----------
    in_channels : input channels (grayscale MRI -> 1)
    out_channels : segmentation heads (binary meniscus -> 1 logit map)
    base : feature width of the first encoder level (doubles per level)
    depth : number of pool/downsampling stages (bottleneck at 2**depth reduction)
    input_size : expected (H, W); enforced divisible by 2**depth
    """

    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        base: int = 32,
        depth: int = 4,
        input_size: tuple[int, int] | None = (256, 256),
    ) -> None:
        super().__init__()
        if depth < 1:
            raise ValueError("depth must be >= 1")
        self.depth = depth
        self.input_size = tuple(input_size) if input_size else None
        if self.input_size:
            for s in self.input_size:
                if s % (2 ** depth):
                    raise ValueError(
                        f"input_size {self.input_size} incompatible with depth={depth}: "
                        f"spatial dims must be divisible by {2 ** depth}"
                    )

        w = [base * (2 ** i) for i in range(depth + 1)]   # e.g. [32,64,128,256,512]

        self.encoders = nn.ModuleList()
        c_prev = in_channels
        for i in range(depth):
            self.encoders.append(ConvBlock(c_prev, w[i]))
            c_prev = w[i]
        self.pool = nn.MaxPool2d(2)

        self.bottleneck = ConvBlock(w[depth - 1], w[depth])

        self.upsamplers = nn.ModuleList()
        self.decoders = nn.ModuleList()
        for i in range(depth - 1, -1, -1):
            self.upsamplers.append(nn.ConvTranspose2d(w[i + 1], w[i], 2, stride=2))
            self.decoders.append(ConvBlock(w[i + 1], w[i]))

        self.head = nn.Conv2d(base, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() != 4:
            raise ValueError(f"expected (N, C, H, W), got shape {tuple(x.shape)}")
        if self.input_size and (x.shape[-2], x.shape[-1]) != self.input_size:
            raise ValueError(
                f"input spatial dims {(x.shape[-2], x.shape[-1])} != "
                f"configured input_size {self.input_size}"
            )

        skips: list[torch.Tensor] = []
        h = x
        for enc in self.encoders:
            h = enc(h)
            skips.append(h)
            h = self.pool(h)

        h = self.bottleneck(h)

        for up, dec, skip in zip(self.upsamplers, self.decoders, reversed(skips)):
            h = up(h)
            h = dec(torch.cat([h, skip], dim=1))

        return self.head(h)

    @torch.no_grad()
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass followed by sigmoid -> pixel probabilities in [0,1]."""
        was_training = self.training
        self.eval()
        try:
            return torch.sigmoid(self.forward(x))
        finally:
            self.train(was_training)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
