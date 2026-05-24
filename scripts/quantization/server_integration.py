"""Server integration for KV cache compression.

This module provides patches and utilities to integrate KV cache compression
with mlx_lm.server at runtime.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def patch_mlx_server_for_kv_compression(
    kv_cache_manager,
    model_provider=None,
):
    """Patch mlx_lm.server to apply KV cache compression after prompt processing.

    This function patches the server's prompt cache creation to automatically
    convert caches to TurboQuantKVCache when compression is enabled.

    Args:
        kv_cache_manager: KVCacheCompressionManager instance
        model_provider: Optional model provider to patch (for testing)

    Returns:
        True if patch was applied successfully, False otherwise
    """
    if not kv_cache_manager or not kv_cache_manager.enabled:
        logger.info("KV cache compression not enabled, skipping server patch")
        return False

    try:
        from mlx_lm.models.cache import make_prompt_cache as _original_make_prompt_cache

        # Store original function
        _original_make_prompt_cache_func = _original_make_prompt_cache

        def _patched_make_prompt_cache(model, *args, **kwargs):
            """Patched version that applies KV cache compression."""
            # Create the original prompt cache
            cache = _original_make_prompt_cache_func(model, *args, **kwargs)

            # Apply KV cache compression if enabled
            if kv_cache_manager.enabled and kv_cache_manager.current_profile:
                try:
                    logger.info("Applying KV cache compression to prompt cache...")
                    compressed_cache = kv_cache_manager.convert_cache_to_turboquant(
                        cache, kv_cache_manager.current_profile
                    )
                    return compressed_cache
                except Exception as e:
                    logger.error(f"Failed to apply KV cache compression: {e}")
                    if kv_cache_manager.fallback_on_error:
                        logger.warning("Falling back to uncompressed cache")
                        return cache
                    raise

            return cache

        # Apply the patch to mlx_lm.models.cache
        import mlx_lm.models.cache

        mlx_lm.models.cache.make_prompt_cache = _patched_make_prompt_cache

        # Patch any local references in mlx_lm.server module
        # (in case it imported make_prompt_cache locally)
        try:
            import mlx_lm.server as server_mod

            if hasattr(server_mod, "make_prompt_cache"):
                server_mod.make_prompt_cache = _patched_make_prompt_cache
        except Exception:
            pass  # Non-critical if this fails

        logger.info("Successfully patched mlx_lm.server for KV cache compression")
        return True

    except ImportError as e:
        logger.error(f"Failed to patch mlx_lm.server: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error patching server: {e}")
        return False


def apply_kv_compression_to_cache(
    prompt_cache: list,
    kv_cache_manager,
    model_size_class: Optional[str] = None,
    weight_bits: Optional[int] = None,
) -> list:
    """Apply KV cache compression to a prompt cache.

    This is a convenience function that can be called manually if needed.

    Args:
        prompt_cache: List of (key_cache, value_cache) tuples per layer
        kv_cache_manager: KVCacheCompressionManager instance
        model_size_class: Optional model size class for auto profile selection
        weight_bits: Optional weight bits for auto profile selection

    Returns:
        Compressed cache list, or original if compression disabled/failed
    """
    if not kv_cache_manager or not kv_cache_manager.enabled:
        return prompt_cache

    # Select profile if not already selected
    if not kv_cache_manager.current_profile:
        profile = kv_cache_manager.select_profile(
            model_size_class or "20B",
            weight_bits,
        )
        if profile:
            kv_cache_manager.current_profile = profile

    if not kv_cache_manager.current_profile:
        return prompt_cache

    return kv_cache_manager.convert_cache_to_turboquant(
        prompt_cache, kv_cache_manager.current_profile
    )
