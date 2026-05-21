#!/usr/bin/env python3
"""CLI helper for quantization just recipes."""

import sys

def quant_apply(model_path, profile_name):
    """Apply quantization profile to a model."""
    try:
        from quantization.quantization_manager import QuantizationManager
        from quantization.profile_validator import ProfileValidationError
        
        manager = QuantizationManager(model_path=model_path, profile_name=profile_name)
        manager.initialize()
        config = manager.apply_quantization()
        print("Quantization applied successfully")
        print(f"Config: {config}")
        return 0
    except ProfileValidationError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

def quant_validate(profile_name):
    """Validate a quantization profile."""
    try:
        from quantization.profile_validator import ProfileValidator
        from quantization.profile_validator import ProfileValidationError
        
        ProfileValidator.validate_preset_name(profile_name)
        print("Profile validation passed")
        return 0
    except ProfileValidationError as e:
        print(f"Validation failed: {e}")
        return 1
    except Exception as e:
        print(f"Profile not found: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["apply", "validate"])
    parser.add_argument("--model", help="Model path for apply")
    parser.add_argument("--profile", help="Profile name")
    
    args = parser.parse_args()
    
    if args.command == "apply":
        if not args.model or not args.profile:
            print("Usage: cli_helper.py apply --model <path> --profile <name>")
            sys.exit(1)
        sys.exit(quant_apply(args.model, args.profile))
    elif args.command == "validate":
        if not args.profile:
            print("Usage: cli_helper.py validate --profile <name>")
            sys.exit(1)
        sys.exit(quant_validate(args.profile))
