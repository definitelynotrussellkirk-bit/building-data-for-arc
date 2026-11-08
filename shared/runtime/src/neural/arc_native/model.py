"""Full-attention ARC-native transformer.

The dense stream uses one token per padded ARC cell. Position, role, and
episode-slot identity are added as embeddings rather than emitted as
separate sequence tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch import nn
import torch.nn.functional as F
import torch.utils.checkpoint as checkpoint_utils

from .config import ArcNativeConfig


@dataclass
class ArcNativeOutput:
    logits: torch.Tensor
    height_logits: torch.Tensor
    width_logits: torch.Tensor
    hidden_states: Optional[torch.Tensor] = None
    loss: Optional[torch.Tensor] = None
    cell_loss: Optional[torch.Tensor] = None
    shape_loss: Optional[torch.Tensor] = None


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        normed = x * torch.rsqrt(x.pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return normed * self.weight


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, config: ArcNativeConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.head_dim = config.head_dim
        self.qkv = nn.Linear(config.d_model, 3 * config.d_model, bias=config.use_bias)
        self.out = nn.Linear(config.d_model, config.d_model, bias=config.use_bias)
        self.dropout = config.attention_dropout

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        bsz, seq_len, dim = x.shape
        qkv = self.qkv(x)
        q, k, v = qkv.chunk(3, dim=-1)

        def reshape(t: torch.Tensor) -> torch.Tensor:
            return t.view(bsz, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        q, k, v = reshape(q), reshape(k), reshape(v)

        attn_mask = None
        if attention_mask is not None:
            attn_mask = attention_mask[:, None, None, :].to(torch.bool)

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
        if attention_mask is not None:
            y = y * attention_mask[:, :, None].to(y.dtype)
        return y


class FeedForward(nn.Module):
    def __init__(self, config: ArcNativeConfig) -> None:
        super().__init__()
        self.up = nn.Linear(config.d_model, config.mlp_hidden_dim, bias=config.use_bias)
        self.down = nn.Linear(config.mlp_hidden_dim, config.d_model, bias=config.use_bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(self.dropout(F.gelu(self.up(x), approximate="tanh")))


class TransformerBlock(nn.Module):
    def __init__(self, config: ArcNativeConfig) -> None:
        super().__init__()
        self.attn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.attn = MultiHeadSelfAttention(config)
        self.ffn_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.ffn = FeedForward(config)
        self.dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        x: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.attn_norm(x), attention_mask=attention_mask))
        x = x + self.dropout(self.ffn(self.ffn_norm(x)))
        if attention_mask is not None:
            x = x * attention_mask[:, :, None].to(x.dtype)
        return x


class ArcNativeModel(nn.Module):
    """Transformer over padded ARC cell tokens."""

    def __init__(self, config: ArcNativeConfig) -> None:
        super().__init__()
        _ = config.head_dim
        self.config = config

        self.color_embedding = nn.Embedding(config.cell_vocab_size, config.d_model)
        self.position_embedding = nn.Embedding(config.num_positions, config.d_model)
        self.role_embedding = nn.Embedding(config.role_vocab_size, config.d_model)
        self.slot_embedding = nn.Embedding(config.slot_vocab_size, config.d_model)
        self.candidate_embedding = nn.Embedding(config.candidate_vocab_size, config.d_model)
        self.input_norm = RMSNorm(config.d_model, config.layer_norm_eps)
        self.dropout = nn.Dropout(config.dropout)

        self.layers = nn.ModuleList([TransformerBlock(config) for _ in range(config.n_layers)])
        self.final_norm = RMSNorm(config.d_model, config.layer_norm_eps)

        self.cell_head = nn.Linear(config.d_model, config.num_arc_colors, bias=True)
        self.height_head = nn.Linear(config.d_model, config.canvas_size, bias=True)
        self.width_head = nn.Linear(config.d_model, config.canvas_size, bias=True)

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def embed(
        self,
        cell_ids: torch.Tensor,
        position_ids: torch.Tensor,
        role_ids: torch.Tensor,
        slot_ids: torch.Tensor,
        candidate_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        if candidate_ids is None:
            candidate_ids = torch.zeros_like(cell_ids)
        x = (
            self.color_embedding(cell_ids)
            + self.position_embedding(position_ids)
            + self.role_embedding(role_ids)
            + self.slot_embedding(slot_ids)
            + self.candidate_embedding(candidate_ids)
        )
        return self.dropout(self.input_norm(x))

    def forward(
        self,
        cell_ids: torch.Tensor,
        position_ids: torch.Tensor,
        role_ids: torch.Tensor,
        slot_ids: torch.Tensor,
        candidate_ids: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        pool_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        height_labels: Optional[torch.Tensor] = None,
        width_labels: Optional[torch.Tensor] = None,
        return_hidden_states: bool = False,
    ) -> ArcNativeOutput:
        x = self.embed(cell_ids, position_ids, role_ids, slot_ids, candidate_ids)
        if attention_mask is not None:
            x = x * attention_mask[:, :, None].to(x.dtype)

        for layer in self.layers:
            if self.config.gradient_checkpointing and self.training:
                x = checkpoint_utils.checkpoint(
                    layer,
                    x,
                    attention_mask,
                    use_reentrant=False,
                )
            else:
                x = layer(x, attention_mask=attention_mask)

        x = self.final_norm(x)
        logits = self.cell_head(x)

        if pool_mask is None:
            pool_mask = attention_mask
        if pool_mask is None:
            pooled = x.mean(dim=1)
        else:
            weights = pool_mask[:, :, None].to(x.dtype)
            denom = weights.sum(dim=1).clamp_min(1.0)
            pooled = (x * weights).sum(dim=1) / denom

        height_logits = self.height_head(pooled)
        width_logits = self.width_head(pooled)

        cell_loss = None
        shape_loss = None
        loss = None
        if labels is not None:
            cell_loss = F.cross_entropy(
                logits.view(-1, self.config.num_arc_colors),
                labels.view(-1),
                ignore_index=-100,
            )
            loss = cell_loss
        if height_labels is not None and width_labels is not None:
            shape_loss = (
                F.cross_entropy(height_logits, height_labels)
                + F.cross_entropy(width_logits, width_labels)
            ) * 0.5
            loss = shape_loss if loss is None else loss + shape_loss

        return ArcNativeOutput(
            logits=logits,
            height_logits=height_logits,
            width_logits=width_logits,
            hidden_states=x if return_hidden_states else None,
            loss=loss,
            cell_loss=cell_loss,
            shape_loss=shape_loss,
        )


def count_parameters(model: nn.Module, *, trainable_only: bool = False) -> int:
    params = model.parameters()
    if trainable_only:
        params = (p for p in params if p.requires_grad)
    return sum(p.numel() for p in params)
