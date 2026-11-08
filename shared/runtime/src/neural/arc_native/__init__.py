"""ARC-native transformer model scaffold."""

from .config import ArcNativeConfig
from .model import ArcNativeModel, ArcNativeOutput, count_parameters
from .dataset import ArcNativeJsonlDataset, episode_row_to_tensors
from .bottleneck_dataset import ArcBottleneckJsonlDataset, bottleneck_row_to_tensors
from .bottleneck_model import ArcBottleneckConfig, ArcBottleneckModel, ArcBottleneckOutput
from .episode_dataset import (
    collate_episode_batch,
    make_holdout_task_filter,
    task_in_holdout,
)
from .episode_features import (
    EPISODE_FEATURE_NAMES,
    EPISODE_FEATURE_VOCAB_SIZES,
    add_episode_features_to_batch,
    episode_feature_channels,
)
from .episode_model import ArcEpisodeConfig, ArcEpisodeModel, ArcEpisodeOutput
from .summary_autoencoder import (
    ArcSummaryAutoencoderConfig,
    ArcSummaryAutoencoderModel,
    ArcSummaryAutoencoderOutput,
    pack_lodo_targets_from_bottleneck_batch,
    pack_query_output_targets_from_bottleneck_batch,
    pack_visible_boards_from_bottleneck_batch,
)
from .bottleneck_tensorize import (
    GRID_FEATURE_NAMES,
    GRID_FEATURE_VOCAB_SIZES,
    build_bottleneck_episode_tensors,
    collate_bottleneck_episode_tensors,
)
from .lora import LoRALinear, apply_lora_to_model, lora_stats, merge_lora_weights
from .tensorize import (
    ArcRoles,
    build_episode_tensors,
    collate_episode_tensors,
    pad_grid,
)

__all__ = [
    "ArcNativeConfig",
    "ArcNativeModel",
    "ArcNativeOutput",
    "ArcBottleneckConfig",
    "ArcBottleneckJsonlDataset",
    "ArcBottleneckModel",
    "ArcBottleneckOutput",
    "ArcEpisodeConfig",
    "ArcEpisodeModel",
    "ArcEpisodeOutput",
    "EPISODE_FEATURE_NAMES",
    "EPISODE_FEATURE_VOCAB_SIZES",
    "add_episode_features_to_batch",
    "collate_episode_batch",
    "episode_feature_channels",
    "make_holdout_task_filter",
    "task_in_holdout",
    "ArcSummaryAutoencoderConfig",
    "ArcSummaryAutoencoderModel",
    "ArcSummaryAutoencoderOutput",
    "ArcNativeJsonlDataset",
    "ArcRoles",
    "GRID_FEATURE_NAMES",
    "GRID_FEATURE_VOCAB_SIZES",
    "bottleneck_row_to_tensors",
    "build_bottleneck_episode_tensors",
    "build_episode_tensors",
    "collate_bottleneck_episode_tensors",
    "collate_episode_tensors",
    "count_parameters",
    "episode_row_to_tensors",
    "LoRALinear",
    "apply_lora_to_model",
    "lora_stats",
    "merge_lora_weights",
    "pad_grid",
    "pack_lodo_targets_from_bottleneck_batch",
    "pack_query_output_targets_from_bottleneck_batch",
    "pack_visible_boards_from_bottleneck_batch",
]
