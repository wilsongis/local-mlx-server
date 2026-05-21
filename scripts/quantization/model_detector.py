"""
Model architecture detector for identifying model types and layer structures.

Detects latent-MoE architectures, expert layers, and extracts model metadata
for per-path quantization configuration.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


class ModelDetectionError(Exception):
    """Raised when model architecture detection fails."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"[{error_code}] {message}")


@dataclass
class ModelArchitecture:
    """Represents detected model architecture with layer type information."""

    architecture_name: str
    total_params: int = 0
    active_params: int = 0
    layer_types: List[str] = field(default_factory=list)
    expert_count: int = 0
    is_moe: bool = False
    detected_expert_layers: List[str] = field(default_factory=list)
    detected_attention_layers: List[str] = field(default_factory=list)

    # Layer pattern matching
    EXPERT_PATTERNS = [".*expert.*", ".*router.*", ".*moe.*", ".*switch.*"]
    ATTENTION_PATTERNS = [
        ".*attention.*",
        ".*self_attn.*",
        ".*q_proj.*",
        ".*k_proj.*",
        ".*v_proj.*",
    ]

    def detect_layer_types(self) -> None:
        """Detect and categorize layer types from layer_types list."""
        self.detected_expert_layers = []
        self.detected_attention_layers = []

        for layer_name in self.layer_types:
            # Check if it's an expert layer
            if any(
                re.match(pattern, layer_name, re.IGNORECASE)
                for pattern in self.EXPERT_PATTERNS
            ):
                self.detected_expert_layers.append(layer_name)

            # Check if it's an attention layer
            if any(
                re.match(pattern, layer_name, re.IGNORECASE)
                for pattern in self.ATTENTION_PATTERNS
            ):
                self.detected_attention_layers.append(layer_name)

        # Update MoE status based on expert detection
        self.is_moe = self.expert_count > 0 or len(self.detected_expert_layers) > 0


class ModelDetector:
    """Detects model architecture from model path or name."""

    # Nemotron model patterns
    NEMOTRON_PATTERNS = [
        r".*nemotron.*120b.*",
        r".*nemotron.*3.*super.*120b.*",
        r".*120b.*moe.*",
    ]

    def __init__(self, model_path: str):
        """
        Initialize detector with model path.

        Args:
            model_path: Path to the model directory or model name
        """
        self.model_path = model_path
        self.model_name = os.path.basename(model_path.rstrip("/"))

    def detect(self) -> ModelArchitecture:
        """
        Detect model architecture.

        Returns:
            ModelArchitecture instance with detected properties

        Raises:
            ModelDetectionError: If detection fails
        """
        architecture = ModelArchitecture(architecture_name=self.model_name)

        # Try to load model config
        config = self._load_model_config()

        if config:
            # Extract architecture info from config
            architecture = self._extract_from_config(architecture, config)

        # Apply pattern matching on model name
        architecture = self._apply_pattern_matching(architecture)

        # Detect layer types if we have config
        if config and "model_type" in config:
            architecture.layer_types = self._get_layer_types_from_config(config)
            architecture.detect_layer_types()

        return architecture

    def _load_model_config(self) -> Optional[dict]:
        """Load model configuration from config.json or similar files."""
        config_files = [
            "config.json",
            "model_config.json",
            "config.yaml",
        ]

        for config_file in config_files:
            config_path = os.path.join(self.model_path, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        if config_file.endswith(".yaml"):
                            import yaml

                            return yaml.safe_load(f)
                        else:
                            return json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")

        return None

    def _extract_from_config(
        self, architecture: ModelArchitecture, config: dict
    ) -> ModelArchitecture:
        """Extract architecture info from model config."""

        # Extract expert count
        if "num_experts" in config:
            architecture.expert_count = config["num_experts"]
        elif "n_experts" in config:
            architecture.expert_count = config["n_experts"]
        elif "num_local_experts" in config:
            architecture.expert_count = config["num_local_experts"]

        # Extract parameter counts if available
        if "num_parameters" in config:
            architecture.total_params = config["num_parameters"]
        elif "model_size" in config:
            # Parse model size string (e.g., "120B")
            size_str = config["model_size"]
            architecture.total_params = self._parse_model_size(size_str)

        # Calculate active params for MoE models
        if architecture.expert_count > 0:
            # For MoE models, active params is typically total / expert_count * active_experts
            # Assuming 2 active experts for Nemotron-style models
            active_experts = config.get("num_experts_per_tok", 2)
            if architecture.total_params > 0:
                architecture.active_params = int(
                    architecture.total_params
                    / architecture.expert_count
                    * active_experts
                )

        return architecture

    def _apply_pattern_matching(
        self, architecture: ModelArchitecture
    ) -> ModelArchitecture:
        """Apply regex patterns to model name for architecture detection."""

        model_name_lower = self.model_name.lower()

        # Check Nemotron patterns
        for pattern in self.NEMOTRON_PATTERNS:
            if re.match(pattern, model_name_lower, re.IGNORECASE):
                architecture.architecture_name = "Nemotron-3-Super-120B-A12B"
                architecture.is_moe = True
                if architecture.expert_count == 0:
                    architecture.expert_count = 8  # Default for Nemotron
                if architecture.total_params == 0:
                    architecture.total_params = 120_000_000_000
                if architecture.active_params == 0:
                    architecture.active_params = 12_000_000_000
                break

        return architecture

    def _get_layer_types_from_config(self, config: dict) -> List[str]:
        """Extract layer type names from model config."""

        layer_types = []

        # Try to get architecture details
        if "architectures" in config:
            arch = config["architectures"][0] if config["architectures"] else None
            if arch:
                layer_types.append(arch)

        # Add common layer types based on model type
        model_type = config.get("model_type", "")

        if "llama" in model_type.lower():
            layer_types.extend(
                [
                    "attention.q_proj",
                    "attention.k_proj",
                    "attention.v_proj",
                    "attention.o_proj",
                    "mlp.gate_proj",
                    "mlp.up_proj",
                    "mlp.down_proj",
                ]
            )
        elif "mixtral" in model_type.lower() or "moe" in model_type.lower():
            # MoE model
            layer_types.extend(
                [
                    "attention.q_proj",
                    "attention.k_proj",
                    "attention.v_proj",
                    "attention.o_proj",
                    "block_sparse_moe.gate",
                    "block_sparse_moe.experts",
                ]
            )

        return layer_types

    def _parse_model_size(self, size_str: str) -> int:
        """Parse model size string to parameter count."""
        size_str = size_str.strip().upper()

        if size_str.endswith("B"):
            try:
                return int(float(size_str[:-1]) * 1_000_000_000)
            except ValueError:
                pass
        elif size_str.endswith("M"):
            try:
                return int(float(size_str[:-1]) * 1_000_000)
            except ValueError:
                pass

        return 0

    @staticmethod
    def detect_from_model_name(model_name: str) -> ModelArchitecture:
        """
        Static method to detect architecture from model name only.

        Args:
            model_name: Model name or path

        Returns:
            ModelArchitecture with basic detection
        """
        detector = ModelDetector(model_name)
        return detector.detect()

    # Additional Nemotron and MoE model patterns for Spec 007
    NEMOTRON_3_SUPER_PATTERNS = [
        r".*nemotron.*3.*super.*120b.*",
        r".*nemotron.*3.*super.*a12b.*",
        r".*120b.*a12b.*",
    ]
    
    def detect_nemotron_3_super(self, model_name: str) -> bool:
        """Detect Nemotron-3-Super-120B-A12B model variants."""
        model_name_lower = model_name.lower()
        for pattern in self.NEMOTRON_3_SUPER_PATTERNS:
            if re.match(pattern, model_name_lower, re.IGNORECASE):
                return True
        return False
    
    def extract_expert_count(self, config: dict) -> int:
        """Extract expert count from model config (T022)."""
        # Common field names for expert count
        expert_fields = [
            "num_experts", "n_experts", "num_local_experts",
            "expert_count", "num_experts_per_layer"
        ]
        
        for expert_field in expert_fields:
            if expert_field in config:
                return int(config[expert_field])
        
        # Check for MoE model type
        model_type = config.get("model_type", "").lower()
        if "moe" in model_type or "mixtral" in model_type:
            # Default expert counts for known architectures
            if "mixtral" in model_type:
                return 8
            elif "nemotron" in model_type:
                return 12  # Nemotron-3-Super-120B-A12B
        
        return 0
    
    def identify_expert_layers(self, layer_names: list) -> list:
        """Identify expert layers from layer names (T021)."""
        expert_layers = []
        
        for layer_name in layer_names:
            # Check for expert layer patterns
            if any(re.match(pattern, layer_name, re.IGNORECASE) 
                   for pattern in self.EXPERT_PATTERNS):
                expert_layers.append(layer_name)
        
        return expert_layers
    
    def calculate_active_params(self, total_params: int, expert_count: int, 
                                active_experts: int = 2) -> int:
        """Calculate active parameters for MoE models (T023)."""
        if expert_count == 0:
            return total_params
        
        # For MoE models, active params = total / expert_count * active_experts
        return int(total_params / expert_count * active_experts)
