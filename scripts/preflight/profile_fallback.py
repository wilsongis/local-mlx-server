"""Profile fallback logic for preflight validation.

This module implements the deterministic profile fallback chain
for selecting quantization profiles.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def determine_fallback_profile(model_path: str) -> str:
    """Determine quantization profile using fallback chain.

    Fallback chain (highest to lowest priority):
        1. Explicit profile (user-specified) - handled by caller
        2. Model-detected profile (from model_detector.py)
        3. Memory-based selection (48GB+ → TurboQuant, 64GB+ → standard)
        4. Safe default: "120b-balanced"

    Args:
        model_path: Path to model directory

    Returns:
        Profile name to use
    """
    # Step 2: Model-detected profile
    detected_profile = _detect_model_profile(model_path)
    if detected_profile:
        logger.info(f"Using model-detected profile: {detected_profile}")
        return detected_profile

    # Step 3: Memory-based selection
    memory_profile = _get_memory_based_profile()
    if memory_profile:
        logger.info(f"Using memory-based profile: {memory_profile}")
        return memory_profile

    # Step 4: Safe default
    default_profile = "120b-balanced"
    logger.info(f"Using safe default profile: {default_profile}")
    return default_profile


def determine_fallback_quantization(model_path: str) -> str:
    """Determine fallback quantization type.

    Args:
        model_path: Path to model directory

    Returns:
        Quantization string (e.g., "4bit-standard", "turboquant")
    """
    profile = determine_fallback_profile(model_path)

    # Map profile to quantization type
    if "tq" in profile.lower() or "turbo" in profile.lower():
        return "turboquant"
    else:
        return "4bit-standard"


def _detect_model_profile(model_path: str) -> Optional[str]:
    """Detect optimal profile from model architecture.

    Args:
        model_path: Path to model directory

    Returns:
        Profile name if detected, None otherwise
    """
    try:
        # Try to use existing model_detector if available
        from scripts.quantization.model_detector import ModelDetector

        detector = ModelDetector(model_path)
        arch = detector.detect()

        if arch and hasattr(arch, "size_class"):
            size_class = arch.size_class

            # Map size class to profile
            if size_class == "100B+":
                # Check memory to decide between TurboQuant and standard
                import psutil

                memory_gb = psutil.virtual_memory().total / (1024**3)
                if memory_gb >= 48:
                    return "tq3a-tq2e-g32"  # TurboQuant hybrid
                else:
                    return "4bit-standard"
            elif size_class == "70B":
                return "70b-balanced"
            elif size_class == "20B":
                return "20b-fast"

    except ImportError:
        logger.warning("Model detector not available")
    except Exception as e:
        logger.warning(f"Model detection failed: {e}")

    return None


def _get_memory_based_profile() -> Optional[str]:
    """Select profile based on available memory.

    Returns:
        Profile name if memory is sufficient, None otherwise
    """
    try:
        import psutil

        memory_gb = psutil.virtual_memory().total / (1024**3)

        if memory_gb >= 64:
            return "4bit-standard"  # Standard 4-bit for 120B+
        elif memory_gb >= 48:
            return "tq3a-tq2e-g32"  # TurboQuant hybrid for 120B+
        else:
            return None  # Insufficient memory

    except ImportError:
        logger.warning("psutil not available for memory check")
        return None
