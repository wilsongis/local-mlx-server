#!/usr/bin/env python3
"""Wrapper script to start mlx_lm.server with KV cache compression patch.

This script applies the KV cache compression patch before starting the server,
allowing TurboQuant KV cache compression to work with mlx_lm.server.
"""

import os
import sys

# Add the project root to Python path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def main():
    """Apply KV cache compression patch and start mlx_lm.server."""
    # Get KV cache config from environment variables
    kv_profile = os.environ.get("KV_CACHE_PROFILE", "auto")
    kv_bits = int(os.environ.get("KV_CACHE_BITS", "3"))
    kv_group_size = int(os.environ.get("KV_CACHE_GROUP_SIZE", "64"))
    kv_enabled = os.environ.get("KV_CACHE_ENABLED", "false").lower() == "true"

    if kv_enabled:
        try:
            from scripts.quantization.kv_cache_compression import (
                KVCacheCompressionManager,
            )
            from scripts.quantization.server_integration import (
                patch_mlx_server_for_kv_compression,
            )

            # Create KV cache manager
            config = {
                "enabled": True,
                "profile": kv_profile,
                "default_bits": kv_bits,
                "default_group_size": kv_group_size,
                "fallback_on_error": True,
            }
            kv_manager = KVCacheCompressionManager(config)

            # Select profile
            # Note: model_size_class and weight_bits would be determined from the model
            # For now, use defaults
            profile = kv_manager.select_profile("20B", None)
            if profile:
                kv_manager.current_profile = profile
                # Apply the patch
                patch_mlx_server_for_kv_compression(kv_manager)
                print(f"[KV Cache] Compression enabled: {kv_profile}, bits={kv_bits}")
            else:
                print(
                    "[KV Cache] Failed to select profile, running without compression"
                )

        except Exception as e:
            print(f"[KV Cache] Warning: Failed to apply KV cache patch: {e}")
            print("[KV Cache] Continuing without KV cache compression")

    # Now start mlx_lm.server
    from mlx_lm.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
