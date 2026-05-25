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
    # Get model path from command line args or environment
    import sys
    model_path = os.environ.get("MODEL_PATH", "")
    if len(sys.argv) > 1 and sys.argv[1] == "--model" and len(sys.argv) > 2:
        model_path = sys.argv[2]

    # Run preflight checks unless skipped
    skip_preflight = os.environ.get("SKIP_PREFLIGHT", "false").lower() == "true"
    if model_path and not skip_preflight:
        try:
            from scripts.preflight.checker import PreflightChecker
            print(f"[Preflight] Running preflight checks for model: {model_path}")
            checker = PreflightChecker(model_path)
            result = checker.run_all_checks()

            if checker.should_block_startup():
                print("=" * 60)
                print("STARTUP BLOCKED due to critical preflight failures!")
                print("=" * 60)
                for check in result.checks:
                    if check.status == "fail" and check.check_type == "critical":
                        print(f"  [CRITICAL] {check.name}: {check.details}")
                print("=" * 60)
                print("Fix the above issues before starting the server.")
                print("=" * 60)
                sys.exit(1)

            if checker.should_enter_degraded_mode():
                print("=" * 60)
                print("ENTERING DEGRADED MODE due to non-critical failures")
                print("=" * 60)
                # Get degraded config and set environment variables
                degraded_config = checker.get_degraded_config()
                if degraded_config:
                    print(f"Disabled features: {', '.join(degraded_config.disabled_features)}")
                    print(f"Fallback quantization: {degraded_config.fallback_quantization}")
                    # Set environment variables to disable features
                    if "turboquant" in degraded_config.disabled_features:
                        os.environ["TURBOQUANT_DISABLED"] = "true"
                    if "kv_cache_compression" in degraded_config.disabled_features:
                        os.environ["KV_CACHE_ENABLED"] = "false"
                print("Server will start with reduced capabilities")
                print("=" * 60)

        except Exception as e:
            print(f"[Preflight] Warning: Preflight checks failed to run: {e}")
            print("[Preflight] Proceeding with startup...")

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
