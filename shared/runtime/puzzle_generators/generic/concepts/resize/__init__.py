"""Resize family: basic upscale / downscale / non-uniform scale at VARIOUS
integer ratios. Closes the grow/shrink size-relation space the distribution
audit shows we under-cover (eval grow=3%/mixed=4% vs ours ~2%/1%), and each
generator parameterizes the ratio so one module spans many ratios. Reuses the
extraction family's RacketBridge parity harness."""
from puzzle_generators.generic.concepts.extraction import parity_check  # re-export

__all__ = ["parity_check"]
