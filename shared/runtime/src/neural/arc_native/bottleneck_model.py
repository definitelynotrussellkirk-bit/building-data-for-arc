"""Compressed ARC model with board-level bottleneck encoders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from .bottleneck_tensorize import GRID_FEATURE_NAMES, GRID_FEATURE_VOCAB_SIZES
from .model import RMSNorm, count_parameters


@dataclass(frozen=True)
class ArcBottleneckConfig:
    """Shape and model-size settings for compressed ARC experiments."""

    canvas_size: int = 30
    num_arc_colors: int = 10
    null_color_id: int = 10
    max_context_pairs: int = 5
    max_query_pairs: int = 1

    d_model: int = 256
    n_heads: int = 8
    grid_latents: int = 64
    rule_latents: int | None = None
    grid_conv_layers: int = 3
    grid_latent_layers: int = 2
    pair_layers: int = 2
    rule_layers: int = 2
    decoder_layers: int = 3
    mlp_ratio: int = 4
    dropout: float = 0.0
    attention_dropout: float = 0.0
    layer_norm_eps: float = 1e-5
    use_bias: bool = False
    use_grid_masks: bool = False
    use_grid_features: bool = False
    per_example_cell_loss: bool = False
    dense_canvas_loss: bool = False
    dense_canvas_outside_weight: float = 0.25
    activation_checkpointing: bool = False
    use_copy_edit_decoder: bool = False
    compact_board_dim: int = 128

    cell_loss_weight: float = 1.0
    shape_loss_weight: float = 0.25
    changed_loss_weight: float = 0.25
    inside_loss_weight: float = 0.0
    copy_loss_weight: float = 0.0
    grid_feature_loss_weight: float = 0.0
    compact_board_reconstruction_loss_weight: float = 0.0
    pair_consistency_loss_weight: float = 0.0
    candidate_loss_weight: float = 0.0
    candidate_wrong_loss_weight: float = 0.0
    candidate_repair_loss_weight: float = 0.0
    candidate_inside_loss_weight: float = 0.0

    @property
    def cell_vocab_size(self) -> int:
        return self.num_arc_colors + 1

    @property
    def output_vocab_size(self) -> int:
        """Number of classes emitted at each output-canvas position."""
        return self.cell_vocab_size if self.dense_canvas_loss else self.num_arc_colors

    @property
    def num_positions(self) -> int:
        return self.canvas_size * self.canvas_size

    @property
    def num_rule_latents(self) -> int:
        return self.grid_latents if self.rule_latents is None else self.rule_latents

    @property
    def head_dim(self) -> int:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return self.d_model // self.n_heads

    @property
    def mlp_hidden_dim(self) -> int:
        return self.d_model * self.mlp_ratio

    @classmethod
    def smoke(cls, *, canvas_size: int = 4) -> "ArcBottleneckConfig":
        return cls(
            canvas_size=canvas_size,
            max_context_pairs=2,
            d_model=32,
            n_heads=4,
            grid_latents=4,
            grid_conv_layers=1,
            grid_latent_layers=1,
            pair_layers=1,
            rule_layers=1,
            decoder_layers=1,
            mlp_ratio=2,
        )

    @classmethod
    def small(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=192,
            n_heads=6,
            grid_latents=48,
            grid_conv_layers=3,
            grid_latent_layers=2,
            pair_layers=2,
            rule_layers=2,
            decoder_layers=2,
        )

    @classmethod
    def base(cls) -> "ArcBottleneckConfig":
        return cls()

    @classmethod
    def large(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=384,
            n_heads=12,
            grid_latents=96,
            grid_conv_layers=4,
            grid_latent_layers=3,
            pair_layers=3,
            rule_layers=3,
            decoder_layers=4,
        )

    @classmethod
    def local_80m(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=512,
            n_heads=16,
            grid_latents=128,
            grid_conv_layers=5,
            grid_latent_layers=4,
            pair_layers=4,
            rule_layers=4,
            decoder_layers=6,
        )

    @classmethod
    def arc_200m(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=768,
            n_heads=12,
            grid_latents=128,
            grid_conv_layers=5,
            grid_latent_layers=4,
            pair_layers=4,
            rule_layers=4,
            decoder_layers=6,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def arc_210m_griddeep(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=768,
            n_heads=12,
            grid_latents=192,
            grid_conv_layers=7,
            grid_latent_layers=6,
            pair_layers=4,
            rule_layers=4,
            decoder_layers=6,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def arc_210m_dense_canvas(cls) -> "ArcBottleneckConfig":
        """Scaled bottleneck revival with explicit supervision over all 900 cells."""
        return cls(
            max_context_pairs=10,
            max_query_pairs=4,
            d_model=768,
            n_heads=12,
            grid_latents=192,
            grid_conv_layers=7,
            grid_latent_layers=6,
            pair_layers=4,
            rule_layers=4,
            decoder_layers=6,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            dense_canvas_loss=True,
            dense_canvas_outside_weight=0.25,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def reasoner_180m(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=640,
            n_heads=10,
            grid_latents=160,
            grid_conv_layers=5,
            grid_latent_layers=4,
            pair_layers=7,
            rule_layers=7,
            decoder_layers=8,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def arc_1b_plus(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=1152,
            n_heads=18,
            grid_latents=256,
            grid_conv_layers=8,
            grid_latent_layers=10,
            pair_layers=12,
            rule_layers=12,
            decoder_layers=12,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def arc_1b_exact(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=1152,
            n_heads=18,
            grid_latents=224,
            rule_latents=96,
            grid_conv_layers=6,
            grid_latent_layers=6,
            pair_layers=16,
            rule_layers=16,
            decoder_layers=10,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            use_copy_edit_decoder=True,
            shape_loss_weight=0.5,
            changed_loss_weight=0.25,
            inside_loss_weight=0.5,
            copy_loss_weight=0.5,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )

    @classmethod
    def arc_1b_contest(cls) -> "ArcBottleneckConfig":
        """Contest-faithful 1B-ish model with room for up to 10 demos."""
        return cls(
            max_context_pairs=10,
            max_query_pairs=4,
            d_model=1152,
            n_heads=18,
            grid_latents=192,
            rule_latents=96,
            grid_conv_layers=6,
            grid_latent_layers=6,
            pair_layers=16,
            rule_layers=16,
            decoder_layers=10,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            use_copy_edit_decoder=True,
            shape_loss_weight=0.5,
            changed_loss_weight=0.25,
            inside_loss_weight=0.5,
            copy_loss_weight=0.5,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
            pair_consistency_loss_weight=0.5,
            candidate_loss_weight=0.3,
            candidate_wrong_loss_weight=0.5,
            candidate_repair_loss_weight=0.5,
            candidate_inside_loss_weight=0.3,
        )

    @classmethod
    def arc_2b_plus(cls) -> "ArcBottleneckConfig":
        return cls(
            d_model=1536,
            n_heads=24,
            grid_latents=320,
            grid_conv_layers=10,
            grid_latent_layers=12,
            pair_layers=14,
            rule_layers=14,
            decoder_layers=14,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
            candidate_loss_weight=0.3,
            candidate_wrong_loss_weight=0.5,
            candidate_repair_loss_weight=0.5,
            candidate_inside_loss_weight=0.3,
        )

    @classmethod
    def arc_4b_single4090(cls) -> "ArcBottleneckConfig":
        """4B-ish single-4090 target for bf16 inference / LoRA experiments."""
        return cls(
            max_context_pairs=10,
            max_query_pairs=4,
            d_model=1920,
            n_heads=30,
            grid_latents=256,
            rule_latents=192,
            grid_conv_layers=8,
            grid_latent_layers=8,
            pair_layers=24,
            rule_layers=28,
            decoder_layers=14,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            use_copy_edit_decoder=True,
            shape_loss_weight=0.5,
            changed_loss_weight=0.25,
            inside_loss_weight=0.5,
            copy_loss_weight=0.5,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
            candidate_loss_weight=0.3,
            candidate_wrong_loss_weight=0.5,
            candidate_repair_loss_weight=0.5,
            candidate_inside_loss_weight=0.3,
        )

    @classmethod
    def arc_5b_single4090(cls) -> "ArcBottleneckConfig":
        """5B-ish stretch target for single-4090 bf16 inference / LoRA probes."""
        return cls(
            max_context_pairs=10,
            max_query_pairs=4,
            d_model=2048,
            n_heads=32,
            grid_latents=256,
            rule_latents=192,
            grid_conv_layers=8,
            grid_latent_layers=8,
            pair_layers=24,
            rule_layers=32,
            decoder_layers=16,
            use_grid_masks=True,
            use_grid_features=True,
            per_example_cell_loss=True,
            use_copy_edit_decoder=True,
            shape_loss_weight=0.5,
            changed_loss_weight=0.25,
            inside_loss_weight=0.5,
            copy_loss_weight=0.5,
            grid_feature_loss_weight=0.05,
            compact_board_reconstruction_loss_weight=0.05,
        )


@dataclass
class ArcBottleneckOutput:
    logits: torch.Tensor
    height_logits: torch.Tensor
    width_logits: torch.Tensor
    changed_logits: torch.Tensor
    inside_logits: Optional[torch.Tensor] = None
    copy_logits: Optional[torch.Tensor] = None
    pair_consistency_logits: Optional[torch.Tensor] = None
    candidate_correct_logits: Optional[torch.Tensor] = None
    candidate_wrong_logits: Optional[torch.Tensor] = None
    candidate_repair_logits: Optional[torch.Tensor] = None
    candidate_inside_logits: Optional[torch.Tensor] = None
    feature_logits: Optional[list[torch.Tensor]] = None
    loss: Optional[torch.Tensor] = None
    cell_loss: Optional[torch.Tensor] = None
    inside_cell_loss: Optional[torch.Tensor] = None
    outside_cell_loss: Optional[torch.Tensor] = None
    shape_loss: Optional[torch.Tensor] = None
    changed_loss: Optional[torch.Tensor] = None
    inside_loss: Optional[torch.Tensor] = None
    copy_loss: Optional[torch.Tensor] = None
    feature_loss: Optional[torch.Tensor] = None
    compact_board_reconstruction_loss: Optional[torch.Tensor] = None
    pair_consistency_loss: Optional[torch.Tensor] = None
    candidate_loss: Optional[torch.Tensor] = None
    candidate_wrong_loss: Optional[torch.Tensor] = None
    candidate_repair_loss: Optional[torch.Tensor] = None
    candidate_inside_loss: Optional[torch.Tensor] = None


class CrossAttention(nn.Module):
    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.head_dim = config.head_dim
        self.q = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.k = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.v = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.out = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.dropout = config.attention_dropout

    def _reshape(self, x: torch.Tensor) -> torch.Tensor:
        bsz, seq_len, dim = x.shape
        return x.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

    def forward(
        self,
        query: torch.Tensor,
        context: torch.Tensor,
        *,
        context_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        q = self._reshape(self.q(query))
        k = self._reshape(self.k(context))
        v = self._reshape(self.v(context))
        attn_mask = None
        if context_mask is not None:
            attn_mask = context_mask[:, None, None, :].to(torch.bool)
        y = F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=attn_mask,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=False,
        )
        y = y.transpose(1, 2).contiguous().view(query.shape)
        return self.out(y)


class SelfAttention(nn.Module):
    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.head_dim = config.head_dim
        self.qkv = nn.Linear(config.d_model, config.d_model * 3, bias=config.use_bias)
        self.out = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.dropout = config.attention_dropout

    def forward(self, x: torch.Tensor, *, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        bsz, seq_len, dim = x.shape
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        def reshape(t: torch.Tensor) -> torch.Tensor:
            return t.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        q, k, v = reshape(q), reshape(k), reshape(v)
        attn_mask = None
        if mask is not None:
            attn_mask = mask[:, None, None, :].to(torch.bool)
        y = F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=attn_mask,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=False,
        )
        y = y.transpose(1, 2).contiguous().view(bsz, seq_len, dim)
        y = self.out(y)
        if mask is not None:
            y = y * mask[:, :, None].to(y.dtype)
        return y


class FeedForward(nn.Module):
    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        self.up = nn.Linear(config.d_model, config.mlp_hidden_dim, bias=config.use_bias)
        self.down = nn.Linear(config.mlp_hidden_dim, config.d_model, bias=config.use_bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(self.dropout(F.gelu(self.up(x), approximate="tanh")))


class SelfAttentionBlock(nn.Module):
    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        self.attn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.attn = SelfAttention(config)
        self.ffn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, *, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.attn_norm(x), mask=mask))
        x = x + self.dropout(self.ffn(self.ffn_norm(x)))
        if mask is not None:
            x = x * mask[:, :, None].to(x.dtype)
        return x


class CrossAttentionBlock(nn.Module):
    def __init__(self, config: ArcBottleneckConfig, *, self_attention: bool = False) -> None:
        super().__init__()
        self.cross_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.context_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.cross = CrossAttention(config)
        self.self_block = SelfAttentionBlock(config) if self_attention else None
        self.ffn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        x: torch.Tensor,
        context: torch.Tensor,
        *,
        context_mask: Optional[torch.Tensor] = None,
        self_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        x = x + self.dropout(
            self.cross(
                self.cross_norm(x),
                self.context_norm(context),
                context_mask=context_mask,
            )
        )
        if self.self_block is not None:
            x = self.self_block(x, mask=self_mask)
        x = x + self.dropout(self.ffn(self.ffn_norm(x)))
        if self_mask is not None:
            x = x * self_mask[:, :, None].to(x.dtype)
        return x


def maybe_checkpoint(
    module: nn.Module,
    *args: torch.Tensor,
    enabled: bool,
    **kwargs,
) -> torch.Tensor:
    if not enabled:
        return module(*args, **kwargs)
    return checkpoint(
        lambda *inner_args: module(*inner_args, **kwargs),
        *args,
        use_reentrant=False,
    )


class ConvBlock(nn.Module):
    def __init__(self, dim: int) -> None:
        super().__init__()
        self.norm = nn.GroupNorm(1, dim)
        self.depthwise = nn.Conv2d(dim, dim, kernel_size=3, padding=1, groups=dim)
        self.pointwise = nn.Conv2d(dim, dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.norm(x)
        y = F.gelu(self.depthwise(y), approximate="tanh")
        y = self.pointwise(y)
        return x + y


class GridEncoder(nn.Module):
    """Encode each padded grid into a small learned latent set."""

    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        self.config = config
        self.color_embedding = nn.Embedding(config.cell_vocab_size, config.d_model)
        self.row_embedding = nn.Embedding(config.canvas_size, config.d_model)
        self.col_embedding = nn.Embedding(config.canvas_size, config.d_model)
        self.role_embedding = nn.Embedding(4, config.d_model)
        self.mask_embedding = nn.Embedding(2, config.d_model) if config.use_grid_masks else None
        if config.use_grid_features:
            self.feature_embeddings = nn.ModuleList(
                [nn.Embedding(vocab_size, config.d_model) for vocab_size in GRID_FEATURE_VOCAB_SIZES]
            )
        else:
            self.feature_embeddings = None
        self.input_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.conv_blocks = nn.ModuleList([ConvBlock(config.d_model) for _ in range(config.grid_conv_layers)])
        self.latent_queries = nn.Parameter(torch.randn(config.grid_latents, config.d_model) * 0.02)
        self.cross = CrossAttentionBlock(config, self_attention=False)
        self.latent_blocks = nn.ModuleList(
            [SelfAttentionBlock(config) for _ in range(config.grid_latent_layers)]
        )

        rows = torch.arange(config.canvas_size).repeat_interleave(config.canvas_size)
        cols = torch.arange(config.canvas_size).repeat(config.canvas_size)
        self.register_buffer("row_ids", rows, persistent=False)
        self.register_buffer("col_ids", cols, persistent=False)

    def _fallback_mask(self, flat_ids: torch.Tensor) -> torch.Tensor:
        return flat_ids != self.config.null_color_id

    def forward(
        self,
        board_ids: torch.Tensor,
        board_roles: torch.Tensor,
        board_masks: Optional[torch.Tensor] = None,
        board_features: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bsz, num_boards, num_cells = board_ids.shape
        if num_cells != self.config.num_positions:
            raise ValueError(f"expected {self.config.num_positions} cells, got {num_cells}")

        flat_ids = board_ids.reshape(bsz * num_boards, num_cells)
        flat_roles = board_roles.reshape(bsz * num_boards)
        flat_mask = None
        context_mask = None
        if self.config.use_grid_masks:
            if board_masks is None:
                flat_mask = self._fallback_mask(flat_ids)
            else:
                flat_mask = board_masks.reshape(bsz * num_boards, num_cells).to(torch.bool)
            context_mask = flat_mask
            empty_boards = ~context_mask.any(dim=1)
            if empty_boards.any():
                context_mask = context_mask.clone()
                context_mask[empty_boards, 0] = True
        x = (
            self.color_embedding(flat_ids)
            + self.row_embedding(self.row_ids)[None, :, :]
            + self.col_embedding(self.col_ids)[None, :, :]
            + self.role_embedding(flat_roles)[:, None, :]
        )
        if self.mask_embedding is not None and flat_mask is not None:
            x = x + self.mask_embedding(flat_mask.to(torch.long))
        if self.feature_embeddings is not None and board_features is not None:
            if board_features.shape[:3] != board_ids.shape:
                raise ValueError(
                    f"board_features shape {board_features.shape} does not match board_ids {board_ids.shape}"
                )
            flat_features = board_features.reshape(bsz * num_boards, num_cells, -1)
            if flat_features.shape[-1] != len(self.feature_embeddings):
                raise ValueError(
                    f"expected {len(self.feature_embeddings)} grid feature channels, "
                    f"got {flat_features.shape[-1]}"
                )
            for idx, embedding in enumerate(self.feature_embeddings):
                feature_ids = flat_features[..., idx].clamp(0, embedding.num_embeddings - 1)
                x = x + embedding(feature_ids)
        x = self.input_norm(x)
        if flat_mask is not None:
            x = x * flat_mask[:, :, None].to(x.dtype)
        h = self.config.canvas_size
        mask2d = None
        if flat_mask is not None:
            mask2d = flat_mask[:, None, :].reshape(bsz * num_boards, 1, h, h).to(x.dtype)
        x2d = x.transpose(1, 2).reshape(bsz * num_boards, self.config.d_model, h, h)
        for block in self.conv_blocks:
            x2d = maybe_checkpoint(
                block,
                x2d,
                enabled=self.config.activation_checkpointing and self.training,
            )
            if mask2d is not None:
                x2d = x2d * mask2d
        x = x2d.reshape(bsz * num_boards, self.config.d_model, num_cells).transpose(1, 2)

        latents = self.latent_queries[None, :, :].expand(bsz * num_boards, -1, -1)
        latents = maybe_checkpoint(
            self.cross,
            latents,
            x,
            enabled=self.config.activation_checkpointing and self.training,
            context_mask=context_mask,
        )
        for block in self.latent_blocks:
            latents = maybe_checkpoint(
                block,
                latents,
                enabled=self.config.activation_checkpointing and self.training,
            )
        return latents.reshape(bsz, num_boards, self.config.grid_latents, self.config.d_model)


class ArcBottleneckModel(nn.Module):
    """ARC model that reasons over compressed per-board latents."""

    def __init__(self, config: ArcBottleneckConfig) -> None:
        super().__init__()
        _ = config.head_dim
        if config.dense_canvas_outside_weight < 0:
            raise ValueError("dense_canvas_outside_weight must be non-negative")
        if config.dense_canvas_loss and config.null_color_id != config.num_arc_colors:
            raise ValueError("dense canvas output requires null_color_id == num_arc_colors")
        if config.dense_canvas_loss and config.use_copy_edit_decoder:
            raise ValueError("dense canvas output is not compatible with the 10-way copy/edit mixer")
        self.config = config
        self.grid_encoder = GridEncoder(config)
        self.pair_slot_embedding = nn.Embedding(config.max_context_pairs, config.d_model)
        self.latent_position_embedding = nn.Embedding(config.grid_latents, config.d_model)
        self.pair_mlp = nn.Sequential(
            nn.Linear(config.d_model * 4, config.d_model, bias=config.use_bias),
            nn.GELU(approximate="tanh"),
            nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
        )
        self.pair_blocks = nn.ModuleList([SelfAttentionBlock(config) for _ in range(config.pair_layers)])
        if config.pair_consistency_loss_weight > 0:
            self.pair_consistency_head = nn.Linear(config.d_model, 1, bias=True)
            self.pair_consistency_none_head = nn.Linear(config.d_model, 1, bias=True)
        else:
            self.pair_consistency_head = None
            self.pair_consistency_none_head = None
        use_candidate_heads = (
            config.candidate_loss_weight > 0
            or config.candidate_wrong_loss_weight > 0
            or config.candidate_repair_loss_weight > 0
            or config.candidate_inside_loss_weight > 0
        )
        if use_candidate_heads:
            self.candidate_verifier = nn.Sequential(
                nn.Linear(config.d_model * 4, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(config.d_model, 1, bias=True),
            )
            self.candidate_cell_embedding = nn.Embedding(config.cell_vocab_size, config.d_model)
            self.candidate_compare = nn.Sequential(
                nn.Linear(config.d_model * 2, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
            )
            self.candidate_wrong_head = nn.Linear(config.d_model, 1, bias=True)
            self.candidate_repair_head = nn.Linear(config.d_model, config.num_arc_colors, bias=True)
            self.candidate_inside_head = nn.Linear(config.d_model, 1, bias=True)
        else:
            self.candidate_verifier = None
            self.candidate_cell_embedding = None
            self.candidate_compare = None
            self.candidate_wrong_head = None
            self.candidate_repair_head = None
            self.candidate_inside_head = None

        self.rule_queries = nn.Parameter(torch.randn(config.num_rule_latents, config.d_model) * 0.02)
        self.rule_cross = CrossAttentionBlock(config, self_attention=False)
        self.rule_blocks = nn.ModuleList([SelfAttentionBlock(config) for _ in range(config.rule_layers)])

        self.output_position_embedding = nn.Embedding(config.num_positions, config.d_model)
        self.output_role = nn.Parameter(torch.randn(config.d_model) * 0.02)
        self.decoder_blocks = nn.ModuleList(
            [CrossAttentionBlock(config, self_attention=True) for _ in range(config.decoder_layers)]
        )
        self.final_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.cell_head = nn.Linear(config.d_model, config.output_vocab_size, bias=True)
        self.changed_head = nn.Linear(config.d_model, 1, bias=True)
        self.copy_head = nn.Linear(config.d_model, 1, bias=True) if config.use_copy_edit_decoder else None
        self.inside_head = nn.Linear(config.d_model, 1, bias=True) if config.use_copy_edit_decoder else None
        if config.grid_feature_loss_weight > 0:
            self.feature_heads = nn.ModuleList(
                [nn.Linear(config.d_model, vocab_size, bias=True) for vocab_size in GRID_FEATURE_VOCAB_SIZES]
            )
        else:
            self.feature_heads = None
        if config.compact_board_reconstruction_loss_weight > 0:
            self.board_recon_down = nn.Linear(config.d_model, config.compact_board_dim, bias=config.use_bias)
            self.board_recon_up = nn.Linear(config.compact_board_dim, config.d_model, bias=config.use_bias)
            self.board_recon_position_embedding = nn.Embedding(config.num_positions, config.d_model)
            self.board_recon_head = nn.Linear(config.d_model, config.cell_vocab_size, bias=True)
        else:
            self.board_recon_down = None
            self.board_recon_up = None
            self.board_recon_position_embedding = None
            self.board_recon_head = None
        self.height_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        self.width_head = nn.Linear(config.d_model, config.canvas_size, bias=True)

        pos = torch.arange(config.num_positions)
        self.register_buffer("position_ids", pos, persistent=False)
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def _encode_boards(
        self,
        demo_input_ids: torch.Tensor,
        demo_output_ids: torch.Tensor,
        query_input_ids: torch.Tensor,
        demo_input_masks: Optional[torch.Tensor] = None,
        demo_output_masks: Optional[torch.Tensor] = None,
        query_input_mask: Optional[torch.Tensor] = None,
        demo_input_features: Optional[torch.Tensor] = None,
        demo_output_features: Optional[torch.Tensor] = None,
        query_input_features: Optional[torch.Tensor] = None,
        candidate_output_ids: Optional[torch.Tensor] = None,
        candidate_output_mask: Optional[torch.Tensor] = None,
        candidate_output_features: Optional[torch.Tensor] = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, Optional[torch.Tensor]]:
        bsz, pairs, _ = demo_input_ids.shape
        if query_input_ids.dim() == 2:
            query_input_ids = query_input_ids[:, None, :]
            if query_input_mask is not None:
                query_input_mask = query_input_mask[:, None, :]
            if query_input_features is not None:
                query_input_features = query_input_features[:, None, :, :]
        if candidate_output_ids is not None and candidate_output_ids.dim() == 2:
            candidate_output_ids = candidate_output_ids[:, None, :]
            if candidate_output_mask is not None:
                candidate_output_mask = candidate_output_mask[:, None, :]
            if candidate_output_features is not None:
                candidate_output_features = candidate_output_features[:, None, :, :]
        queries = query_input_ids.shape[1]
        board_parts = [demo_input_ids, demo_output_ids, query_input_ids]
        role_parts = [
            torch.full((bsz, pairs), 0, device=demo_input_ids.device, dtype=torch.long),
            torch.full((bsz, pairs), 1, device=demo_input_ids.device, dtype=torch.long),
            torch.full((bsz, queries), 2, device=demo_input_ids.device, dtype=torch.long),
        ]
        if candidate_output_ids is not None:
            if candidate_output_ids.shape[1] != queries:
                raise ValueError(
                    f"candidate query slots {candidate_output_ids.shape[1]} != query slots {queries}"
                )
            board_parts.append(candidate_output_ids)
            role_parts.append(torch.full((bsz, queries), 3, device=demo_input_ids.device, dtype=torch.long))
        boards = torch.cat(board_parts, dim=1)
        roles = torch.cat(role_parts, dim=1)
        features = None
        if self.config.use_grid_features:
            if (
                demo_input_features is not None
                and demo_output_features is not None
                and query_input_features is not None
            ):
                feature_parts = [demo_input_features, demo_output_features, query_input_features]
                if candidate_output_ids is not None:
                    if candidate_output_features is None:
                        candidate_output_features = torch.zeros(
                            (
                                bsz,
                                queries,
                                self.config.num_positions,
                                len(GRID_FEATURE_NAMES),
                            ),
                            device=demo_input_ids.device,
                            dtype=torch.long,
                        )
                    feature_parts.append(candidate_output_features)
                features = torch.cat(feature_parts, dim=1)
        masks = None
        if self.config.use_grid_masks:
            if demo_input_masks is not None and demo_output_masks is not None and query_input_mask is not None:
                mask_parts = [demo_input_masks, demo_output_masks, query_input_mask]
                if candidate_output_ids is not None:
                    if candidate_output_mask is None:
                        candidate_output_mask = candidate_output_ids != self.config.null_color_id
                    mask_parts.append(candidate_output_mask)
                masks = torch.cat(mask_parts, dim=1)
            else:
                masks = boards != self.config.null_color_id
        encoded = self.grid_encoder(boards, roles, masks, features)
        query_start = 2 * pairs
        candidate_start = query_start + queries
        candidate = encoded[:, candidate_start : candidate_start + queries] if candidate_output_ids is not None else None
        return encoded[:, :pairs], encoded[:, pairs : 2 * pairs], encoded[:, query_start:candidate_start], candidate

    def _compact_board_reconstruction_loss(
        self,
        board_latents: torch.Tensor,
        board_ids: torch.Tensor,
        board_active: torch.Tensor,
    ) -> Optional[torch.Tensor]:
        if (
            self.board_recon_down is None
            or self.board_recon_up is None
            or self.board_recon_position_embedding is None
            or self.board_recon_head is None
        ):
            return None
        active = board_active.to(torch.bool)
        if not active.any():
            return None
        compact = self.board_recon_down(board_latents)
        compact = F.gelu(compact, approximate="tanh")
        restored = self.board_recon_up(compact)
        summary = restored.mean(dim=2)
        pos = self.board_recon_position_embedding(self.position_ids)
        recon_tokens = summary[:, :, None, :] + pos[None, None, :, :]
        logits = self.board_recon_head(recon_tokens)
        raw_loss = F.cross_entropy(
            logits.reshape(-1, self.config.cell_vocab_size),
            board_ids.reshape(-1),
            reduction="none",
        ).reshape(board_ids.shape)
        per_board_loss = raw_loss.mean(dim=-1)
        return per_board_loss[active].mean()

    def _pair_tokens(
        self,
        demo_input_latents: torch.Tensor,
        demo_output_latents: torch.Tensor,
        pair_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        bsz, pairs, latents, _ = demo_input_latents.shape
        features = torch.cat(
            [
                demo_input_latents,
                demo_output_latents,
                demo_output_latents - demo_input_latents,
                demo_input_latents * demo_output_latents,
            ],
            dim=-1,
        )
        tokens = self.pair_mlp(features)
        pair_ids = torch.arange(pairs, device=tokens.device)
        latent_ids = torch.arange(latents, device=tokens.device)
        tokens = (
            tokens
            + self.pair_slot_embedding(pair_ids)[None, :, None, :]
            + self.latent_position_embedding(latent_ids)[None, None, :, :]
        )
        tokens = tokens.reshape(bsz, pairs * latents, self.config.d_model)
        token_mask = pair_mask[:, :, None].expand(bsz, pairs, latents).reshape(bsz, pairs * latents)
        tokens = tokens * token_mask[:, :, None].to(tokens.dtype)
        for block in self.pair_blocks:
            tokens = maybe_checkpoint(
                block,
                tokens,
                enabled=self.config.activation_checkpointing and self.training,
                mask=token_mask,
            )
        pair_summary = tokens.reshape(bsz, pairs, latents, self.config.d_model).mean(dim=2)
        pair_summary = pair_summary * pair_mask[:, :, None].to(pair_summary.dtype)
        return tokens, token_mask, pair_summary

    def _rule_tokens(self, pair_tokens: torch.Tensor, pair_token_mask: torch.Tensor) -> torch.Tensor:
        bsz = pair_tokens.shape[0]
        rule = self.rule_queries[None, :, :].expand(bsz, -1, -1)
        rule = maybe_checkpoint(
            self.rule_cross,
            rule,
            pair_tokens,
            enabled=self.config.activation_checkpointing and self.training,
            context_mask=pair_token_mask,
        )
        for block in self.rule_blocks:
            rule = maybe_checkpoint(
                block,
                rule,
                enabled=self.config.activation_checkpointing and self.training,
            )
        return rule

    def forward(
        self,
        demo_input_ids: torch.Tensor,
        demo_output_ids: torch.Tensor,
        pair_mask: torch.Tensor,
        query_input_ids: torch.Tensor,
        query_mask: Optional[torch.Tensor] = None,
        demo_input_masks: Optional[torch.Tensor] = None,
        demo_output_masks: Optional[torch.Tensor] = None,
        query_input_mask: Optional[torch.Tensor] = None,
        demo_input_features: Optional[torch.Tensor] = None,
        demo_output_features: Optional[torch.Tensor] = None,
        query_input_features: Optional[torch.Tensor] = None,
        candidate_output_ids: Optional[torch.Tensor] = None,
        candidate_output_mask: Optional[torch.Tensor] = None,
        candidate_output_features: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        height_labels: Optional[torch.Tensor] = None,
        width_labels: Optional[torch.Tensor] = None,
        changed_labels: Optional[torch.Tensor] = None,
        feature_labels: Optional[torch.Tensor] = None,
        pair_consistency_labels: Optional[torch.Tensor] = None,
        candidate_correct_labels: Optional[torch.Tensor] = None,
        candidate_wrong_labels: Optional[torch.Tensor] = None,
        candidate_repair_labels: Optional[torch.Tensor] = None,
        candidate_inside_labels: Optional[torch.Tensor] = None,
    ) -> ArcBottleneckOutput:
        squeeze_query_dim = query_input_ids.dim() == 2
        if squeeze_query_dim:
            query_input_ids = query_input_ids[:, None, :]
            if query_mask is not None and query_mask.dim() == 1:
                query_mask = query_mask[:, None]
            if query_input_mask is not None:
                query_input_mask = query_input_mask[:, None, :]
            if query_input_features is not None:
                query_input_features = query_input_features[:, None, :, :]
            if candidate_output_ids is not None:
                candidate_output_ids = candidate_output_ids[:, None, :]
            if candidate_output_mask is not None:
                candidate_output_mask = candidate_output_mask[:, None, :]
            if candidate_output_features is not None:
                candidate_output_features = candidate_output_features[:, None, :, :]
            if labels is not None:
                labels = labels[:, None, :]
            if changed_labels is not None:
                changed_labels = changed_labels[:, None, :]
            if feature_labels is not None:
                feature_labels = feature_labels[:, None, :, :]
            if height_labels is not None:
                height_labels = height_labels[:, None]
            if width_labels is not None:
                width_labels = width_labels[:, None]
            if candidate_correct_labels is not None and candidate_correct_labels.dim() == 1:
                candidate_correct_labels = candidate_correct_labels[:, None]
            if candidate_wrong_labels is not None:
                candidate_wrong_labels = candidate_wrong_labels[:, None, :]
            if candidate_repair_labels is not None:
                candidate_repair_labels = candidate_repair_labels[:, None, :]
            if candidate_inside_labels is not None:
                candidate_inside_labels = candidate_inside_labels[:, None, :]

        demo_in, demo_out, query, candidate = self._encode_boards(
            demo_input_ids,
            demo_output_ids,
            query_input_ids,
            demo_input_masks=demo_input_masks,
            demo_output_masks=demo_output_masks,
            query_input_mask=query_input_mask,
            demo_input_features=demo_input_features,
            demo_output_features=demo_output_features,
            query_input_features=query_input_features,
            candidate_output_ids=candidate_output_ids,
            candidate_output_mask=candidate_output_mask,
            candidate_output_features=candidate_output_features,
        )
        pair_tokens, pair_token_mask, pair_summary = self._pair_tokens(demo_in, demo_out, pair_mask)
        rule = self._rule_tokens(pair_tokens, pair_token_mask)

        bsz, queries, query_latents, dim = query.shape
        flat_query = query.reshape(bsz * queries, query_latents, dim)
        flat_rule = rule[:, None, :, :].expand(bsz, queries, -1, -1).reshape(
            bsz * queries,
            rule.shape[1],
            dim,
        )
        memory = torch.cat([flat_rule, flat_query], dim=1)

        x = self.output_position_embedding(self.position_ids)[None, :, :].expand(bsz * queries, -1, -1)
        x = x + self.output_role[None, None, :]
        for block in self.decoder_blocks:
            x = maybe_checkpoint(
                block,
                x,
                memory,
                enabled=self.config.activation_checkpointing and self.training,
            )
        x = self.final_norm(x)
        decoder_states = x.reshape(bsz, queries, self.config.num_positions, self.config.d_model)

        write_logits = self.cell_head(x)
        changed_logits = self.changed_head(x).squeeze(-1)
        copy_logits = self.copy_head(x).squeeze(-1) if self.copy_head is not None else None
        inside_logits = self.inside_head(x).squeeze(-1) if self.inside_head is not None else None
        feature_logits = (
            [head(x) for head in self.feature_heads]
            if self.feature_heads is not None and feature_labels is not None
            else None
        )
        write_logits = write_logits.reshape(
            bsz,
            queries,
            self.config.num_positions,
            self.config.output_vocab_size,
        )
        changed_logits = changed_logits.reshape(bsz, queries, self.config.num_positions)
        if copy_logits is not None:
            copy_logits = copy_logits.reshape(bsz, queries, self.config.num_positions)
        if inside_logits is not None:
            inside_logits = inside_logits.reshape(bsz, queries, self.config.num_positions)
        if feature_logits is not None:
            feature_logits = [
                logits_for_feature.reshape(bsz, queries, self.config.num_positions, -1)
                for logits_for_feature in feature_logits
            ]
        logits = write_logits
        if self.config.use_copy_edit_decoder and copy_logits is not None:
            query_valid = (
                query_input_mask.to(write_logits.dtype)
                if query_input_mask is not None
                else (query_input_ids != self.config.null_color_id).to(write_logits.dtype)
            )
            clamped_query = query_input_ids.clamp(0, self.config.num_arc_colors - 1)
            query_one_hot = F.one_hot(clamped_query, num_classes=self.config.num_arc_colors).to(write_logits.dtype)
            copy_prob = torch.sigmoid(copy_logits) * query_valid
            write_probs = F.softmax(write_logits, dim=-1)
            mixed_probs = copy_prob[..., None] * query_one_hot + (1.0 - copy_prob[..., None]) * write_probs
            logits = torch.log(mixed_probs.clamp_min(1e-8))
        pooled = memory.mean(dim=1)
        height_logits = self.height_head(pooled).reshape(bsz, queries, self.config.canvas_size)
        width_logits = self.width_head(pooled).reshape(bsz, queries, self.config.canvas_size)
        pair_consistency_logits = None
        if self.pair_consistency_head is not None and self.pair_consistency_none_head is not None:
            pair_scores = self.pair_consistency_head(pair_summary).squeeze(-1)
            pair_scores = pair_scores.masked_fill(~pair_mask.to(torch.bool), -1e4)
            none_score = self.pair_consistency_none_head(rule.mean(dim=1))
            pair_consistency_logits = torch.cat([pair_scores, none_score], dim=1)
        candidate_correct_logits = None
        candidate_wrong_logits = None
        candidate_repair_logits = None
        candidate_inside_logits = None
        if self.candidate_verifier is not None and candidate is not None:
            rule_summary = rule.mean(dim=1)
            query_summary = query.mean(dim=2)
            candidate_summary = candidate.mean(dim=2)
            rule_summary = rule_summary[:, None, :].expand(bsz, queries, -1)
            verifier_features = torch.cat(
                [
                    rule_summary,
                    query_summary,
                    candidate_summary,
                    candidate_summary - query_summary,
                ],
                dim=-1,
            )
            candidate_correct_logits = self.candidate_verifier(verifier_features).squeeze(-1)
            if (
                self.candidate_cell_embedding is not None
                and self.candidate_compare is not None
                and self.candidate_wrong_head is not None
                and self.candidate_repair_head is not None
                and self.candidate_inside_head is not None
                and candidate_output_ids is not None
            ):
                candidate_ids = candidate_output_ids.clamp(0, self.config.cell_vocab_size - 1)
                candidate_cell_states = self.candidate_cell_embedding(candidate_ids)
                verifier_states = self.candidate_compare(
                    torch.cat([decoder_states, candidate_cell_states], dim=-1)
                )
                candidate_wrong_logits = self.candidate_wrong_head(verifier_states).squeeze(-1)
                candidate_repair_logits = self.candidate_repair_head(verifier_states)
                candidate_inside_logits = self.candidate_inside_head(verifier_states).squeeze(-1)

        cell_loss = None
        inside_cell_loss = None
        outside_cell_loss = None
        shape_loss = None
        changed_loss = None
        inside_loss = None
        copy_loss = None
        feature_loss = None
        compact_board_reconstruction_loss = None
        pair_consistency_loss = None
        candidate_loss = None
        candidate_wrong_loss = None
        candidate_repair_loss = None
        candidate_inside_loss = None
        loss = None
        if labels is not None:
            if self.config.dense_canvas_loss:
                flat_labels = labels.reshape(-1, self.config.num_positions)
                flat_logits = logits.reshape(
                    -1,
                    self.config.num_positions,
                    self.config.output_vocab_size,
                )
                inside_mask = flat_labels != -100
                if query_mask is not None:
                    active_queries = query_mask.reshape(-1).to(torch.bool)
                else:
                    active_queries = inside_mask.any(dim=1)
                dense_targets = torch.where(
                    inside_mask,
                    flat_labels,
                    torch.full_like(flat_labels, self.config.null_color_id),
                )
                raw_dense_loss = F.cross_entropy(
                    flat_logits.reshape(-1, self.config.output_vocab_size),
                    dense_targets.reshape(-1),
                    reduction="none",
                ).reshape(flat_labels.shape)
                inside_per_query = (
                    (raw_dense_loss * inside_mask).sum(dim=1)
                    / inside_mask.sum(dim=1).clamp_min(1)
                )
                outside_mask = (~inside_mask) & active_queries[:, None]
                outside_count = outside_mask.sum(dim=1)
                outside_per_query = (
                    (raw_dense_loss * outside_mask).sum(dim=1)
                    / outside_count.clamp_min(1)
                )
                inside_cell_loss = inside_per_query[active_queries].mean()
                outside_active = active_queries & (outside_count > 0)
                if outside_active.any():
                    outside_cell_loss = outside_per_query[outside_active].mean()
                else:
                    outside_cell_loss = raw_dense_loss.new_zeros(())
                weight = self.config.dense_canvas_outside_weight
                combined_per_query = torch.where(
                    outside_count > 0,
                    (inside_per_query + weight * outside_per_query) / (1.0 + weight),
                    inside_per_query,
                )
                cell_loss = combined_per_query[active_queries].mean()
            elif self.config.per_example_cell_loss:
                raw_cell_loss = F.cross_entropy(
                    logits.reshape(-1, self.config.num_arc_colors),
                    labels.reshape(-1),
                    ignore_index=-100,
                    reduction="none",
                ).reshape(labels.shape)
                label_mask = labels != -100
                flat_label_mask = label_mask.reshape(-1, self.config.num_positions)
                flat_raw_cell_loss = raw_cell_loss.reshape(-1, self.config.num_positions)
                active_queries = flat_label_mask.any(dim=1)
                per_example_loss = (
                    flat_raw_cell_loss.sum(dim=1) / flat_label_mask.sum(dim=1).clamp_min(1)
                )
                cell_loss = per_example_loss[active_queries].mean()
            else:
                cell_loss = F.cross_entropy(
                    logits.reshape(-1, self.config.num_arc_colors),
                    labels.reshape(-1),
                    ignore_index=-100,
                )
            loss = self.config.cell_loss_weight * cell_loss
            if self.config.use_copy_edit_decoder and inside_logits is not None:
                inside_targets = (labels != -100).to(inside_logits.dtype)
                inside_loss = F.binary_cross_entropy_with_logits(inside_logits, inside_targets)
                loss = loss + self.config.inside_loss_weight * inside_loss
            if (
                self.config.use_copy_edit_decoder
                and copy_logits is not None
                and query_input_mask is not None
            ):
                label_mask = labels != -100
                same_cell = query_input_ids.clamp(0, self.config.num_arc_colors - 1) == labels.clamp_min(0)
                copy_targets = (label_mask & query_input_mask.to(torch.bool) & same_cell).to(copy_logits.dtype)
                raw_copy = F.binary_cross_entropy_with_logits(
                    copy_logits,
                    copy_targets,
                    reduction="none",
                )
                copy_loss = raw_copy[label_mask].mean()
                loss = loss + self.config.copy_loss_weight * copy_loss
        if feature_labels is not None and feature_logits is not None:
            losses = []
            for idx, logits_for_feature in enumerate(feature_logits):
                target = feature_labels[..., idx]
                if (target != -100).any():
                    losses.append(
                        F.cross_entropy(
                            logits_for_feature.reshape(-1, logits_for_feature.shape[-1]),
                            target.reshape(-1),
                            ignore_index=-100,
                        )
                    )
            if losses:
                feature_loss = torch.stack(losses).mean()
                loss = (
                    self.config.grid_feature_loss_weight * feature_loss
                    if loss is None
                    else loss + self.config.grid_feature_loss_weight * feature_loss
                )
        if self.config.compact_board_reconstruction_loss_weight > 0 and labels is not None:
            bsz, pairs, cells = demo_input_ids.shape
            board_latents = torch.cat([demo_in, demo_out, query], dim=1)
            board_ids = torch.cat([demo_input_ids, demo_output_ids, query_input_ids], dim=1)
            if query_mask is not None:
                query_active = query_mask.to(torch.bool)
            elif query_input_mask is not None:
                query_active = query_input_mask.to(torch.bool).any(dim=-1)
            else:
                query_active = torch.ones((bsz, queries), device=pair_mask.device, dtype=torch.bool)
            board_active = torch.cat([pair_mask.to(torch.bool), pair_mask.to(torch.bool), query_active], dim=1)
            compact_board_reconstruction_loss = self._compact_board_reconstruction_loss(
                board_latents,
                board_ids,
                board_active,
            )
            if compact_board_reconstruction_loss is not None:
                loss = (
                    self.config.compact_board_reconstruction_loss_weight * compact_board_reconstruction_loss
                    if loss is None
                    else loss
                    + self.config.compact_board_reconstruction_loss_weight * compact_board_reconstruction_loss
                )
        if height_labels is not None and width_labels is not None:
            shape_loss = (
                F.cross_entropy(
                    height_logits.reshape(-1, self.config.canvas_size),
                    height_labels.reshape(-1),
                    ignore_index=-100,
                )
                + F.cross_entropy(
                    width_logits.reshape(-1, self.config.canvas_size),
                    width_labels.reshape(-1),
                    ignore_index=-100,
                )
            ) * 0.5
            loss = (
                self.config.shape_loss_weight * shape_loss
                if loss is None
                else loss + self.config.shape_loss_weight * shape_loss
            )
        if changed_labels is not None:
            changed_mask = changed_labels != -100
            if changed_mask.any():
                changed_targets = changed_labels.to(changed_logits.dtype)
                raw_changed = F.binary_cross_entropy_with_logits(
                    changed_logits,
                    changed_targets.clamp_min(0),
                    reduction="none",
                )
                changed_loss = raw_changed[changed_mask].mean()
                loss = (
                    self.config.changed_loss_weight * changed_loss
                    if loss is None
                    else loss + self.config.changed_loss_weight * changed_loss
                )
        if pair_consistency_labels is not None and pair_consistency_logits is not None:
            pair_consistency_loss = F.cross_entropy(pair_consistency_logits, pair_consistency_labels)
            loss = (
                self.config.pair_consistency_loss_weight * pair_consistency_loss
                if loss is None
                else loss + self.config.pair_consistency_loss_weight * pair_consistency_loss
            )
        if candidate_correct_labels is not None and candidate_correct_logits is not None:
            candidate_targets = candidate_correct_labels.to(candidate_correct_logits.dtype)
            raw_candidate_loss = F.binary_cross_entropy_with_logits(
                candidate_correct_logits,
                candidate_targets,
                reduction="none",
            )
            if query_mask is not None:
                active_candidate = query_mask.to(torch.bool)
                candidate_loss = raw_candidate_loss[active_candidate].mean()
            else:
                candidate_loss = raw_candidate_loss.mean()
            loss = (
                self.config.candidate_loss_weight * candidate_loss
                if loss is None
                else loss + self.config.candidate_loss_weight * candidate_loss
            )
        if candidate_wrong_labels is not None and candidate_wrong_logits is not None:
            wrong_mask = candidate_wrong_labels != -100
            if wrong_mask.any():
                wrong_targets = candidate_wrong_labels.to(candidate_wrong_logits.dtype).clamp_min(0)
                raw_wrong = F.binary_cross_entropy_with_logits(
                    candidate_wrong_logits,
                    wrong_targets,
                    reduction="none",
                )
                candidate_wrong_loss = raw_wrong[wrong_mask].mean()
                loss = (
                    self.config.candidate_wrong_loss_weight * candidate_wrong_loss
                    if loss is None
                    else loss + self.config.candidate_wrong_loss_weight * candidate_wrong_loss
                )
        if candidate_repair_labels is not None and candidate_repair_logits is not None:
            if (candidate_repair_labels != -100).any():
                candidate_repair_loss = F.cross_entropy(
                    candidate_repair_logits.reshape(-1, self.config.num_arc_colors),
                    candidate_repair_labels.reshape(-1),
                    ignore_index=-100,
                )
                loss = (
                    self.config.candidate_repair_loss_weight * candidate_repair_loss
                    if loss is None
                    else loss + self.config.candidate_repair_loss_weight * candidate_repair_loss
                )
        if candidate_inside_labels is not None and candidate_inside_logits is not None:
            inside_mask = candidate_inside_labels != -100
            if inside_mask.any():
                inside_targets = candidate_inside_labels.to(candidate_inside_logits.dtype).clamp_min(0)
                raw_inside = F.binary_cross_entropy_with_logits(
                    candidate_inside_logits,
                    inside_targets,
                    reduction="none",
                )
                candidate_inside_loss = raw_inside[inside_mask].mean()
                loss = (
                    self.config.candidate_inside_loss_weight * candidate_inside_loss
                    if loss is None
                    else loss + self.config.candidate_inside_loss_weight * candidate_inside_loss
                )

        if squeeze_query_dim:
            logits = logits[:, 0]
            height_logits = height_logits[:, 0]
            width_logits = width_logits[:, 0]
            changed_logits = changed_logits[:, 0]
            if inside_logits is not None:
                inside_logits = inside_logits[:, 0]
            if copy_logits is not None:
                copy_logits = copy_logits[:, 0]
            if feature_logits is not None:
                feature_logits = [logits_for_feature[:, 0] for logits_for_feature in feature_logits]
            if candidate_correct_logits is not None:
                candidate_correct_logits = candidate_correct_logits[:, 0]
            if candidate_wrong_logits is not None:
                candidate_wrong_logits = candidate_wrong_logits[:, 0]
            if candidate_repair_logits is not None:
                candidate_repair_logits = candidate_repair_logits[:, 0]
            if candidate_inside_logits is not None:
                candidate_inside_logits = candidate_inside_logits[:, 0]

        return ArcBottleneckOutput(
            logits=logits,
            height_logits=height_logits,
            width_logits=width_logits,
            changed_logits=changed_logits,
            inside_logits=inside_logits,
            copy_logits=copy_logits,
            pair_consistency_logits=pair_consistency_logits,
            candidate_correct_logits=candidate_correct_logits,
            candidate_wrong_logits=candidate_wrong_logits,
            candidate_repair_logits=candidate_repair_logits,
            candidate_inside_logits=candidate_inside_logits,
            feature_logits=feature_logits,
            loss=loss,
            cell_loss=cell_loss,
            inside_cell_loss=inside_cell_loss,
            outside_cell_loss=outside_cell_loss,
            shape_loss=shape_loss,
            changed_loss=changed_loss,
            inside_loss=inside_loss,
            copy_loss=copy_loss,
            feature_loss=feature_loss,
            compact_board_reconstruction_loss=compact_board_reconstruction_loss,
            pair_consistency_loss=pair_consistency_loss,
            candidate_loss=candidate_loss,
            candidate_wrong_loss=candidate_wrong_loss,
            candidate_repair_loss=candidate_repair_loss,
            candidate_inside_loss=candidate_inside_loss,
        )


__all__ = [
    "ArcBottleneckConfig",
    "ArcBottleneckModel",
    "ArcBottleneckOutput",
    "GRID_FEATURE_NAMES",
    "GRID_FEATURE_VOCAB_SIZES",
    "count_parameters",
]
