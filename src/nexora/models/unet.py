"""Phase 4 (architecture only): 2D U-Net for meniscus segmentation.

Standard encoder-decoder with skip connections. Input  (N, 1, H, W)
normalized slices; output (N, 1, H, W) logits (apply sigmoid externally).
No training logic lives here.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class DoubleConv(nn.Module):
    def __init__(self, c_in: int, c_out: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(c_in, c_out, 3, padding=1, bias=False),
            nn.BatchNorm2d(c_out),
            nn.ReLU(inplace=True),
            nn.Conv2d(c_out, c_out, 3, padding=1, bias=False),
            nn.BatchNorm2d(c_out),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class UNet2D(nn.Module):
    """Minimal U-Net: 4 downsampling levels, base width 32."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1, base: int = 32) -> None:
        super().__init__()
        w = [base, base * 2, base * 4, base * 8]
        self.enc1 = DoubleConv(in_channels, w[0])
        self.enc2 = DoubleConv(w[0], w[1])
        self.enc3 = DoubleConv(w[1], w[2])
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = DoubleConv(w[2], w[3])
        self.up3 = nn.ConvTranspose2d(w[3], w[2], 2, stride=2)
        self.dec3 = DoubleConv(w[3], w[2])
        self.up2 = nn.ConvTranspose2d(w[2], w[1], 2, stride=2)
        self.dec2 = DoubleConv(w[2], w[1])
        self.up1 = nn.ConvTranspose2d(w[1], w[0], 2, stride=2)
        self.dec1 = DoubleConv(w[1], w[0])
        self.head = nn.Conv2d(w[0], out_channels, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        b = self.bottleneck(self.pool(e3))
        d3 = self.dec3(torch.cat([self.up3(b), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.head(d1)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
