"""Configuration for the ARC-native transformer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArcNativeConfig:
    """Shape and model-size settings for ARC-native experiments."""

    canvas_size: int = 30
    num_arc_colors: int = 10
    null_color_id: int = 10
    role_vocab_size: int = 8
    slot_vocab_size: int = 24
    candidate_vocab_size: int = 8

    n_layers: int = 36
    d_model: int = 672
    n_heads: int = 12
    mlp_ratio: int = 4
    dropout: float = 0.0
    attention_dropout: float = 0.0
    layer_norm_eps: float = 1e-5

    use_bias: bool = False
    gradient_checkpointing: bool = False

    @property
    def cell_vocab_size(self) -> int:
        return self.num_arc_colors + 1

    @property
    def num_positions(self) -> int:
        return self.canvas_size * self.canvas_size

    @property
    def head_dim(self) -> int:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return self.d_model // self.n_heads

    @property
    def mlp_hidden_dim(self) -> int:
        return self.d_model * self.mlp_ratio

    @classmethod
    def tiny(cls, *, canvas_size: int = 30) -> "ArcNativeConfig":
        return cls(
            canvas_size=canvas_size,
            n_layers=4,
            d_model=128,
            n_heads=4,
            dropout=0.0,
            attention_dropout=0.0,
        )

    @classmethod
    def smoke(cls, *, canvas_size: int = 4) -> "ArcNativeConfig":
        return cls(
            canvas_size=canvas_size,
            n_layers=2,
            d_model=32,
            n_heads=4,
            slot_vocab_size=24,
            candidate_vocab_size=4,
            dropout=0.0,
            attention_dropout=0.0,
        )

    @classmethod
    def local_100m(cls) -> "ArcNativeConfig":
        return cls(n_layers=28, d_model=576, n_heads=12)

    @classmethod
    def target_200m(cls) -> "ArcNativeConfig":
        # Deep/narrow enough for long ARC contexts while landing near 200M params.
        return cls(n_layers=36, d_model=672, n_heads=12)

    @classmethod
    def wide_220m(cls) -> "ArcNativeConfig":
        # Cleaner 64-dim heads, but less friendly for long full-attention contexts.
        return cls(n_layers=32, d_model=768, n_heads=12)
