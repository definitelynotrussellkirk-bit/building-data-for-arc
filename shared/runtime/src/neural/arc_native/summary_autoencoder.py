"""Summary-first ARC autoencoder.

This pretraining model learns a compact task summary before it learns to solve
hidden queries. It sees visible ARC boards, writes a summary token bank, then
reconstructs the visible boards from that summary only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
import torch.nn.functional as F

from .bottleneck_model import ConvBlock, CrossAttentionBlock, SelfAttentionBlock, maybe_checkpoint
from .bottleneck_tensorize import (
    BottleneckBoardRoles,
    GRID_FEATURE_IGNORE_INDEX,
    GRID_FEATURE_NAMES,
    GRID_FEATURE_VOCAB_SIZES,
)
from .model import RMSNorm


@dataclass(frozen=True)
class ArcSummaryAutoencoderConfig:
    """Shape and scale settings for the summary autoencoder."""

    canvas_size: int = 30
    num_arc_colors: int = 10
    null_color_id: int = 10
    max_context_pairs: int = 10
    max_query_pairs: int = 4
    num_board_roles: int = 8

    d_model: int = 512
    n_heads: int = 16
    summary_tokens: int = 256
    summary_vocab_size: int = 1024
    discrete_summary: bool = False
    summary_codebook_loss_weight: float = 0.0
    summary_commitment_loss_weight: float = 0.25
    summary_code_entropy_loss_weight: float = 0.0
    summary_code_temperature: float = 1.0
    grid_conv_layers: int = 4
    summary_cross_layers: int = 2
    summary_layers: int = 12
    diagnostic_layers: int = 0
    decoder_layers: int = 4
    decoder_self_attention: bool = False
    mlp_ratio: int = 4
    dropout: float = 0.0
    attention_dropout: float = 0.0
    layer_norm_eps: float = 1e-5
    use_bias: bool = False
    use_grid_masks: bool = True
    use_grid_features: bool = True
    activation_checkpointing: bool = False

    reconstruction_loss_weight: float = 1.0
    null_reconstruction_weight: float = 0.2
    reconstruction_sample_fraction: float = 1.0
    reconstruction_sample_min: int = 0
    reconstruction_full_prob: float = 1.0
    hard_cell_loss_weight: float = 0.0
    hard_cell_fraction: float = 0.02
    hard_cell_min: int = 8
    cell_margin_loss_weight: float = 0.0
    cell_margin: float = 2.0
    cell_margin_fraction: float = 0.02
    inside_loss_weight: float = 0.25
    shape_loss_weight: float = 0.25
    grid_feature_loss_weight: float = 0.05
    jepa_loss_weight: float = 0.0
    jepa_retrieval_loss_weight: float = 0.0
    jepa_temperature: float = 0.07
    jepa_predictor_ratio: int = 2
    board_structure_loss_weight: float = 0.0
    pair_diff_loss_weight: float = 0.0
    pair_diff_positive_weight: float = 1.0

    @property
    def cell_vocab_size(self) -> int:
        return self.num_arc_colors + 1

    @property
    def num_positions(self) -> int:
        return self.canvas_size * self.canvas_size

    @property
    def max_visible_boards(self) -> int:
        return (2 * self.max_context_pairs) + self.max_query_pairs

    @property
    def head_dim(self) -> int:
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        return self.d_model // self.n_heads

    @property
    def mlp_hidden_dim(self) -> int:
        return self.d_model * self.mlp_ratio

    @classmethod
    def smoke(cls, *, canvas_size: int = 4) -> "ArcSummaryAutoencoderConfig":
        return cls(
            canvas_size=canvas_size,
            max_context_pairs=2,
            max_query_pairs=1,
            d_model=32,
            n_heads=4,
            summary_tokens=8,
            summary_vocab_size=32,
            grid_conv_layers=1,
            summary_cross_layers=1,
            summary_layers=1,
            decoder_layers=1,
            mlp_ratio=2,
        )

    @classmethod
    def summary_1b(cls) -> "ArcSummaryAutoencoderConfig":
        return cls(
            d_model=1152,
            n_heads=18,
            summary_tokens=768,
            summary_vocab_size=2048,
            grid_conv_layers=6,
            summary_cross_layers=4,
            summary_layers=48,
            decoder_layers=8,
            decoder_self_attention=False,
            use_grid_masks=True,
            use_grid_features=True,
            reconstruction_loss_weight=1.0,
            inside_loss_weight=0.25,
            shape_loss_weight=0.25,
            grid_feature_loss_weight=0.05,
            jepa_loss_weight=0.5,
            discrete_summary=True,
            summary_codebook_loss_weight=0.05,
            summary_commitment_loss_weight=0.25,
            board_structure_loss_weight=0.1,
            pair_diff_loss_weight=0.2,
        )

    @classmethod
    def summary_9b(cls) -> "ArcSummaryAutoencoderConfig":
        """9B target for frozen-base LoRA/merge or sharded TPU FFT runs."""
        return cls(
            d_model=3072,
            n_heads=48,
            summary_tokens=1536,
            summary_vocab_size=8192,
            grid_conv_layers=8,
            summary_cross_layers=8,
            summary_layers=48,
            diagnostic_layers=8,
            decoder_layers=8,
            decoder_self_attention=False,
            use_grid_masks=True,
            use_grid_features=True,
            reconstruction_loss_weight=1.0,
            inside_loss_weight=0.25,
            shape_loss_weight=0.25,
            grid_feature_loss_weight=0.05,
            jepa_loss_weight=0.5,
            discrete_summary=True,
            summary_codebook_loss_weight=0.05,
            summary_commitment_loss_weight=0.25,
            board_structure_loss_weight=0.1,
            pair_diff_loss_weight=0.2,
        )


@dataclass
class ArcSummaryAutoencoderOutput:
    reconstruction_logits: torch.Tensor
    inside_logits: torch.Tensor
    height_logits: torch.Tensor
    width_logits: torch.Tensor
    summary: torch.Tensor
    feature_logits: Optional[list[torch.Tensor]] = None
    jepa_pred: Optional[torch.Tensor] = None
    jepa_target: Optional[torch.Tensor] = None
    jepa_retrieval_logits: Optional[torch.Tensor] = None
    summary_code_indices: Optional[torch.Tensor] = None
    board_symmetry_logits: Optional[torch.Tensor] = None
    board_color_presence_logits: Optional[torch.Tensor] = None
    board_nonzero_count_logits: Optional[torch.Tensor] = None
    board_color_count_logits: Optional[torch.Tensor] = None
    board_local_signature_logits: Optional[torch.Tensor] = None
    board_topology_logits: Optional[torch.Tensor] = None
    pair_diff_logits: Optional[torch.Tensor] = None
    pair_same_shape_logits: Optional[torch.Tensor] = None
    pair_diff_count_logits: Optional[torch.Tensor] = None
    pair_color_delta_logits: Optional[torch.Tensor] = None
    pair_color_transition_logits: Optional[torch.Tensor] = None
    loss: Optional[torch.Tensor] = None
    reconstruction_loss: Optional[torch.Tensor] = None
    hard_cell_loss: Optional[torch.Tensor] = None
    cell_margin_loss: Optional[torch.Tensor] = None
    inside_loss: Optional[torch.Tensor] = None
    shape_loss: Optional[torch.Tensor] = None
    feature_loss: Optional[torch.Tensor] = None
    summary_codebook_loss: Optional[torch.Tensor] = None
    summary_commitment_loss: Optional[torch.Tensor] = None
    summary_code_entropy_loss: Optional[torch.Tensor] = None
    summary_code_perplexity: Optional[torch.Tensor] = None
    jepa_loss: Optional[torch.Tensor] = None
    jepa_retrieval_loss: Optional[torch.Tensor] = None
    board_structure_loss: Optional[torch.Tensor] = None
    pair_diff_loss: Optional[torch.Tensor] = None
    decoded_visible_boards: bool = True


def _as_query_slots(tensor: torch.Tensor) -> torch.Tensor:
    if tensor.dim() == 2:
        return tensor[:, None, :]
    if tensor.dim() == 3:
        return tensor
    raise ValueError(f"expected query tensor rank 2 or 3, got {tensor.shape}")


def pack_visible_boards_from_bottleneck_batch(
    batch: dict[str, torch.Tensor],
    *,
    include_query_inputs: bool = True,
) -> dict[str, torch.Tensor]:
    """Pack legal visible boards from a bottleneck batch for summary pretraining."""
    demo_input_ids = batch["demo_input_ids"]
    demo_output_ids = batch["demo_output_ids"]
    pair_mask = batch["pair_mask"].to(torch.bool)
    bsz, pairs, _ = demo_input_ids.shape
    device = demo_input_ids.device

    board_ids = [demo_input_ids, demo_output_ids]
    board_masks = [batch["demo_input_masks"], batch["demo_output_masks"]]
    board_features = [batch["demo_input_features"], batch["demo_output_features"]]
    board_active = [pair_mask, pair_mask]
    board_roles = [
        torch.full((bsz, pairs), BottleneckBoardRoles.DEMO_INPUT, dtype=torch.long, device=device),
        torch.full((bsz, pairs), BottleneckBoardRoles.DEMO_OUTPUT, dtype=torch.long, device=device),
    ]

    if include_query_inputs and "query_input_ids" in batch:
        query_ids = _as_query_slots(batch["query_input_ids"])
        query_masks = _as_query_slots(batch["query_input_mask"])
        query_features = batch["query_input_features"]
        if query_features.dim() == 3:
            query_features = query_features[:, None, :, :]
        query_count = query_ids.shape[1]
        if "query_mask" in batch:
            query_active = batch["query_mask"]
            if query_active.dim() == 1:
                query_active = query_active[:, None]
            query_active = query_active.to(torch.bool)
        else:
            query_active = torch.ones((bsz, query_count), dtype=torch.bool, device=device)
        board_ids.append(query_ids)
        board_masks.append(query_masks)
        board_features.append(query_features)
        board_active.append(query_active)
        board_roles.append(
            torch.full(
                (bsz, query_count),
                BottleneckBoardRoles.QUERY_INPUT,
                dtype=torch.long,
                device=device,
            )
        )

    packed_ids = torch.cat(board_ids, dim=1)
    num_boards = packed_ids.shape[1]
    slot_ids = torch.arange(num_boards, device=device, dtype=torch.long)[None, :].expand(bsz, -1)
    return {
        "board_ids": packed_ids,
        "board_roles": torch.cat(board_roles, dim=1),
        "board_slots": slot_ids,
        "board_active": torch.cat(board_active, dim=1),
        "board_masks": torch.cat(board_masks, dim=1),
        "board_features": torch.cat(board_features, dim=1),
    }


def pack_query_output_targets_from_bottleneck_batch(
    batch: dict[str, torch.Tensor],
    config: ArcSummaryAutoencoderConfig,
) -> dict[str, torch.Tensor]:
    """Pack hidden query outputs as decoder targets.

    These boards are never fed into the encoder. They only describe which
    output board slots the summary decoder should produce from the legal
    visible context: demo inputs, demo outputs, and query inputs.
    """
    labels = _as_query_slots(batch["labels"])
    bsz, query_count, num_cells = labels.shape
    device = labels.device
    target_masks = labels != -100
    target_ids = labels.masked_fill(~target_masks, config.null_color_id)
    query_active = batch.get("query_mask")
    if query_active is None:
        query_active = target_masks.any(dim=-1)
    elif query_active.dim() == 1:
        query_active = query_active[:, None]
    query_active = query_active.to(torch.bool)
    query_slots = (
        torch.arange(query_count, device=device, dtype=torch.long)[None, :]
        + (2 * config.max_context_pairs)
    ).expand(bsz, -1)
    query_roles = torch.full(
        (bsz, query_count),
        BottleneckBoardRoles.DEMO_OUTPUT,
        dtype=torch.long,
        device=device,
    )
    feature_labels = batch["feature_labels"]
    if feature_labels.dim() == 3:
        feature_labels = feature_labels[:, None, :, :]
    if feature_labels.shape[1] != query_count:
        raise ValueError(
            f"feature query count {feature_labels.shape[1]} does not match labels {query_count}"
        )
    return {
        "board_ids": target_ids,
        "board_roles": query_roles,
        "board_slots": query_slots,
        "board_active": query_active,
        "board_masks": target_masks,
        "board_features": feature_labels,
        "labels": target_ids,
    }


def pack_lodo_targets_from_bottleneck_batch(
    batch: dict[str, torch.Tensor],
    config: ArcSummaryAutoencoderConfig,
    *,
    target_pairs: Optional[torch.Tensor] = None,
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    """Build a leave-one-demo-output-out view and the hidden output target."""
    visible = pack_visible_boards_from_bottleneck_batch(batch, include_query_inputs=True)
    pair_mask = batch["pair_mask"].to(torch.bool)
    bsz, pair_count = pair_mask.shape
    device = pair_mask.device
    if target_pairs is None:
        target_pairs = torch.full((bsz,), -1, dtype=torch.long, device=device)
        for batch_idx in range(bsz):
            options = torch.nonzero(pair_mask[batch_idx], as_tuple=False).flatten()
            if options.numel() == 0:
                continue
            choice = torch.randint(options.numel(), (1,), device=device)
            target_pairs[batch_idx] = options[choice]
    target_pairs = target_pairs.to(device=device, dtype=torch.long)
    valid = (target_pairs >= 0) & (target_pairs < pair_count)
    safe_pairs = target_pairs.clamp(0, max(pair_count - 1, 0))

    output_slots = pair_count + safe_pairs
    visible["board_active"] = visible["board_active"].clone()
    visible["board_active"][torch.arange(bsz, device=device), output_slots] = False

    gather = safe_pairs[:, None, None].expand(-1, 1, config.num_positions)
    target_ids = batch["demo_output_ids"].gather(1, gather)
    target_masks = batch["demo_output_masks"].gather(1, gather)
    feature_gather = safe_pairs[:, None, None, None].expand(
        -1,
        1,
        config.num_positions,
        batch["demo_output_features"].shape[-1],
    )
    target_features = batch["demo_output_features"].gather(1, feature_gather)
    target_roles = torch.full(
        (bsz, 1),
        BottleneckBoardRoles.DEMO_OUTPUT,
        dtype=torch.long,
        device=device,
    )
    target_slots = output_slots[:, None]
    target_active = valid[:, None]
    target_ids = target_ids.masked_fill(~target_masks.to(torch.bool), config.null_color_id)
    target = {
        "board_ids": target_ids,
        "board_roles": target_roles,
        "board_slots": target_slots,
        "board_active": target_active,
        "board_masks": target_masks,
        "board_features": target_features,
        "labels": target_ids,
    }
    return visible, target


class VisibleBoardCellEncoder(nn.Module):
    """Encode each visible board as 900 contextual cell states."""

    def __init__(self, config: ArcSummaryAutoencoderConfig) -> None:
        super().__init__()
        self.config = config
        self.color_embedding = nn.Embedding(config.cell_vocab_size, config.d_model)
        self.row_embedding = nn.Embedding(config.canvas_size, config.d_model)
        self.col_embedding = nn.Embedding(config.canvas_size, config.d_model)
        self.role_embedding = nn.Embedding(config.num_board_roles, config.d_model)
        self.board_slot_embedding = nn.Embedding(config.max_visible_boards, config.d_model)
        self.mask_embedding = nn.Embedding(2, config.d_model) if config.use_grid_masks else None
        if config.use_grid_features:
            self.feature_embeddings = nn.ModuleList(
                [nn.Embedding(vocab_size, config.d_model) for vocab_size in GRID_FEATURE_VOCAB_SIZES]
            )
        else:
            self.feature_embeddings = None
        self.input_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.conv_blocks = nn.ModuleList([ConvBlock(config.d_model) for _ in range(config.grid_conv_layers)])

        rows = torch.arange(config.canvas_size).repeat_interleave(config.canvas_size)
        cols = torch.arange(config.canvas_size).repeat(config.canvas_size)
        self.register_buffer("row_ids", rows, persistent=False)
        self.register_buffer("col_ids", cols, persistent=False)

    def forward(
        self,
        board_ids: torch.Tensor,
        board_roles: torch.Tensor,
        board_slots: torch.Tensor,
        board_active: torch.Tensor,
        board_masks: Optional[torch.Tensor] = None,
        board_features: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bsz, num_boards, num_cells = board_ids.shape
        if num_cells != self.config.num_positions:
            raise ValueError(f"expected {self.config.num_positions} cells, got {num_cells}")
        if num_boards > self.config.max_visible_boards:
            raise ValueError(
                f"num_boards={num_boards} exceeds max_visible_boards={self.config.max_visible_boards}"
            )

        flat_ids = board_ids.clamp(0, self.config.cell_vocab_size - 1).reshape(bsz * num_boards, num_cells)
        flat_roles = board_roles.reshape(bsz * num_boards).clamp(0, self.config.num_board_roles - 1)
        flat_slots = board_slots.reshape(bsz * num_boards).clamp(0, self.config.max_visible_boards - 1)
        flat_active = board_active.reshape(bsz * num_boards).to(torch.bool)
        flat_mask = None
        if board_masks is not None:
            flat_mask = board_masks.reshape(bsz * num_boards, num_cells).to(torch.bool)

        x = (
            self.color_embedding(flat_ids)
            + self.row_embedding(self.row_ids)[None, :, :]
            + self.col_embedding(self.col_ids)[None, :, :]
            + self.role_embedding(flat_roles)[:, None, :]
            + self.board_slot_embedding(flat_slots)[:, None, :]
        )
        if self.mask_embedding is not None and flat_mask is not None:
            x = x + self.mask_embedding(flat_mask.to(torch.long))
        if self.feature_embeddings is not None and board_features is not None:
            flat_features = board_features.reshape(bsz * num_boards, num_cells, -1)
            if flat_features.shape[-1] != len(self.feature_embeddings):
                raise ValueError(
                    f"expected {len(self.feature_embeddings)} feature channels, got {flat_features.shape[-1]}"
                )
            for idx, embedding in enumerate(self.feature_embeddings):
                feature_ids = flat_features[..., idx].clamp(0, embedding.num_embeddings - 1)
                x = x + embedding(feature_ids)

        x = self.input_norm(x)
        active_cell_mask = flat_active[:, None]
        if flat_mask is not None:
            active_cell_mask = active_cell_mask & flat_mask
        x = x * active_cell_mask[:, :, None].to(x.dtype)

        h = self.config.canvas_size
        mask2d = active_cell_mask[:, None, :].reshape(bsz * num_boards, 1, h, h).to(x.dtype)
        x2d = x.transpose(1, 2).reshape(bsz * num_boards, self.config.d_model, h, h)
        for block in self.conv_blocks:
            x2d = maybe_checkpoint(
                block,
                x2d,
                enabled=self.config.activation_checkpointing and self.training,
            )
            x2d = x2d * mask2d
        return x2d.reshape(bsz, num_boards, self.config.d_model, num_cells).transpose(2, 3)


class ArcSummaryAutoencoderModel(nn.Module):
    """Compress visible ARC boards into summary tokens, then reconstruct them."""

    def __init__(self, config: ArcSummaryAutoencoderConfig) -> None:
        super().__init__()
        _ = config.head_dim
        self.config = config
        self.cell_encoder = VisibleBoardCellEncoder(config)
        self.summary_tokens = nn.Parameter(torch.randn(config.summary_tokens, config.d_model) * 0.02)
        self.summary_vocab_embedding = nn.Embedding(config.summary_vocab_size, config.d_model)
        self.summary_codebook_embedding = nn.Embedding(config.summary_vocab_size, config.d_model)
        self.summary_cross_blocks = nn.ModuleList(
            [CrossAttentionBlock(config, self_attention=True) for _ in range(config.summary_cross_layers)]
        )
        self.summary_blocks = nn.ModuleList(
            [SelfAttentionBlock(config) for _ in range(config.summary_layers)]
        )
        self.diagnostic_blocks = nn.ModuleList(
            [SelfAttentionBlock(config) for _ in range(config.diagnostic_layers)]
        )

        self.decoder_position_embedding = nn.Embedding(config.num_positions, config.d_model)
        self.decoder_role_embedding = nn.Embedding(config.num_board_roles, config.d_model)
        self.decoder_slot_embedding = nn.Embedding(config.max_visible_boards, config.d_model)
        self.decoder_blocks = nn.ModuleList(
            [
                CrossAttentionBlock(config, self_attention=config.decoder_self_attention)
                for _ in range(config.decoder_layers)
            ]
        )
        self.final_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.reconstruction_head = nn.Linear(config.d_model, config.cell_vocab_size, bias=True)
        self.inside_head = nn.Linear(config.d_model, 1, bias=True)
        self.height_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        self.width_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        if config.use_grid_features and config.grid_feature_loss_weight > 0:
            self.feature_heads = nn.ModuleList(
                [nn.Linear(config.d_model, vocab_size, bias=True) for vocab_size in GRID_FEATURE_VOCAB_SIZES]
            )
        else:
            self.feature_heads = None
        if config.jepa_loss_weight > 0:
            jepa_hidden = config.d_model * config.jepa_predictor_ratio
            self.jepa_summary_norm = RMSNorm(config.d_model, config.layer_norm_eps)
            self.jepa_target_norm = RMSNorm(config.d_model, config.layer_norm_eps)
            self.jepa_predictor = nn.Sequential(
                nn.Linear(config.d_model * 2, jepa_hidden, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(jepa_hidden, config.d_model, bias=config.use_bias),
            )
        else:
            self.jepa_summary_norm = None
            self.jepa_target_norm = None
            self.jepa_predictor = None
        if config.board_structure_loss_weight > 0:
            self.board_structure_mlp = nn.Sequential(
                nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
            )
            self.board_symmetry_head = nn.Linear(config.d_model, 4, bias=True)
            self.board_color_presence_head = nn.Linear(config.d_model, config.num_arc_colors, bias=True)
            self.board_nonzero_count_head = nn.Linear(config.d_model, 8, bias=True)
            self.board_color_count_head = nn.Linear(config.d_model, config.num_arc_colors * 8, bias=True)
            self.board_local_signature_head = nn.Linear(config.d_model, 4 * 8, bias=True)
            self.board_topology_head = nn.Linear(config.d_model, 4 * 8, bias=True)
        else:
            self.board_structure_mlp = None
            self.board_symmetry_head = None
            self.board_color_presence_head = None
            self.board_nonzero_count_head = None
            self.board_color_count_head = None
            self.board_local_signature_head = None
            self.board_topology_head = None
        if config.pair_diff_loss_weight > 0:
            self.pair_diff_mlp = nn.Sequential(
                nn.Linear(config.d_model * 4, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
            )
            self.pair_diff_position_embedding = nn.Embedding(config.num_positions, config.d_model)
            self.pair_diff_mask_head = nn.Sequential(
                nn.Linear(config.d_model, config.d_model, bias=config.use_bias),
                nn.GELU(approximate="tanh"),
                nn.Linear(config.d_model, 1, bias=True),
            )
            self.pair_same_shape_head = nn.Linear(config.d_model, 1, bias=True)
            self.pair_diff_count_head = nn.Linear(config.d_model, 8, bias=True)
            self.pair_color_delta_head = nn.Linear(config.d_model, config.num_arc_colors * 7, bias=True)
            self.pair_color_transition_head = nn.Linear(
                config.d_model,
                config.num_arc_colors * config.num_arc_colors,
                bias=True,
            )
        else:
            self.pair_diff_mlp = None
            self.pair_diff_position_embedding = None
            self.pair_diff_mask_head = None
            self.pair_same_shape_head = None
            self.pair_diff_count_head = None
            self.pair_color_delta_head = None
            self.pair_color_transition_head = None

        pos = torch.arange(config.num_positions)
        summary_vocab_ids = torch.arange(config.summary_tokens) % config.summary_vocab_size
        self.register_buffer("position_ids", pos, persistent=False)
        self.register_buffer("summary_vocab_ids", summary_vocab_ids, persistent=False)
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def _context_mask(
        self,
        board_active: torch.Tensor,
        board_masks: Optional[torch.Tensor],
        num_cells: int,
    ) -> torch.Tensor:
        if board_masks is None:
            mask = board_active[:, :, None].expand(-1, -1, num_cells)
        else:
            mask = board_active[:, :, None].to(torch.bool) & board_masks.to(torch.bool)
        mask = mask.reshape(mask.shape[0], -1)
        empty_rows = ~mask.any(dim=1)
        if empty_rows.any():
            mask = mask.clone()
            mask[empty_rows, 0] = True
        return mask

    def _shape_labels(
        self,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        bsz, num_boards, _ = board_masks.shape
        h = self.config.canvas_size
        mask2d = board_masks.reshape(bsz, num_boards, h, h).to(torch.bool)
        heights = mask2d.any(dim=-1).sum(dim=-1) - 1
        widths = mask2d.any(dim=-2).sum(dim=-1) - 1
        active = board_active.to(torch.bool) & mask2d.reshape(bsz, num_boards, -1).any(dim=-1)
        heights = heights.masked_fill(~active, -100).to(torch.long)
        widths = widths.masked_fill(~active, -100).to(torch.long)
        return heights, widths

    def _build_summary(self, context: torch.Tensor, context_mask: torch.Tensor) -> torch.Tensor:
        bsz = context.shape[0]
        summary = (
            self.summary_tokens[None, :, :]
            + self.summary_vocab_embedding(self.summary_vocab_ids)[None, :, :]
        ).expand(bsz, -1, -1)
        for block in self.summary_cross_blocks:
            summary = maybe_checkpoint(
                block,
                summary,
                context,
                enabled=self.config.activation_checkpointing and self.training,
                context_mask=context_mask,
            )
        for block in self.summary_blocks:
            summary = maybe_checkpoint(
                block,
                summary,
                enabled=self.config.activation_checkpointing and self.training,
            )
        return summary

    def _build_diagnostic_summary(self, summary: torch.Tensor) -> torch.Tensor:
        diagnostic = summary
        for block in self.diagnostic_blocks:
            diagnostic = maybe_checkpoint(
                block,
                diagnostic,
                enabled=self.config.activation_checkpointing and self.training,
            )
        return diagnostic

    def _quantize_summary(
        self,
        summary: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        summary_norm = F.normalize(summary.float(), dim=-1)
        codebook = self.summary_codebook_embedding.weight
        codebook_norm = F.normalize(codebook.float(), dim=-1)
        logits = torch.matmul(summary_norm, codebook_norm.t())
        if self.config.summary_code_temperature != 1.0:
            logits = logits / max(float(self.config.summary_code_temperature), 1e-6)
        code_indices = logits.argmax(dim=-1)
        quantized = self.summary_codebook_embedding(code_indices)

        codebook_loss = F.mse_loss(quantized.float(), summary.detach().float())
        commitment_loss = F.mse_loss(summary.float(), quantized.detach().float())
        quantized_summary = summary + (quantized - summary).detach()

        usage_loss = summary.new_zeros(())
        if self.config.summary_code_entropy_loss_weight > 0:
            probs = F.softmax(logits.float(), dim=-1)
            avg_probs = probs.mean(dim=(0, 1)).clamp_min(1e-12)
            entropy = -(avg_probs * avg_probs.log()).sum()
            usage_loss = 1.0 - entropy / torch.log(
                torch.tensor(float(self.config.summary_vocab_size), device=summary.device)
            )

        with torch.no_grad():
            counts = torch.bincount(code_indices.reshape(-1), minlength=self.config.summary_vocab_size)
            probs = counts.to(torch.float32) / counts.sum().clamp_min(1)
            entropy = -(probs[probs > 0] * probs[probs > 0].log()).sum()
            perplexity = entropy.exp()
        return quantized_summary, code_indices, codebook_loss, commitment_loss, usage_loss, perplexity

    def _jepa_context_mask(
        self,
        base_mask: torch.Tensor,
        board_active: torch.Tensor,
        target_indices: torch.Tensor,
        num_cells: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        bsz, num_boards = board_active.shape
        valid = (
            (target_indices >= 0)
            & (target_indices < num_boards)
            & board_active.gather(1, target_indices.clamp(0, num_boards - 1)[:, None]).squeeze(1).to(torch.bool)
        )
        mask = base_mask.clone()
        rows = torch.arange(bsz, device=mask.device)
        safe_indices = target_indices.clamp(0, num_boards - 1)
        for row, board_idx in zip(rows[valid].tolist(), safe_indices[valid].tolist()):
            start = board_idx * num_cells
            mask[row, start : start + num_cells] = False
        empty_rows = ~mask.any(dim=1)
        if empty_rows.any():
            mask[empty_rows, 0] = True
        return mask, valid

    def _board_mean_pool(
        self,
        states: torch.Tensor,
        board_masks: Optional[torch.Tensor],
        board_active: torch.Tensor,
    ) -> torch.Tensor:
        if board_masks is None:
            weights = board_active[:, :, None].to(states.dtype).expand(states.shape[:-1])
        else:
            weights = (board_masks.to(torch.bool) & board_active[:, :, None].to(torch.bool)).to(states.dtype)
        denom = weights.sum(dim=-1).clamp_min(1.0)
        return (states * weights[..., None]).sum(dim=2) / denom[..., None]

    def _count_bucket(self, counts: torch.Tensor) -> torch.Tensor:
        buckets = torch.zeros_like(counts, dtype=torch.long)
        buckets = torch.where(counts == 1, torch.ones_like(buckets), buckets)
        buckets = torch.where(counts == 2, torch.full_like(buckets, 2), buckets)
        buckets = torch.where((counts > 2) & (counts <= 4), torch.full_like(buckets, 3), buckets)
        buckets = torch.where((counts > 4) & (counts <= 8), torch.full_like(buckets, 4), buckets)
        buckets = torch.where((counts > 8) & (counts <= 16), torch.full_like(buckets, 5), buckets)
        buckets = torch.where((counts > 16) & (counts <= 32), torch.full_like(buckets, 6), buckets)
        buckets = torch.where(counts > 32, torch.full_like(buckets, 7), buckets)
        return buckets

    def _signed_count_bucket(self, deltas: torch.Tensor) -> torch.Tensor:
        buckets = torch.full_like(deltas, 3, dtype=torch.long)
        buckets = torch.where(deltas <= -8, torch.zeros_like(buckets), buckets)
        buckets = torch.where((deltas > -8) & (deltas <= -2), torch.full_like(buckets, 1), buckets)
        buckets = torch.where(deltas == -1, torch.full_like(buckets, 2), buckets)
        buckets = torch.where(deltas == 1, torch.full_like(buckets, 4), buckets)
        buckets = torch.where((deltas >= 2) & (deltas < 8), torch.full_like(buckets, 5), buckets)
        buckets = torch.where(deltas >= 8, torch.full_like(buckets, 6), buckets)
        return buckets

    def _sample_reconstruction_weights(
        self,
        cell_weights: torch.Tensor,
        active: torch.Tensor,
        board_masks: Optional[torch.Tensor],
    ) -> torch.Tensor:
        if not self.training:
            return cell_weights
        fraction = max(0.0, min(1.0, float(self.config.reconstruction_sample_fraction)))
        full_prob = max(0.0, min(1.0, float(self.config.reconstruction_full_prob)))
        if fraction >= 1.0 or torch.rand((), device=cell_weights.device).item() < full_prob:
            return cell_weights

        bsz, num_boards, num_cells = cell_weights.shape
        if board_masks is not None:
            candidates = active[:, :, None] & board_masks.to(torch.bool)
        else:
            candidates = cell_weights > 0
        flat_candidates = candidates.reshape(bsz * num_boards, num_cells)
        flat_weights = cell_weights.reshape(bsz * num_boards, num_cells)
        sampled = torch.zeros_like(flat_candidates)
        sample_min = max(0, int(self.config.reconstruction_sample_min))
        for row_idx, row_candidates in enumerate(flat_candidates):
            positions = torch.nonzero(row_candidates, as_tuple=False).flatten()
            count = int(positions.numel())
            if count == 0:
                continue
            by_fraction = int(count * fraction + 0.999999)
            k = max(1, sample_min, by_fraction)
            k = min(k, count)
            choice = torch.randperm(count, device=cell_weights.device)[:k]
            sampled[row_idx, positions[choice]] = True
        return (flat_weights * sampled.to(flat_weights.dtype)).reshape_as(cell_weights)

    def _symmetry_labels(
        self,
        board_ids: torch.Tensor,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> torch.Tensor:
        bsz, num_boards, _ = board_ids.shape
        h = self.config.canvas_size
        ids = board_ids.reshape(bsz, num_boards, h, h)
        masks = board_masks.reshape(bsz, num_boards, h, h).to(torch.bool)
        labels = torch.zeros((bsz, num_boards, 4), dtype=torch.float32, device=board_ids.device)
        for batch_idx in range(bsz):
            for board_idx in range(num_boards):
                if not bool(board_active[batch_idx, board_idx]):
                    continue
                mask = masks[batch_idx, board_idx]
                rows = torch.nonzero(mask.any(dim=1), as_tuple=False).flatten()
                cols = torch.nonzero(mask.any(dim=0), as_tuple=False).flatten()
                if rows.numel() == 0 or cols.numel() == 0:
                    continue
                height = int(rows[-1].item()) + 1
                width = int(cols[-1].item()) + 1
                grid = ids[batch_idx, board_idx, :height, :width]
                labels[batch_idx, board_idx, 0] = float(torch.equal(grid, torch.flip(grid, dims=[1])))
                labels[batch_idx, board_idx, 1] = float(torch.equal(grid, torch.flip(grid, dims=[0])))
                labels[batch_idx, board_idx, 2] = float(torch.equal(grid, torch.flip(grid, dims=[0, 1])))
                if height == width:
                    labels[batch_idx, board_idx, 3] = float(torch.equal(grid, torch.rot90(grid, k=1, dims=(0, 1))))
        return labels

    def _local_signature_labels(
        self,
        board_ids: torch.Tensor,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> torch.Tensor:
        bsz, num_boards, _ = board_ids.shape
        h = self.config.canvas_size
        ids = board_ids.reshape(bsz, num_boards, h, h)
        real = board_masks.reshape(bsz, num_boards, h, h).to(torch.bool) & board_active[:, :, None, None].to(torch.bool)
        foreground = real & (ids != 0) & (ids != self.config.null_color_id)

        def shifted(delta_r: int, delta_c: int) -> tuple[torch.Tensor, torch.Tensor]:
            neighbor_ids = torch.full_like(ids, self.config.null_color_id)
            neighbor_real = torch.zeros_like(real)
            src_r0 = max(0, -delta_r)
            src_r1 = h - max(0, delta_r)
            src_c0 = max(0, -delta_c)
            src_c1 = h - max(0, delta_c)
            dst_r0 = max(0, delta_r)
            dst_r1 = h - max(0, -delta_r)
            dst_c0 = max(0, delta_c)
            dst_c1 = h - max(0, -delta_c)
            neighbor_ids[..., dst_r0:dst_r1, dst_c0:dst_c1] = ids[..., src_r0:src_r1, src_c0:src_c1]
            neighbor_real[..., dst_r0:dst_r1, dst_c0:dst_c1] = real[..., src_r0:src_r1, src_c0:src_c1]
            return neighbor_ids, neighbor_real

        cardinals = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        diagonals = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        neighbor_data = [shifted(dr, dc) for dr, dc in cardinals + diagonals]
        valid = torch.stack([item[1] for item in neighbor_data], dim=0)
        equal = torch.stack([(item[0] == ids) & item[1] for item in neighbor_data], dim=0)
        valid4 = valid[:4]
        valid8 = valid
        equal4 = equal[:4]
        equal8 = equal
        has4 = valid4.any(dim=0)
        has8 = valid8.any(dim=0)
        same4 = foreground & has4 & (equal4 | ~valid4).all(dim=0)
        same8 = foreground & has8 & (equal8 | ~valid8).all(dim=0)
        isolated4 = foreground & ~equal4.any(dim=0)
        boundary4 = foreground & (valid4.sum(dim=0) < 4)
        counts = torch.stack(
            [
                same4.sum(dim=(-1, -2)),
                same8.sum(dim=(-1, -2)),
                isolated4.sum(dim=(-1, -2)),
                boundary4.sum(dim=(-1, -2)),
            ],
            dim=-1,
        )
        return self._count_bucket(counts)

    def _topology_proxy_labels(
        self,
        board_ids: torch.Tensor,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> torch.Tensor:
        bsz, num_boards, _ = board_ids.shape
        h = self.config.canvas_size
        ids = board_ids.reshape(bsz, num_boards, h, h)
        real = board_masks.reshape(bsz, num_boards, h, h).to(torch.bool)
        foreground = real & board_active[:, :, None, None].to(torch.bool) & (ids != 0) & (ids != self.config.null_color_id)
        labels = torch.zeros((bsz, num_boards, 4), dtype=torch.long, device=board_ids.device)
        for batch_idx in range(bsz):
            for board_idx in range(num_boards):
                if not bool(board_active[batch_idx, board_idx]):
                    continue
                cells = foreground[batch_idx, board_idx]
                if not bool(cells.any()):
                    continue
                rows = torch.nonzero(cells.any(dim=1), as_tuple=False).flatten()
                cols = torch.nonzero(cells.any(dim=0), as_tuple=False).flatten()
                bbox_h = rows[-1] - rows[0] + 1
                bbox_w = cols[-1] - cols[0] + 1
                bbox_area = bbox_h * bbox_w
                bbox_real = real[batch_idx, board_idx, rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
                bbox_ids = ids[batch_idx, board_idx, rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
                hole_proxy = bbox_real & (bbox_ids == 0)
                labels[batch_idx, board_idx, 0] = self._count_bucket(bbox_h[None])[0]
                labels[batch_idx, board_idx, 1] = self._count_bucket(bbox_w[None])[0]
                labels[batch_idx, board_idx, 2] = self._count_bucket(bbox_area[None])[0]
                labels[batch_idx, board_idx, 3] = self._count_bucket(hole_proxy.sum()[None])[0]
        return labels

    def _board_structure_labels(
        self,
        board_ids: torch.Tensor,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        real = board_masks.to(torch.bool) & board_active[:, :, None].to(torch.bool)
        symmetry = self._symmetry_labels(board_ids, board_masks, board_active)
        color_presence = torch.stack(
            [(real & (board_ids == color)).any(dim=-1).to(torch.float32) for color in range(self.config.num_arc_colors)],
            dim=-1,
        )
        color_counts = torch.stack(
            [(real & (board_ids == color)).sum(dim=-1) for color in range(self.config.num_arc_colors)],
            dim=-1,
        )
        nonzero = real & (board_ids != 0) & (board_ids != self.config.null_color_id)
        nonzero_count = nonzero.sum(dim=-1)
        nonzero_bucket = self._count_bucket(nonzero_count)
        color_count_bucket = self._count_bucket(color_counts)
        local_signature_bucket = self._local_signature_labels(board_ids, board_masks, board_active)
        topology_bucket = self._topology_proxy_labels(board_ids, board_masks, board_active)
        return (
            symmetry,
            color_presence,
            nonzero_bucket,
            color_count_bucket,
            local_signature_bucket,
            topology_bucket,
        )

    def _pair_diff_labels(
        self,
        board_ids: torch.Tensor,
        board_masks: torch.Tensor,
        board_active: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        pairs = min(self.config.max_context_pairs, board_ids.shape[1] // 2)
        input_ids = board_ids[:, :pairs]
        output_ids = board_ids[:, pairs : 2 * pairs]
        input_masks = board_masks[:, :pairs].to(torch.bool)
        output_masks = board_masks[:, pairs : 2 * pairs].to(torch.bool)
        pair_active = board_active[:, :pairs].to(torch.bool) & board_active[:, pairs : 2 * pairs].to(torch.bool)
        valid = (input_masks | output_masks) & pair_active[:, :, None]
        diff = ((input_ids != output_ids) | (input_masks != output_masks)) & valid
        same_shape = (input_masks == output_masks).all(dim=-1).to(torch.float32)
        diff_count_bucket = self._count_bucket(diff.sum(dim=-1))
        input_color_counts = torch.stack(
            [(input_masks & (input_ids == color)).sum(dim=-1) for color in range(self.config.num_arc_colors)],
            dim=-1,
        )
        output_color_counts = torch.stack(
            [(output_masks & (output_ids == color)).sum(dim=-1) for color in range(self.config.num_arc_colors)],
            dim=-1,
        )
        color_delta_bucket = self._signed_count_bucket(output_color_counts - input_color_counts)
        transition_valid = input_masks & output_masks & pair_active[:, :, None]
        transitions = torch.stack(
            [
                ((input_ids == old_color) & (output_ids == new_color) & transition_valid).any(dim=-1).to(torch.float32)
                for old_color in range(self.config.num_arc_colors)
                for new_color in range(self.config.num_arc_colors)
            ],
            dim=-1,
        )
        return diff.to(torch.float32), valid, same_shape, diff_count_bucket, color_delta_bucket, transitions

    def forward(
        self,
        *,
        board_ids: torch.Tensor,
        board_roles: torch.Tensor,
        board_active: torch.Tensor,
        board_slots: Optional[torch.Tensor] = None,
        board_masks: Optional[torch.Tensor] = None,
        board_features: Optional[torch.Tensor] = None,
        decode_board_roles: Optional[torch.Tensor] = None,
        decode_board_active: Optional[torch.Tensor] = None,
        decode_board_slots: Optional[torch.Tensor] = None,
        decode_board_masks: Optional[torch.Tensor] = None,
        decode_board_features: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        jepa_target_indices: Optional[torch.Tensor] = None,
        decode_visible_boards: bool = True,
        return_summary: bool = True,
    ) -> ArcSummaryAutoencoderOutput:
        bsz, num_boards, num_cells = board_ids.shape
        if board_slots is None:
            board_slots = torch.arange(num_boards, device=board_ids.device, dtype=torch.long)
            board_slots = board_slots[None, :].expand(bsz, -1)
        has_separate_decode_boards = (
            decode_board_roles is not None
            or decode_board_active is not None
            or decode_board_slots is not None
            or decode_board_masks is not None
            or decode_board_features is not None
        )
        if labels is None and not has_separate_decode_boards:
            labels = board_ids

        context_active = board_active.to(torch.bool)
        cell_states = self.cell_encoder(
            board_ids=board_ids,
            board_roles=board_roles,
            board_slots=board_slots,
            board_active=board_active,
            board_masks=board_masks,
            board_features=board_features,
        )
        context = cell_states.reshape(bsz, num_boards * num_cells, self.config.d_model)
        context_mask = self._context_mask(board_active, board_masks, num_cells)

        if decode_board_roles is None:
            decode_board_roles = board_roles
        if decode_board_active is None:
            decode_board_active = board_active
        if decode_board_slots is None:
            decode_num_boards = decode_board_roles.shape[1]
            decode_board_slots = torch.arange(
                decode_num_boards,
                device=board_ids.device,
                dtype=torch.long,
            )[None, :].expand(bsz, -1)
        if decode_board_masks is None:
            decode_board_masks = board_masks
        if decode_board_features is None:
            decode_board_features = board_features
        decode_num_boards = decode_board_roles.shape[1]
        decode_active_bool = decode_board_active.to(torch.bool)

        summary = self._build_summary(context, context_mask)
        summary_code_indices = None
        summary_codebook_loss = None
        summary_commitment_loss = None
        summary_code_entropy_loss = None
        summary_code_perplexity = None
        if self.config.discrete_summary:
            (
                summary,
                summary_code_indices,
                summary_codebook_loss,
                summary_commitment_loss,
                summary_code_entropy_loss,
                summary_code_perplexity,
            ) = self._quantize_summary(summary)

        summary_for_board_probe = summary
        if self.diagnostic_blocks and (
            self.board_structure_mlp is not None or self.pair_diff_mlp is not None
        ):
            summary_for_board_probe = self._build_diagnostic_summary(summary)

        flat_active = decode_active_bool.reshape(-1)
        active_rows = flat_active.nonzero(as_tuple=False).squeeze(1)
        flat_count = bsz * decode_num_boards
        flat_reconstruction = summary.new_zeros((flat_count, num_cells, self.config.cell_vocab_size))
        flat_inside = summary.new_zeros((flat_count, num_cells))
        flat_height = summary.new_zeros((flat_count, self.config.canvas_size))
        flat_width = summary.new_zeros((flat_count, self.config.canvas_size))
        flat_board_state = summary.new_zeros((flat_count, self.config.d_model))
        flat_feature_logits = (
            [
                summary.new_zeros((flat_count, num_cells, vocab_size))
                for vocab_size in GRID_FEATURE_VOCAB_SIZES
            ]
            if self.feature_heads is not None
            else None
        )

        needs_board_probe = (
            not decode_visible_boards
            and (
                self.config.shape_loss_weight > 0
                or self.board_structure_mlp is not None
                or self.pair_diff_mlp is not None
            )
        )

        if active_rows.numel() > 0 and (decode_visible_boards or needs_board_probe):
            batch_rows = active_rows // decode_num_boards
            active_roles = decode_board_roles.reshape(-1)[active_rows].clamp(0, self.config.num_board_roles - 1)
            active_slots = decode_board_slots.reshape(-1)[active_rows].clamp(0, self.config.max_visible_boards - 1)
            if decode_visible_boards:
                pos = self.decoder_position_embedding(self.position_ids)
                decode = (
                    pos[None, :, :]
                    + self.decoder_role_embedding(active_roles)[:, None, :]
                    + self.decoder_slot_embedding(active_slots)[:, None, :]
                )
            else:
                decode = (
                    self.decoder_role_embedding(active_roles)[:, None, :]
                    + self.decoder_slot_embedding(active_slots)[:, None, :]
                )
            summary_source = summary_for_board_probe if needs_board_probe and not decode_visible_boards else summary
            summary_context = summary_source[batch_rows]
            for block in self.decoder_blocks:
                decode = maybe_checkpoint(
                    block,
                    decode,
                    summary_context,
                    enabled=self.config.activation_checkpointing and self.training,
                )
            decode = self.final_norm(decode)
            active_board_state = decode.mean(dim=1)
            active_board_state = active_board_state.to(flat_board_state.dtype)
            flat_height = flat_height.index_copy(0, active_rows, self.height_head(active_board_state))
            flat_width = flat_width.index_copy(0, active_rows, self.width_head(active_board_state))
            flat_board_state = flat_board_state.index_copy(0, active_rows, active_board_state)
            if decode_visible_boards:
                flat_reconstruction = flat_reconstruction.index_copy(0, active_rows, self.reconstruction_head(decode))
                flat_inside = flat_inside.index_copy(0, active_rows, self.inside_head(decode).squeeze(-1))
            if decode_visible_boards and flat_feature_logits is not None and self.feature_heads is not None:
                for idx, head in enumerate(self.feature_heads):
                    flat_feature_logits[idx] = flat_feature_logits[idx].index_copy(0, active_rows, head(decode))

        reconstruction_logits = flat_reconstruction.reshape(
            bsz, decode_num_boards, num_cells, self.config.cell_vocab_size
        )
        inside_logits = flat_inside.reshape(bsz, decode_num_boards, num_cells)
        height_logits = flat_height.reshape(bsz, decode_num_boards, self.config.canvas_size)
        width_logits = flat_width.reshape(bsz, decode_num_boards, self.config.canvas_size)
        board_state = flat_board_state.reshape(bsz, decode_num_boards, self.config.d_model)
        feature_logits = (
            [logits.reshape(bsz, decode_num_boards, num_cells, logits.shape[-1]) for logits in flat_feature_logits]
            if flat_feature_logits is not None
            else None
        )
        jepa_pred = None
        jepa_target = None
        jepa_retrieval_logits = None
        board_symmetry_logits = None
        board_color_presence_logits = None
        board_nonzero_count_logits = None
        board_color_count_logits = None
        board_local_signature_logits = None
        board_topology_logits = None
        pair_diff_logits = None
        pair_same_shape_logits = None
        pair_diff_count_logits = None
        pair_color_delta_logits = None
        pair_color_transition_logits = None
        if self.board_structure_mlp is not None and not has_separate_decode_boards:
            structure_states = self.board_structure_mlp(board_state)
            board_symmetry_logits = self.board_symmetry_head(structure_states)
            board_color_presence_logits = self.board_color_presence_head(structure_states)
            board_nonzero_count_logits = self.board_nonzero_count_head(structure_states)
            board_color_count_logits = self.board_color_count_head(structure_states).reshape(
                bsz,
                decode_num_boards,
                self.config.num_arc_colors,
                8,
            )
            board_local_signature_logits = self.board_local_signature_head(structure_states).reshape(
                bsz,
                decode_num_boards,
                4,
                8,
            )
            board_topology_logits = self.board_topology_head(structure_states).reshape(
                bsz,
                decode_num_boards,
                4,
                8,
            )
        if (
            self.pair_diff_mlp is not None
            and not has_separate_decode_boards
            and decode_num_boards >= 2 * self.config.max_context_pairs
        ):
            pairs = self.config.max_context_pairs
            pair_in = board_state[:, :pairs]
            pair_out = board_state[:, pairs : 2 * pairs]
            pair_features = torch.cat([pair_in, pair_out, pair_out - pair_in, pair_in * pair_out], dim=-1)
            pair_states = self.pair_diff_mlp(pair_features)
            pair_same_shape_logits = self.pair_same_shape_head(pair_states).squeeze(-1)
            pair_diff_count_logits = self.pair_diff_count_head(pair_states)
            pair_color_delta_logits = self.pair_color_delta_head(pair_states).reshape(
                bsz,
                pairs,
                self.config.num_arc_colors,
                7,
            )
            pair_color_transition_logits = self.pair_color_transition_head(pair_states).reshape(
                bsz,
                pairs,
                self.config.num_arc_colors * self.config.num_arc_colors,
            )
            pair_pos = self.pair_diff_position_embedding(self.position_ids)
            pair_cell_states = pair_states[:, :, None, :] + pair_pos[None, None, :, :]
            pair_diff_logits = self.pair_diff_mask_head(pair_cell_states).squeeze(-1)

        loss = None
        reconstruction_loss = None
        hard_cell_loss = None
        cell_margin_loss = None
        inside_loss = None
        shape_loss = None
        feature_loss = None
        jepa_loss = None
        jepa_retrieval_loss = None
        board_structure_loss = None
        pair_diff_loss = None
        if summary_codebook_loss is not None and self.config.summary_codebook_loss_weight > 0:
            loss = self.config.summary_codebook_loss_weight * summary_codebook_loss
        if summary_commitment_loss is not None and self.config.summary_commitment_loss_weight > 0:
            loss = (
                self.config.summary_commitment_loss_weight * summary_commitment_loss
                if loss is None
                else loss + self.config.summary_commitment_loss_weight * summary_commitment_loss
            )
        if summary_code_entropy_loss is not None and self.config.summary_code_entropy_loss_weight > 0:
            loss = (
                self.config.summary_code_entropy_loss_weight * summary_code_entropy_loss
                if loss is None
                else loss + self.config.summary_code_entropy_loss_weight * summary_code_entropy_loss
            )
        decode_cell_losses = (
            decode_visible_boards
            and labels is not None
            and (
                self.config.reconstruction_loss_weight > 0
                or self.config.hard_cell_loss_weight > 0
                or self.config.cell_margin_loss_weight > 0
            )
        )
        if decode_cell_losses:
            if labels.shape != (bsz, decode_num_boards, num_cells):
                raise ValueError(
                    "labels must match decoder target shape "
                    f"{(bsz, decode_num_boards, num_cells)}, got {tuple(labels.shape)}"
                )
            targets = labels.clamp(0, self.config.cell_vocab_size - 1)
            raw_recon = F.cross_entropy(
                reconstruction_logits.reshape(-1, self.config.cell_vocab_size),
                targets.reshape(-1),
                reduction="none",
            ).reshape(bsz, decode_num_boards, num_cells)
            if decode_board_masks is not None:
                cell_weights = torch.where(
                    decode_board_masks.to(torch.bool),
                    torch.ones_like(raw_recon),
                    torch.full_like(raw_recon, self.config.null_reconstruction_weight),
                )
            else:
                cell_weights = torch.ones_like(raw_recon)
            cell_weights = cell_weights * decode_active_bool[:, :, None].to(cell_weights.dtype)
            cell_weights = self._sample_reconstruction_weights(cell_weights, decode_active_bool, decode_board_masks)
            denom = cell_weights.sum(dim=-1).clamp_min(1.0)
            per_board = (raw_recon * cell_weights).sum(dim=-1) / denom
            if decode_active_bool.any():
                reconstruction_loss = per_board[decode_active_bool].mean()
                loss = (
                    self.config.reconstruction_loss_weight * reconstruction_loss
                    if loss is None
                    else loss + self.config.reconstruction_loss_weight * reconstruction_loss
                )

            active_cells = decode_active_bool[:, :, None].expand_as(targets)
            exact_pressure_cells = active_cells
            if decode_board_masks is not None:
                exact_pressure_cells = exact_pressure_cells & decode_board_masks.to(torch.bool)
            if not exact_pressure_cells.any():
                exact_pressure_cells = active_cells
            if self.config.hard_cell_loss_weight > 0 and exact_pressure_cells.any():
                k = max(self.config.hard_cell_min, int(num_cells * self.config.hard_cell_fraction))
                k = max(1, min(num_cells, k))
                hard_values = raw_recon.reshape(bsz * decode_num_boards, num_cells)
                hard_masks = exact_pressure_cells.reshape(bsz * decode_num_boards, num_cells)
                hard_board_losses = []
                for row_values, row_mask in zip(hard_values, hard_masks):
                    valid_count = int(row_mask.sum().item())
                    if valid_count == 0:
                        continue
                    row_k = min(k, valid_count)
                    hard_board_losses.append(row_values[row_mask].topk(row_k, dim=-1).values.mean())
                hard_cell_loss = torch.stack(hard_board_losses).mean()
                loss = (
                    self.config.hard_cell_loss_weight * hard_cell_loss
                    if loss is None
                    else loss + self.config.hard_cell_loss_weight * hard_cell_loss
                )

            if self.config.cell_margin_loss_weight > 0 and exact_pressure_cells.any():
                logits_float = reconstruction_logits.float()
                target_logits = logits_float.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
                target_one_hot = F.one_hot(targets, num_classes=self.config.cell_vocab_size).to(torch.bool)
                wrong_logits = logits_float.masked_fill(target_one_hot, float("-inf")).max(dim=-1).values
                margin_raw = F.relu(self.config.cell_margin - (target_logits - wrong_logits))
                k = max(self.config.hard_cell_min, int(num_cells * self.config.cell_margin_fraction))
                k = max(1, min(num_cells, k))
                margin_values = margin_raw.reshape(bsz * decode_num_boards, num_cells)
                margin_masks = exact_pressure_cells.reshape(bsz * decode_num_boards, num_cells)
                margin_board_losses = []
                for row_values, row_mask in zip(margin_values, margin_masks):
                    valid_count = int(row_mask.sum().item())
                    if valid_count == 0:
                        continue
                    row_k = min(k, valid_count)
                    margin_board_losses.append(row_values[row_mask].topk(row_k, dim=-1).values.mean())
                cell_margin_loss = torch.stack(margin_board_losses).mean()
                loss = (
                    self.config.cell_margin_loss_weight * cell_margin_loss
                    if loss is None
                    else loss + self.config.cell_margin_loss_weight * cell_margin_loss
                )

        if decode_board_masks is not None and self.config.inside_loss_weight > 0 and decode_visible_boards:
            raw_inside = F.binary_cross_entropy_with_logits(
                inside_logits,
                decode_board_masks.to(inside_logits.dtype),
                reduction="none",
            )
            inside_weights = decode_active_bool[:, :, None].to(raw_inside.dtype)
            if inside_weights.any():
                inside_loss = (raw_inside * inside_weights).sum() / inside_weights.sum().clamp_min(1.0) / num_cells
                loss = (
                    self.config.inside_loss_weight * inside_loss
                    if loss is None
                    else loss + self.config.inside_loss_weight * inside_loss
                )

        if decode_board_masks is not None and self.config.shape_loss_weight > 0:
            height_labels, width_labels = self._shape_labels(decode_board_masks, decode_board_active)
            if (height_labels != -100).any():
                height_loss = F.cross_entropy(
                    height_logits.reshape(-1, self.config.canvas_size),
                    height_labels.reshape(-1),
                    ignore_index=-100,
                )
                width_loss = F.cross_entropy(
                    width_logits.reshape(-1, self.config.canvas_size),
                    width_labels.reshape(-1),
                    ignore_index=-100,
                )
                shape_loss = 0.5 * (height_loss + width_loss)
                loss = (
                    self.config.shape_loss_weight * shape_loss
                    if loss is None
                    else loss + self.config.shape_loss_weight * shape_loss
                )

        if (
            decode_board_features is not None
            and feature_logits is not None
            and self.config.grid_feature_loss_weight > 0
            and decode_board_masks is not None
            and decode_visible_boards
        ):
            feature_losses = []
            feature_active = decode_active_bool[:, :, None] & decode_board_masks.to(torch.bool)
            for idx, logits in enumerate(feature_logits):
                feature_targets = decode_board_features[..., idx]
                valid = feature_active & (feature_targets != GRID_FEATURE_IGNORE_INDEX)
                if not valid.any():
                    continue
                raw_feature = F.cross_entropy(
                    logits.reshape(-1, logits.shape[-1]),
                    feature_targets.clamp(0, logits.shape[-1] - 1).reshape(-1),
                    reduction="none",
                ).reshape(bsz, decode_num_boards, num_cells)
                feature_losses.append(raw_feature[valid].mean())
            if feature_losses:
                feature_loss = torch.stack(feature_losses).mean()
                loss = (
                    self.config.grid_feature_loss_weight * feature_loss
                    if loss is None
                    else loss + self.config.grid_feature_loss_weight * feature_loss
                )

        if (
            board_masks is not None
            and not has_separate_decode_boards
            and self.config.board_structure_loss_weight > 0
            and board_symmetry_logits is not None
            and board_color_presence_logits is not None
            and board_nonzero_count_logits is not None
            and board_color_count_logits is not None
            and board_local_signature_logits is not None
            and board_topology_logits is not None
        ):
            if context_active.any():
                (
                    symmetry_targets,
                    color_targets,
                    count_targets,
                    color_count_targets,
                    local_signature_targets,
                    topology_targets,
                ) = self._board_structure_labels(
                    board_ids,
                    board_masks,
                    context_active,
                )
                symmetry_loss = F.binary_cross_entropy_with_logits(
                    board_symmetry_logits[context_active],
                    symmetry_targets.to(board_symmetry_logits.dtype)[context_active],
                )
                color_loss = F.binary_cross_entropy_with_logits(
                    board_color_presence_logits[context_active],
                    color_targets.to(board_color_presence_logits.dtype)[context_active],
                )
                count_loss = F.cross_entropy(
                    board_nonzero_count_logits[context_active],
                    count_targets[context_active],
                )
                color_count_loss = F.cross_entropy(
                    board_color_count_logits[context_active].reshape(-1, 8),
                    color_count_targets[context_active].reshape(-1),
                )
                local_signature_loss = F.cross_entropy(
                    board_local_signature_logits[context_active].reshape(-1, 8),
                    local_signature_targets[context_active].reshape(-1),
                )
                topology_loss = F.cross_entropy(
                    board_topology_logits[context_active].reshape(-1, 8),
                    topology_targets[context_active].reshape(-1),
                )
                board_structure_loss = torch.stack(
                    [
                        symmetry_loss,
                        color_loss,
                        count_loss,
                        color_count_loss,
                        local_signature_loss,
                        topology_loss,
                    ]
                ).mean()
                loss = (
                    self.config.board_structure_loss_weight * board_structure_loss
                    if loss is None
                    else loss + self.config.board_structure_loss_weight * board_structure_loss
                )

        if (
            board_masks is not None
            and not has_separate_decode_boards
            and self.config.pair_diff_loss_weight > 0
            and pair_diff_logits is not None
            and pair_same_shape_logits is not None
            and pair_diff_count_logits is not None
            and pair_color_delta_logits is not None
            and pair_color_transition_logits is not None
        ):
            (
                pair_diff_targets,
                pair_valid,
                same_shape_targets,
                diff_count_targets,
                color_delta_targets,
                transition_targets,
            ) = self._pair_diff_labels(
                board_ids,
                board_masks,
                context_active,
            )
            pair_active = context_active[:, : pair_diff_logits.shape[1]] & context_active[
                :, pair_diff_logits.shape[1] : 2 * pair_diff_logits.shape[1]
            ]
            pair_losses = []
            if pair_valid.any():
                pos_weight = torch.tensor(
                    self.config.pair_diff_positive_weight,
                    dtype=pair_diff_logits.dtype,
                    device=pair_diff_logits.device,
                )
                diff_raw = F.binary_cross_entropy_with_logits(
                    pair_diff_logits,
                    pair_diff_targets.to(pair_diff_logits.dtype),
                    pos_weight=pos_weight,
                    reduction="none",
                )
                pair_losses.append(diff_raw[pair_valid].mean())
            if pair_active.any():
                same_shape_loss = F.binary_cross_entropy_with_logits(
                    pair_same_shape_logits[pair_active],
                    same_shape_targets.to(pair_same_shape_logits.dtype)[pair_active],
                )
                diff_count_loss = F.cross_entropy(
                    pair_diff_count_logits[pair_active],
                    diff_count_targets[pair_active],
                )
                color_delta_loss = F.cross_entropy(
                    pair_color_delta_logits[pair_active].reshape(-1, 7),
                    color_delta_targets[pair_active].reshape(-1),
                )
                transition_loss = F.binary_cross_entropy_with_logits(
                    pair_color_transition_logits[pair_active],
                    transition_targets.to(pair_color_transition_logits.dtype)[pair_active],
                )
                pair_losses.extend([same_shape_loss, diff_count_loss, color_delta_loss, transition_loss])
            if pair_losses:
                pair_diff_loss = torch.stack(pair_losses).mean()
                loss = (
                    self.config.pair_diff_loss_weight * pair_diff_loss
                    if loss is None
                    else loss + self.config.pair_diff_loss_weight * pair_diff_loss
                )

        if (
            jepa_target_indices is not None
            and self.config.jepa_loss_weight > 0
            and self.jepa_predictor is not None
            and self.jepa_summary_norm is not None
            and self.jepa_target_norm is not None
        ):
            target_indices = jepa_target_indices.to(board_ids.device).to(torch.long)
            jepa_mask, valid = self._jepa_context_mask(context_mask, context_active, target_indices, num_cells)
            if valid.any():
                jepa_summary = self._build_summary(context, jepa_mask)
                summary_pooled = self.jepa_summary_norm(jepa_summary.mean(dim=1))
                safe_indices = target_indices.clamp(0, num_boards - 1)
                target_board_states = self._board_mean_pool(cell_states, board_masks, context_active)
                target_states = target_board_states[
                    torch.arange(bsz, device=board_ids.device),
                    safe_indices,
                ]
                target_states = self.jepa_target_norm(target_states).detach()
                target_descriptor = (
                    self.decoder_role_embedding(board_roles[torch.arange(bsz, device=board_ids.device), safe_indices])
                    + self.decoder_slot_embedding(board_slots[torch.arange(bsz, device=board_ids.device), safe_indices])
                )
                jepa_pred = self.jepa_predictor(torch.cat([summary_pooled, target_descriptor], dim=-1))
                jepa_target = target_states
                pred_norm = F.normalize(jepa_pred.float(), dim=-1)
                target_norm = F.normalize(target_states.float(), dim=-1)
                cosine = (pred_norm * target_norm).sum(dim=-1)
                jepa_loss = (1.0 - cosine)[valid].mean()
                loss = (
                    self.config.jepa_loss_weight * jepa_loss
                    if loss is None
                    else loss + self.config.jepa_loss_weight * jepa_loss
                )
                if self.config.jepa_retrieval_loss_weight > 0:
                    target_pool = self.jepa_target_norm(target_board_states).detach()
                    target_pool = F.normalize(target_pool.float(), dim=-1)
                    retrieval_logits = torch.einsum("bd,bnd->bn", pred_norm, target_pool)
                    retrieval_logits = retrieval_logits / max(self.config.jepa_temperature, 1e-6)
                    retrieval_logits = retrieval_logits.masked_fill(~context_active, -1.0e4)
                    jepa_retrieval_logits = retrieval_logits
                    jepa_retrieval_loss = F.cross_entropy(retrieval_logits[valid], safe_indices[valid])
                    loss = (
                        self.config.jepa_retrieval_loss_weight * jepa_retrieval_loss
                        if loss is None
                        else loss + self.config.jepa_retrieval_loss_weight * jepa_retrieval_loss
                    )

        if not return_summary:
            summary = summary.detach()
        return ArcSummaryAutoencoderOutput(
            reconstruction_logits=reconstruction_logits,
            inside_logits=inside_logits,
            height_logits=height_logits,
            width_logits=width_logits,
            summary=summary,
            feature_logits=feature_logits,
            jepa_pred=jepa_pred,
            jepa_target=jepa_target,
            jepa_retrieval_logits=jepa_retrieval_logits,
            summary_code_indices=summary_code_indices,
            board_symmetry_logits=board_symmetry_logits,
            board_color_presence_logits=board_color_presence_logits,
            board_nonzero_count_logits=board_nonzero_count_logits,
            board_color_count_logits=board_color_count_logits,
            board_local_signature_logits=board_local_signature_logits,
            board_topology_logits=board_topology_logits,
            pair_diff_logits=pair_diff_logits,
            pair_same_shape_logits=pair_same_shape_logits,
            pair_diff_count_logits=pair_diff_count_logits,
            pair_color_delta_logits=pair_color_delta_logits,
            pair_color_transition_logits=pair_color_transition_logits,
            loss=loss,
            reconstruction_loss=reconstruction_loss,
            hard_cell_loss=hard_cell_loss,
            cell_margin_loss=cell_margin_loss,
            inside_loss=inside_loss,
            shape_loss=shape_loss,
            feature_loss=feature_loss,
            summary_codebook_loss=summary_codebook_loss,
            summary_commitment_loss=summary_commitment_loss,
            summary_code_entropy_loss=summary_code_entropy_loss,
            summary_code_perplexity=summary_code_perplexity,
            jepa_loss=jepa_loss,
            jepa_retrieval_loss=jepa_retrieval_loss,
            board_structure_loss=board_structure_loss,
            pair_diff_loss=pair_diff_loss,
            decoded_visible_boards=decode_visible_boards,
        )
