"""Small LoRA utilities for ARC-native PyTorch modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch
from torch import nn
import torch.nn.functional as F


@dataclass(frozen=True)
class LoRAStats:
    modules: int
    trainable_parameters: int
    total_parameters: int


@dataclass(frozen=True)
class ExtraTrainableStats:
    specs: tuple[str, ...]
    parameters: int
    tensors: int


class LoRALinear(nn.Module):
    """LoRA adapter around an existing Linear layer."""

    def __init__(
        self,
        base: nn.Linear,
        *,
        rank: int,
        alpha: float,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if rank <= 0:
            raise ValueError("LoRA rank must be positive")
        self.base = base
        self.rank = rank
        self.alpha = float(alpha)
        self.scaling = self.alpha / self.rank
        self.dropout = nn.Dropout(dropout)
        self.lora_a = nn.Parameter(
            torch.empty(rank, base.in_features, device=base.weight.device, dtype=base.weight.dtype)
        )
        self.lora_b = nn.Parameter(
            torch.zeros(base.out_features, rank, device=base.weight.device, dtype=base.weight.dtype)
        )
        nn.init.kaiming_uniform_(self.lora_a, a=5**0.5)
        for parameter in self.base.parameters():
            parameter.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.base(x)
        update = F.linear(F.linear(self.dropout(x), self.lora_a), self.lora_b)
        if self.scaling != 1.0:
            update = update.mul(self.scaling)
        return y.add_(update)

    def merged_linear(self) -> nn.Linear:
        merged = nn.Linear(
            self.base.in_features,
            self.base.out_features,
            bias=self.base.bias is not None,
            device=self.base.weight.device,
            dtype=self.base.weight.dtype,
        )
        merged.weight.data.copy_(self.base.weight.data)
        if self.base.bias is not None:
            merged.bias.data.copy_(self.base.bias.data)
        delta = torch.matmul(self.lora_b.data, self.lora_a.data).to(merged.weight.dtype)
        merged.weight.data.add_(delta, alpha=self.scaling)
        return merged


def _target_suffixes(value: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, str):
        parts = value.split(",")
    else:
        parts = list(value)
    suffixes = tuple(part.strip() for part in parts if part.strip())
    if not suffixes:
        raise ValueError("at least one LoRA target suffix is required")
    return suffixes


def apply_lora_to_model(
    model: nn.Module,
    *,
    rank: int,
    alpha: float,
    dropout: float,
    target_modules: str | Iterable[str],
) -> LoRAStats:
    """Freeze a model and replace selected Linear layers with LoRA adapters."""

    suffixes = _target_suffixes(target_modules)
    match_all_linear = any(suffix.lower() in {"*", "all", "all-linear", "all_linear"} for suffix in suffixes)
    for parameter in model.parameters():
        parameter.requires_grad = False

    replaced = 0
    for module_name, module in list(model.named_modules()):
        for child_name, child in list(module.named_children()):
            if not isinstance(child, nn.Linear):
                continue
            full_name = f"{module_name}.{child_name}" if module_name else child_name
            if not match_all_linear and not any(full_name.endswith(suffix) for suffix in suffixes):
                continue
            setattr(
                module,
                child_name,
                LoRALinear(child, rank=rank, alpha=alpha, dropout=dropout),
            )
            replaced += 1

    if replaced == 0:
        raise ValueError(f"LoRA did not match any Linear modules; targets={suffixes}")
    return lora_stats(model, modules=replaced)


def mark_lora_extra_trainable(model: nn.Module, specs: str | Iterable[str]) -> ExtraTrainableStats:
    """Unfreeze cheap non-linear ARC scaffolding alongside LoRA adapters."""

    raw_specs = _target_suffixes(specs) if specs else ()
    expanded: set[str] = set()
    for spec in raw_specs:
        key = spec.strip().lower().replace("_", "-")
        if key in {"none", "off", "false", "0"}:
            continue
        if key in {"arc-scaffold", "scaffold", "nonlinear", "non-linear"}:
            expanded.update({"embeddings", "convs", "norms", "latents", "heads"})
        else:
            expanded.add(key)
    if not expanded:
        return ExtraTrainableStats(specs=(), parameters=lora_stats(model).trainable_parameters, tensors=0)

    touched: set[int] = set()

    def unfreeze_parameter(parameter: nn.Parameter) -> None:
        parameter.requires_grad = True
        touched.add(id(parameter))

    def unfreeze_module(module: nn.Module, *, recurse: bool = False) -> None:
        for parameter in module.parameters(recurse=recurse):
            unfreeze_parameter(parameter)

    norm_types = (nn.LayerNorm, nn.GroupNorm, nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d)
    conv_types = (nn.Conv1d, nn.Conv2d, nn.Conv3d)
    for module_name, module in model.named_modules():
        module_key = module_name.lower()
        if "embeddings" in expanded and isinstance(module, nn.Embedding):
            unfreeze_module(module)
        if "convs" in expanded and isinstance(module, conv_types):
            unfreeze_module(module)
        if "norms" in expanded and (isinstance(module, norm_types) or module.__class__.__name__.lower().endswith("norm")):
            unfreeze_module(module)
        if "heads" in expanded and (
            module_key.endswith("head")
            or ".head" in module_key
            or "feature_heads" in module_key
            or "board_recon" in module_key
            or "candidate_verifier" in module_key
            or "pair_consistency" in module_key
            or "jepa_predictor" in module_key
        ):
            unfreeze_module(module, recurse=True)

    if "latents" in expanded:
        latent_names = ("latent_queries", "rule_queries", "summary_tokens", "output_role")
        for name, parameter in model.named_parameters():
            if any(part in name for part in latent_names):
                unfreeze_parameter(parameter)

    trainable = lora_stats(model).trainable_parameters
    return ExtraTrainableStats(specs=tuple(sorted(expanded)), parameters=trainable, tensors=len(touched))


def merge_lora_weights(model: nn.Module) -> int:
    """Merge all LoRA adapters into base Linear weights in-place."""

    merged = 0
    for module in model.modules():
        for child_name, child in list(module.named_children()):
            if isinstance(child, LoRALinear):
                setattr(module, child_name, child.merged_linear())
                merged += 1
    return merged


def lora_stats(model: nn.Module, *, modules: int | None = None) -> LoRAStats:
    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    if modules is None:
        modules = sum(1 for module in model.modules() if isinstance(module, LoRALinear))
    return LoRAStats(modules=modules, trainable_parameters=trainable, total_parameters=total)


__all__ = [
    "ExtraTrainableStats",
    "LoRALinear",
    "LoRAStats",
    "apply_lora_to_model",
    "lora_stats",
    "mark_lora_extra_trainable",
    "merge_lora_weights",
]
