"""Dense full-attention ARC episode model.

One transformer stack over the entire episode at cell resolution:
up to 10 demo pairs (input+output boards), up to 4 query inputs, and
up to 4 output canvases — all in one bidirectional full-attention
sequence (max ~25.2k tokens). Nothing is compressed; cross-board
cell<->cell comparison happens directly in attention.

Design points (decided 2026-06-11):
- Output canvases are decoded jointly, non-autoregressively, in the same
  pass. Each output token is initialized from its query input's cell
  (copy-by-default editing) plus an OUTPUT role embedding.
- 2D rotary position embeddings (row half / col half of each head) make
  cell<->cell attention translation-relative; every board shares the
  same 30x30 coordinate frame.
- Deterministic per-cell feature channels (episode_features.py, 28
  channels incl. pair-diff) are summed into cell embeddings: the
  machine computes facts, the model attends to them.
- Depth-scaled residual init (GPT-2 style) for very deep stacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from .episode_features import (
    BOARD_TOKEN_FEATURE_VOCAB_SIZES,
    EPISODE_FEATURE_VOCAB_SIZES,
    PAIR_TOKEN_FEATURE_VOCAB_SIZES,
)
from .model import RMSNorm, count_parameters

import os

# ---- FlexAttention backend (optional, flash-style kernel + padding mask) -----
# Lazily imported + compiled once. _FLEX_STATE: None=untried, False=unavailable
# (fall back to SDPA forever), or a (compiled_flex, create_block_mask) tuple.
_FLEX_STATE = None


def _flex_enabled(config) -> bool:
    """Flex is on if the config asks for it or env ARC_FLEX_ATTN=1; env
    ARC_FLEX_ATTN=0 force-disables (overrides the config)."""
    env = os.environ.get("ARC_FLEX_ATTN")
    if env == "0":
        return False
    if env == "1":
        return True
    return bool(getattr(config, "use_flex_attention", False))


def _get_flex():
    """Return (compiled_flex_attention, create_block_mask) or False if flex
    can't be loaded/compiled on this torch/GPU. Tried at most once."""
    global _FLEX_STATE
    if _FLEX_STATE is not None:
        return _FLEX_STATE
    try:
        from torch.nn.attention.flex_attention import (
            flex_attention,
            create_block_mask,
        )
        compiled = torch.compile(flex_attention, dynamic=False)
        _FLEX_STATE = (compiled, create_block_mask)
        print("[episode_model] FlexAttention backend enabled.", flush=True)
    except Exception as exc:  # any import/compile failure -> SDPA for good
        print(f"[episode_model] FlexAttention unavailable ({type(exc).__name__}: "
              f"{exc}); using SDPA mem-efficient path.", flush=True)
        _FLEX_STATE = False
    return _FLEX_STATE


def _build_padding_block_mask(key_mask: torch.Tensor):
    """Block mask for a key-PADDING mask (same across query rows and heads).
    key_mask: [B, S] bool. Returns a BlockMask, or None if flex unavailable."""
    flex = _get_flex()
    if flex is False:
        return None
    _, create_block_mask = flex
    bsz, seq_len = key_mask.shape

    def mask_mod(b, h, q_idx, kv_idx):
        return key_mask[b, kv_idx]

    try:
        # H=None => broadcast over heads. Eager build is cheap (O((S/128)^2)).
        return create_block_mask(
            mask_mod, B=bsz, H=None, Q_LEN=seq_len, KV_LEN=seq_len,
            device=key_mask.device,
        )
    except Exception as exc:
        global _FLEX_STATE
        print(f"[episode_model] block-mask build failed ({type(exc).__name__}: "
              f"{exc}); falling back to SDPA.", flush=True)
        _FLEX_STATE = False
        return None


@dataclass(frozen=True)
class ArcEpisodeConfig:
    """Shape and scale settings for the dense full-attention episode model."""

    canvas_size: int = 30
    num_arc_colors: int = 10
    null_color_id: int = 10
    max_context_pairs: int = 10
    max_query_slots: int = 4

    d_model: int = 1600
    n_heads: int = 25
    n_layers: int = 32
    # Small learned-perception stem before the transformer: residual
    # multi-scale depthwise+pointwise conv blocks per board. The feature
    # channels are a floor (exact facts), not a ceiling — the stem can
    # discover local motifs we didn't enumerate, with conv's
    # translation-equivariant inductive bias, at <1% of the parameter
    # budget. Each block runs every kernel size in parallel (spatial
    # weights are k^2*d — trivial) and sums the branches before one
    # pointwise mix. 0 layers disables (clean one-flag ablation).
    conv_stem_layers: int = 3
    conv_stem_kernels: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9, 10)
    # Hot-plane stem: the same multi-scale conv blocks, but run on the
    # explicit one-hot planes (color + role + slot + mask + every feature
    # value as its own binary 30x30 plane) BEFORE the d_model mixing.
    # On hot planes, mask algebra is native — AND is multiply, "count of
    # color 3 in a window" is one kernel on one plane (the neurogolf
    # substrate). The learned DELTA is 1x1-projected into d_model and
    # added to the embedded tokens, so at init this is a no-op and
    # everything learned is new capability. 0 disables.
    hot_stem_layers: int = 3
    mlp_ratio: int = 4
    rope_base: float = 10000.0
    dropout: float = 0.0
    attention_dropout: float = 0.0
    layer_norm_eps: float = 1e-5
    use_bias: bool = False
    use_grid_features: bool = True
    depth_scaled_init: bool = True
    activation_checkpointing: bool = False
    # Attention kernel. The model passes a key-PADDING mask to attention,
    # which disables torch SDPA's flash backend (flash takes only
    # is_causal/no-mask) and routes to mem-efficient. FlexAttention
    # (torch>=2.5) is a flash-style fused kernel that DOES accept the
    # padding mask and, crucially, skips fully-padded KV blocks — boards
    # are 30x30=900 tokens but real ARC grids are far smaller, so most of
    # the sequence is contiguous padding it can skip. Default off (exact
    # SDPA path unchanged); enable via this flag or env ARC_FLEX_ATTN=1.
    # Falls back to SDPA automatically if flex import/compile/run fails.
    use_flex_attention: bool = False

    cell_loss_weight: float = 1.0
    shape_loss_weight: float = 0.25
    changed_loss_weight: float = 0.25
    inside_loss_weight: float = 0.1
    # B1 "detector" supervision: multi-label BCE over the rule's
    # racket_primitives. DISABLED in the current model (default 0) — the
    # arc_2b_dense model learns raw grids with no primitive supervision
    # (no --primitive-vocab); this head + primitive_vocab_size are inert
    # scaffolding kept for a future primitive-grounded variant.
    primitive_vocab_size: int = 0
    primitive_loss_weight: float = 0.05

    @property
    def cell_vocab_size(self) -> int:
        return self.num_arc_colors + 1

    @property
    def num_positions(self) -> int:
        return self.canvas_size * self.canvas_size

    @property
    def max_boards(self) -> int:
        # demo inputs + demo outputs + query inputs + output canvases
        return 2 * self.max_context_pairs + 2 * self.max_query_slots

    @property
    def head_dim(self) -> int:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return self.d_model // self.n_heads

    @property
    def mlp_hidden_dim(self) -> int:
        return self.d_model * self.mlp_ratio

    @property
    def hot_planes(self) -> int:
        """One binary plane per possible value of every per-cell channel."""
        return (
            self.cell_vocab_size            # color one-hot
            + BoardRoles.NUM_ROLES          # role
            + self.max_context_pairs        # pair slot
            + self.max_query_slots          # query slot
            + 2                             # valid mask
            + sum(EPISODE_FEATURE_VOCAB_SIZES)
        )

    @classmethod
    def arc_2b_dense(cls) -> "ArcEpisodeConfig":
        """PRIMARY trained target: 32 layers, 25 heads at head_dim 96
        (d=2400, ~2.2B) — compute-optimal for the ~10^21 FLOP budget."""
        return cls(
            d_model=2400,
            n_heads=25,
            n_layers=32,
            activation_checkpointing=True,
        )


@dataclass
class ArcEpisodeOutput:
    logits: torch.Tensor
    height_logits: torch.Tensor
    width_logits: torch.Tensor
    changed_logits: torch.Tensor
    inside_logits: torch.Tensor
    primitive_logits: Optional[torch.Tensor] = None
    loss: Optional[torch.Tensor] = None
    cell_loss: Optional[torch.Tensor] = None
    shape_loss: Optional[torch.Tensor] = None
    changed_loss: Optional[torch.Tensor] = None
    inside_loss: Optional[torch.Tensor] = None
    primitive_loss: Optional[torch.Tensor] = None


class BoardRoles:
    DEMO_INPUT = 0
    DEMO_OUTPUT = 1
    QUERY_INPUT = 2
    OUTPUT_SLOT = 3
    NUM_ROLES = 4


class Rotary2D(nn.Module):
    """2D rotary embedding over the 30x30 cell frame.

    The first half of each head's dims rotates with the row index, the
    second half with the column index, so attention scores depend on
    (dr, dc) between cells — translation-relative by construction.
    """

    def __init__(self, head_dim: int, canvas_size: int, base: float) -> None:
        super().__init__()
        if head_dim % 4 != 0:
            raise ValueError("head_dim must be divisible by 4 for 2D rope")
        quarter = head_dim // 4
        inv_freq = base ** (-torch.arange(quarter, dtype=torch.float32) / quarter)
        rows = torch.arange(canvas_size).repeat_interleave(canvas_size).to(torch.float32)
        cols = torch.arange(canvas_size).repeat(canvas_size).to(torch.float32)
        row_angles = rows[:, None] * inv_freq[None, :]
        col_angles = cols[:, None] * inv_freq[None, :]
        angles = torch.cat([row_angles, col_angles], dim=-1)  # (900, head_dim/2)
        cos = torch.cat([angles.cos(), angles.cos()], dim=-1)  # (900, head_dim)
        sin = torch.cat([angles.sin(), angles.sin()], dim=-1)
        self.register_buffer("cos", cos, persistent=False)
        self.register_buffer("sin", sin, persistent=False)

    def tables(self, position_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return self.cos[position_ids], self.sin[position_ids]


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    # x: (bsz, heads, seq, head_dim); cos/sin: (seq, head_dim)
    x1, x2 = x.chunk(2, dim=-1)
    rotated = torch.cat([-x2, x1], dim=-1)
    return x * cos[None, None, :, :] + rotated * sin[None, None, :, :]


class MixConvBlock(nn.Module):
    """Residual multi-scale conv block: parallel depthwise convs at several
    kernel sizes (2x2 fine detail, 3x3 motifs, 5x5 context — spatial weights
    are k^2*d, nearly free), summed, then one pointwise channel mix."""

    def __init__(self, dim: int, kernel_sizes: tuple[int, ...]) -> None:
        super().__init__()
        self.norm = nn.GroupNorm(1, dim)
        self.depthwise = nn.ModuleList(
            [nn.Conv2d(dim, dim, kernel_size=k, padding="same", groups=dim) for k in kernel_sizes]
        )
        self.pointwise = nn.Conv2d(dim, dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.norm(x)
        y = sum(conv(y) for conv in self.depthwise)
        y = F.gelu(y, approximate="tanh")
        y = self.pointwise(y)
        return x + y


class EpisodeSelfAttention(nn.Module):
    def __init__(self, config: ArcEpisodeConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.head_dim = config.head_dim
        self.qkv = nn.Linear(config.d_model, config.d_model * 3, bias=config.use_bias)
        self.out = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.dropout = config.attention_dropout

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        key_mask: Optional[torch.Tensor] = None,
        block_mask=None,
    ) -> torch.Tensor:
        bsz, seq_len, dim = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)

        def reshape(t: torch.Tensor) -> torch.Tensor:
            return t.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        q, k, v = reshape(q), reshape(k), reshape(v)
        q = apply_rope(q, cos, sin)
        k = apply_rope(k, cos, sin)

        # FlexAttention path: same math as the masked SDPA below (1/sqrt(d)
        # scale, padding-masked softmax), but a flash-style fused kernel that
        # skips fully-padded KV blocks. Only taken when the model threaded a
        # block_mask in (flex enabled + build succeeded). Any runtime error
        # disables flex for the rest of the process and re-runs on SDPA.
        if block_mask is not None:
            flex = _get_flex()
            if flex is not False:
                try:
                    compiled_flex, _ = flex
                    y = compiled_flex(q, k, v, block_mask=block_mask)
                    y = y.transpose(1, 2).contiguous().view(bsz, seq_len, dim)
                    return self.out(y)
                except Exception as exc:
                    global _FLEX_STATE
                    print(f"[episode_model] flex_attention runtime error "
                          f"({type(exc).__name__}: {exc}); SDPA fallback.", flush=True)
                    _FLEX_STATE = False

        attn_mask = None
        if key_mask is not None:
            attn_mask = key_mask[:, None, None, :].to(torch.bool)
        y = F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=attn_mask,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=False,
        )
        y = y.transpose(1, 2).contiguous().view(bsz, seq_len, dim)
        return self.out(y)


class EpisodeBlock(nn.Module):
    def __init__(self, config: ArcEpisodeConfig) -> None:
        super().__init__()
        self.attn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.attn = EpisodeSelfAttention(config)
        self.ffn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.up = nn.Linear(config.d_model, config.mlp_hidden_dim, bias=config.use_bias)
        self.down = nn.Linear(config.mlp_hidden_dim, config.d_model, bias=config.use_bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        key_mask: Optional[torch.Tensor] = None,
        block_mask=None,
    ) -> torch.Tensor:
        x = x + self.dropout(
            self.attn(self.attn_norm(x), cos, sin, key_mask=key_mask, block_mask=block_mask)
        )
        h = F.gelu(self.up(self.ffn_norm(x)), approximate="tanh")
        x = x + self.dropout(self.down(h))
        if key_mask is not None:
            x = x * key_mask[:, :, None].to(x.dtype)
        return x


class ArcEpisodeModel(nn.Module):
    """Full-attention transformer over the entire ARC episode."""

    def __init__(self, config: ArcEpisodeConfig) -> None:
        super().__init__()
        _ = config.head_dim
        self.config = config

        self.color_embedding = nn.Embedding(config.cell_vocab_size, config.d_model)
        self.role_embedding = nn.Embedding(BoardRoles.NUM_ROLES, config.d_model)
        self.pair_slot_embedding = nn.Embedding(config.max_context_pairs, config.d_model)
        self.query_slot_embedding = nn.Embedding(config.max_query_slots, config.d_model)
        self.mask_embedding = nn.Embedding(2, config.d_model)
        if config.use_grid_features:
            self.feature_embeddings = nn.ModuleList(
                [nn.Embedding(vocab_size, config.d_model) for vocab_size in EPISODE_FEATURE_VOCAB_SIZES]
            )
            # Typed summary tokens: one per board + one per demo pair,
            # appended to the sequence (position-free under rope pos 0).
            self.board_feature_embeddings = nn.ModuleList(
                [nn.Embedding(vocab_size, config.d_model) for vocab_size in BOARD_TOKEN_FEATURE_VOCAB_SIZES]
            )
            self.pair_feature_embeddings = nn.ModuleList(
                [nn.Embedding(vocab_size, config.d_model) for vocab_size in PAIR_TOKEN_FEATURE_VOCAB_SIZES]
            )
            self.board_summary_marker = nn.Parameter(torch.randn(config.d_model) * 0.02)
            self.pair_summary_marker = nn.Parameter(torch.randn(config.d_model) * 0.02)
        else:
            self.feature_embeddings = None
            self.board_feature_embeddings = None
            self.pair_feature_embeddings = None
            self.board_summary_marker = None
            self.pair_summary_marker = None
        self.input_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        # Learned local perception on each board before the transformer.
        self.conv_stem = (
            nn.ModuleList(
                [
                    MixConvBlock(config.d_model, config.conv_stem_kernels)
                    for _ in range(config.conv_stem_layers)
                ]
            )
            if config.conv_stem_layers > 0
            else None
        )
        # Hot-plane stem: same kernel ladder, but on the explicit one-hot
        # planes; the learned delta is 1x1-projected into d_model.
        if config.hot_stem_layers > 0:
            self.hot_stem = nn.ModuleList(
                [
                    MixConvBlock(config.hot_planes, config.conv_stem_kernels)
                    for _ in range(config.hot_stem_layers)
                ]
            )
            self.hot_proj = nn.Conv2d(config.hot_planes, config.d_model, kernel_size=1, bias=False)
        else:
            self.hot_stem = None
            self.hot_proj = None

        self.rotary = Rotary2D(config.head_dim, config.canvas_size, config.rope_base)
        self.layers = nn.ModuleList([EpisodeBlock(config) for _ in range(config.n_layers)])
        self.final_norm = RMSNorm(config.d_model, config.layer_norm_eps)

        self.cell_head = nn.Linear(config.d_model, config.num_arc_colors, bias=True)
        self.changed_head = nn.Linear(config.d_model, 1, bias=True)
        self.inside_head = nn.Linear(config.d_model, 1, bias=True)
        self.height_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        self.width_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        self.primitive_head = (
            nn.Linear(config.d_model, config.primitive_vocab_size, bias=True)
            if config.primitive_vocab_size > 0
            else None
        )

        self.apply(self._init_weights)
        if config.depth_scaled_init:
            scale = (2 * config.n_layers) ** -0.5
            for layer in self.layers:
                with torch.no_grad():
                    layer.attn.out.weight.mul_(scale)
                    layer.down.weight.mul_(scale)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def _embed_board(
        self,
        ids: torch.Tensor,
        role: int,
        slot_embedding: torch.Tensor,
        mask: torch.Tensor,
        features: Optional[torch.Tensor],
    ) -> torch.Tensor:
        x = self.color_embedding(ids.clamp(0, self.config.cell_vocab_size - 1))
        x = x + self.role_embedding.weight[role][None, None, :]
        x = x + slot_embedding
        x = x + self.mask_embedding(mask.to(torch.long))
        if self.feature_embeddings is not None and features is not None:
            if features.shape[-1] != len(self.feature_embeddings):
                raise ValueError(
                    f"expected {len(self.feature_embeddings)} feature channels "
                    f"(episode set), got {features.shape[-1]} — build batches with "
                    "add_episode_features_to_batch"
                )
            for idx, embedding in enumerate(self.feature_embeddings):
                feature_ids = features[..., idx].clamp(0, embedding.num_embeddings - 1)
                x = x + embedding(feature_ids)
        return x

    def _hot_stem_delta(
        self,
        demo_input_ids: torch.Tensor,
        demo_output_ids: torch.Tensor,
        query_input_ids: torch.Tensor,
        demo_input_masks: torch.Tensor,
        demo_output_masks: torch.Tensor,
        query_input_mask: torch.Tensor,
        demo_input_features: Optional[torch.Tensor],
        demo_output_features: Optional[torch.Tensor],
        query_input_features: Optional[torch.Tensor],
        key_mask: torch.Tensor,
        pairs: int,
        queries: int,
        num_boards: int,
    ) -> torch.Tensor:
        """Run the multi-scale stem on the explicit one-hot planes and
        return the learned delta projected into d_model, (b, boards,
        cells, d). The identity part of the residual blocks cancels, so
        this is ~zero at init and a strict superset of the embedding sum."""
        config = self.config
        device = demo_input_ids.device
        fdtype = self.color_embedding.weight.dtype
        bsz = demo_input_ids.shape[0]
        num_cells = config.num_positions
        n_feat = len(EPISODE_FEATURE_VOCAB_SIZES)
        feat_planes = sum(EPISODE_FEATURE_VOCAB_SIZES)

        def onehot(t: torch.Tensor, n: int) -> torch.Tensor:
            return F.one_hot(t.clamp(0, n - 1), n).to(fdtype)

        def board_planes(ids, masks, feats, role_idx, slot_kind):
            b_, n_, _ = ids.shape
            comp = [onehot(ids, config.cell_vocab_size)]
            role_oh = torch.zeros((b_, n_, num_cells, BoardRoles.NUM_ROLES), device=device, dtype=fdtype)
            role_oh[..., role_idx] = 1.0
            comp.append(role_oh)
            pair_oh = torch.zeros((b_, n_, num_cells, config.max_context_pairs), device=device, dtype=fdtype)
            query_oh = torch.zeros((b_, n_, num_cells, config.max_query_slots), device=device, dtype=fdtype)
            for slot in range(n_):
                if slot_kind == "pair":
                    pair_oh[:, slot, :, slot] = 1.0
                else:
                    query_oh[:, slot, :, slot] = 1.0
            comp.extend([pair_oh, query_oh])
            comp.append(onehot(masks.to(torch.long), 2))
            if feats is not None:
                comp.extend(
                    onehot(feats[..., k], EPISODE_FEATURE_VOCAB_SIZES[k]) for k in range(n_feat)
                )
            else:
                comp.append(torch.zeros((b_, n_, num_cells, feat_planes), device=device, dtype=fdtype))
            return torch.cat(comp, dim=-1)

        demo_in_planes = board_planes(
            demo_input_ids, demo_input_masks, demo_input_features, BoardRoles.DEMO_INPUT, "pair"
        )
        demo_out_planes = board_planes(
            demo_output_ids, demo_output_masks, demo_output_features, BoardRoles.DEMO_OUTPUT, "pair"
        )
        planes = torch.cat(
            [
                torch.stack([demo_in_planes, demo_out_planes], dim=2).reshape(
                    bsz, pairs * 2, num_cells, config.hot_planes
                ),
                board_planes(
                    query_input_ids, query_input_mask, query_input_features,
                    BoardRoles.QUERY_INPUT, "query",
                ),
                board_planes(
                    query_input_ids, query_input_mask, query_input_features,
                    BoardRoles.OUTPUT_SLOT, "query",
                ),
            ],
            dim=1,
        )
        side = config.canvas_size
        planes2d = (
            planes.reshape(bsz * num_boards, num_cells, config.hot_planes)
            .transpose(1, 2)
            .reshape(bsz * num_boards, config.hot_planes, side, side)
        )
        gate = key_mask.reshape(bsz * num_boards, 1, side, side).to(fdtype)
        planes2d = planes2d * gate
        y = planes2d
        for block in self.hot_stem:
            if config.activation_checkpointing and self.training:
                y = checkpoint(block, y, use_reentrant=False) * gate
            else:
                y = block(y) * gate
        delta = self.hot_proj(y - planes2d)
        return (
            delta.reshape(bsz * num_boards, config.d_model, num_cells)
            .transpose(1, 2)
            .reshape(bsz, num_boards, num_cells, config.d_model)
        )

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
        demo_input_board_features: Optional[torch.Tensor] = None,
        demo_output_board_features: Optional[torch.Tensor] = None,
        query_board_features: Optional[torch.Tensor] = None,
        pair_features: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        height_labels: Optional[torch.Tensor] = None,
        width_labels: Optional[torch.Tensor] = None,
        changed_labels: Optional[torch.Tensor] = None,
        primitive_labels: Optional[torch.Tensor] = None,
        primitive_labels_mask: Optional[torch.Tensor] = None,
    ) -> ArcEpisodeOutput:
        config = self.config
        squeeze_query_dim = query_input_ids.dim() == 2
        if squeeze_query_dim:
            query_input_ids = query_input_ids[:, None, :]
            if query_mask is not None and query_mask.dim() == 1:
                query_mask = query_mask[:, None]
            if query_input_mask is not None:
                query_input_mask = query_input_mask[:, None, :]
            if query_input_features is not None:
                query_input_features = query_input_features[:, None, :, :]
            if query_board_features is not None and query_board_features.dim() == 2:
                query_board_features = query_board_features[:, None, :]
            if labels is not None:
                labels = labels[:, None, :]
            if changed_labels is not None:
                changed_labels = changed_labels[:, None, :]
            if height_labels is not None and height_labels.dim() == 1:
                height_labels = height_labels[:, None]
            if width_labels is not None and width_labels.dim() == 1:
                width_labels = width_labels[:, None]

        bsz, pairs, num_cells = demo_input_ids.shape
        queries = query_input_ids.shape[1]
        if num_cells != config.num_positions:
            raise ValueError(f"expected {config.num_positions} cells, got {num_cells}")
        if pairs > config.max_context_pairs:
            raise ValueError(f"pairs={pairs} exceeds max_context_pairs={config.max_context_pairs}")
        if queries > config.max_query_slots:
            raise ValueError(f"queries={queries} exceeds max_query_slots={config.max_query_slots}")
        device = demo_input_ids.device

        pair_active = pair_mask.to(torch.bool)
        if query_mask is None:
            query_active = torch.ones((bsz, queries), dtype=torch.bool, device=device)
        else:
            query_active = query_mask.to(torch.bool)

        if demo_input_masks is None:
            demo_input_masks = demo_input_ids != config.null_color_id
        if demo_output_masks is None:
            demo_output_masks = demo_output_ids != config.null_color_id
        if query_input_mask is None:
            query_input_mask = query_input_ids != config.null_color_id
        demo_input_masks = demo_input_masks.to(torch.bool)
        demo_output_masks = demo_output_masks.to(torch.bool)
        query_input_mask = query_input_mask.to(torch.bool)

        pair_ids = torch.arange(pairs, device=device)
        query_ids = torch.arange(queries, device=device)
        pair_slots = self.pair_slot_embedding(pair_ids)[None, :, None, :]
        query_slots = self.query_slot_embedding(query_ids)[None, :, None, :]

        demo_in = self._embed_board(
            demo_input_ids, BoardRoles.DEMO_INPUT, pair_slots, demo_input_masks, demo_input_features
        )
        demo_out = self._embed_board(
            demo_output_ids, BoardRoles.DEMO_OUTPUT, pair_slots, demo_output_masks, demo_output_features
        )
        query_in = self._embed_board(
            query_input_ids, BoardRoles.QUERY_INPUT, query_slots, query_input_mask, query_input_features
        )
        # Output canvases: copy-by-default — start from the query input's
        # cells under the OUTPUT role; the stack edits them.
        output_slots = self._embed_board(
            query_input_ids, BoardRoles.OUTPUT_SLOT, query_slots, query_input_mask, query_input_features
        )

        # Sequence: [d0_in, d0_out, d1_in, d1_out, ..., q0, ..., out0, ...]
        demo_tokens = torch.stack([demo_in, demo_out], dim=2).reshape(
            bsz, pairs * 2, num_cells, config.d_model
        )
        tokens = torch.cat([demo_tokens, query_in, output_slots], dim=1)
        num_boards = tokens.shape[1]

        # Key mask: demo boards gated by pair_mask AND their cell masks;
        # query inputs gated by query_mask AND cell masks; output canvases
        # expose ALL 900 positions (shape is unknown — the model decides).
        demo_board_masks = torch.stack([demo_input_masks, demo_output_masks], dim=2).reshape(
            bsz, pairs * 2, num_cells
        )
        demo_key = demo_board_masks & pair_active[:, :, None].expand(bsz, pairs, 2 * num_cells).reshape(
            bsz, pairs * 2, num_cells
        )
        query_key = query_input_mask & query_active[:, :, None]
        output_key = query_active[:, :, None].expand(bsz, queries, num_cells)
        key_mask = torch.cat([demo_key, query_key, output_key], dim=1).reshape(bsz, -1)

        if self.hot_stem is not None:
            tokens = tokens + self._hot_stem_delta(
                demo_input_ids, demo_output_ids, query_input_ids,
                demo_input_masks, demo_output_masks, query_input_mask,
                demo_input_features, demo_output_features, query_input_features,
                key_mask, pairs, queries, num_boards,
            )

        x = self.input_norm(tokens.reshape(bsz, num_boards * num_cells, config.d_model))

        if self.conv_stem is not None:
            side = config.canvas_size
            cell_mask2d = key_mask.reshape(bsz * num_boards, 1, side, side).to(x.dtype)
            x2d = (
                x.reshape(bsz * num_boards, num_cells, config.d_model)
                .transpose(1, 2)
                .reshape(bsz * num_boards, config.d_model, side, side)
            )
            for block in self.conv_stem:
                x2d = block(x2d) * cell_mask2d
            x = (
                x2d.reshape(bsz * num_boards, config.d_model, num_cells)
                .transpose(1, 2)
                .reshape(bsz, num_boards * num_cells, config.d_model)
            )

        # Typed summary tokens (board facts, pair facts) appended AFTER the
        # output canvases so output-state slicing stays contiguous.
        num_summary = 0
        if (
            self.board_feature_embeddings is not None
            and demo_input_board_features is not None
            and demo_output_board_features is not None
            and query_board_features is not None
            and pair_features is not None
        ):
            def embed_summary(feats: torch.Tensor, tables: nn.ModuleList) -> torch.Tensor:
                token = torch.zeros(
                    (*feats.shape[:-1], config.d_model), device=device, dtype=x.dtype
                )
                for idx, embedding in enumerate(tables):
                    token = token + embedding(feats[..., idx].clamp(0, embedding.num_embeddings - 1))
                return token

            demo_in_tok = (
                embed_summary(demo_input_board_features, self.board_feature_embeddings)
                + self.role_embedding.weight[BoardRoles.DEMO_INPUT]
                + pair_slots[:, :, 0, :]
                + self.board_summary_marker
            )
            demo_out_tok = (
                embed_summary(demo_output_board_features, self.board_feature_embeddings)
                + self.role_embedding.weight[BoardRoles.DEMO_OUTPUT]
                + pair_slots[:, :, 0, :]
                + self.board_summary_marker
            )
            query_tok = (
                embed_summary(query_board_features, self.board_feature_embeddings)
                + self.role_embedding.weight[BoardRoles.QUERY_INPUT]
                + query_slots[:, :, 0, :]
                + self.board_summary_marker
            )
            pair_tok = (
                embed_summary(pair_features, self.pair_feature_embeddings)
                + pair_slots[:, :, 0, :]
                + self.pair_summary_marker
            )
            summary = torch.cat([demo_in_tok, demo_out_tok, query_tok, pair_tok], dim=1)
            summary_mask = torch.cat(
                [pair_active, pair_active, query_active, pair_active], dim=1
            )
            num_summary = summary.shape[1]
            x = torch.cat([x, self.input_norm(summary)], dim=1)
            key_mask = torch.cat([key_mask, summary_mask], dim=1)

        empty_rows = ~key_mask.any(dim=1)
        if empty_rows.any():
            key_mask = key_mask.clone()
            key_mask[empty_rows, 0] = True
        x = x * key_mask[:, :, None].to(x.dtype)

        # Build the padding block-mask ONCE per forward (key_mask is identical
        # across all 32 layers) so flex amortizes the build over the stack.
        # None => SDPA path (flex disabled or unavailable), unchanged behavior.
        block_mask = None
        if _flex_enabled(config):
            block_mask = _build_padding_block_mask(key_mask.to(torch.bool))

        position_ids = torch.arange(num_cells, device=device).repeat(num_boards)
        if num_summary:
            # Summary tokens are position-free: rope at position 0 is identity.
            position_ids = torch.cat(
                [position_ids, torch.zeros(num_summary, device=device, dtype=torch.long)]
            )
        cos, sin = self.rotary.tables(position_ids)

        for layer in self.layers:
            if config.activation_checkpointing and self.training:
                x = checkpoint(layer, x, cos, sin, key_mask, block_mask, use_reentrant=False)
            else:
                x = layer(x, cos, sin, key_mask=key_mask, block_mask=block_mask)
        x = self.final_norm(x)

        output_start = (pairs * 2 + queries) * num_cells
        output_end = output_start + queries * num_cells
        out_states = x[:, output_start:output_end, :].reshape(bsz, queries, num_cells, config.d_model)

        logits = self.cell_head(out_states)
        changed_logits = self.changed_head(out_states).squeeze(-1)
        inside_logits = self.inside_head(out_states).squeeze(-1)
        pooled = out_states.mean(dim=2)
        height_logits = self.height_head(pooled)
        width_logits = self.width_head(pooled)
        primitive_logits = None
        if self.primitive_head is not None:
            # Episode-level pooled state: masked mean over the whole
            # sequence (cell + summary tokens) — the "what rule is this"
            # representation the detector head reads.
            weights = key_mask[:, :, None].to(x.dtype)
            episode_pooled = (x * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)
            primitive_logits = self.primitive_head(episode_pooled)

        cell_loss = None
        shape_loss = None
        changed_loss = None
        inside_loss = None
        loss = None
        if labels is not None:
            raw_cell = F.cross_entropy(
                logits.reshape(-1, config.num_arc_colors),
                labels.reshape(-1),
                ignore_index=-100,
                reduction="none",
            ).reshape(labels.shape)
            label_mask = labels != -100
            flat_mask = label_mask.reshape(-1, num_cells)
            flat_raw = raw_cell.reshape(-1, num_cells)
            active_rows = flat_mask.any(dim=1)
            # Per-example normalization: a 30x30 episode must not drown a 3x3 one.
            per_example = flat_raw.sum(dim=1) / flat_mask.sum(dim=1).clamp_min(1)
            if active_rows.any():
                cell_loss = per_example[active_rows].mean()
                loss = config.cell_loss_weight * cell_loss
            inside_targets = label_mask.to(inside_logits.dtype)
            raw_inside = F.binary_cross_entropy_with_logits(
                inside_logits, inside_targets, reduction="none"
            )
            inside_weights = query_active[:, :, None].to(raw_inside.dtype)
            if inside_weights.any():
                inside_loss = (raw_inside * inside_weights).sum() / (
                    inside_weights.sum().clamp_min(1.0) * num_cells
                )
                term = config.inside_loss_weight * inside_loss
                loss = term if loss is None else loss + term
        if height_labels is not None and width_labels is not None:
            shape_loss = (
                F.cross_entropy(
                    height_logits.reshape(-1, config.canvas_size),
                    height_labels.reshape(-1),
                    ignore_index=-100,
                )
                + F.cross_entropy(
                    width_logits.reshape(-1, config.canvas_size),
                    width_labels.reshape(-1),
                    ignore_index=-100,
                )
            ) * 0.5
            term = config.shape_loss_weight * shape_loss
            loss = term if loss is None else loss + term
        if changed_labels is not None:
            changed_mask = changed_labels != -100
            if changed_mask.any():
                raw_changed = F.binary_cross_entropy_with_logits(
                    changed_logits,
                    changed_labels.to(changed_logits.dtype).clamp_min(0),
                    reduction="none",
                )
                changed_loss = raw_changed[changed_mask].mean()
                term = config.changed_loss_weight * changed_loss
                loss = term if loss is None else loss + term
        primitive_loss = None
        if primitive_logits is not None and primitive_labels is not None:
            if primitive_labels_mask is None:
                primitive_labels_mask = torch.ones(
                    primitive_labels.shape[0], dtype=torch.bool, device=device
                )
            active = primitive_labels_mask.to(torch.bool)
            if active.any():
                raw_primitive = F.binary_cross_entropy_with_logits(
                    primitive_logits[active],
                    primitive_labels[active].to(primitive_logits.dtype),
                )
                primitive_loss = raw_primitive
                term = config.primitive_loss_weight * primitive_loss
                loss = term if loss is None else loss + term

        if squeeze_query_dim:
            logits = logits[:, 0]
            height_logits = height_logits[:, 0]
            width_logits = width_logits[:, 0]
            changed_logits = changed_logits[:, 0]
            inside_logits = inside_logits[:, 0]

        return ArcEpisodeOutput(
            logits=logits,
            height_logits=height_logits,
            width_logits=width_logits,
            changed_logits=changed_logits,
            inside_logits=inside_logits,
            primitive_logits=primitive_logits,
            loss=loss,
            cell_loss=cell_loss,
            shape_loss=shape_loss,
            changed_loss=changed_loss,
            inside_loss=inside_loss,
            primitive_loss=primitive_loss,
        )


__all__ = [
    "ArcEpisodeConfig",
    "ArcEpisodeModel",
    "ArcEpisodeOutput",
    "BoardRoles",
    "MixConvBlock",
    "count_parameters",
]
