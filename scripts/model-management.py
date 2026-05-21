"""
Model Management Module for Local MLX Server.

Provides model profile registry, validation, and state management for
selecting and activating large language model profiles on Apple Silicon.
"""

import argparse
import fcntl
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psutil
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
PROFILES_PATH = Path(__file__).parent / "wrapper-config" / "profiles.yaml"
STATE_FILE = Path(__file__).parent.parent / ".active-model"


@dataclass
class ModelProfile:
    """Represents a configured large language model with quantization settings."""

    name: str
    model_path: str
    description: Optional[str] = None
    memory_estimate_gb: Optional[float] = None
    quantization: Optional[dict] = field(default_factory=dict)
    kv_cache: Optional[dict] = field(default_factory=dict)
    inference_args: Optional[dict] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Outcome of validating a model profile against filesystem and system constraints."""

    profile_name: str
    is_valid: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    path_exists: bool = False
    key_files_present: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    disk_space_gb_available: float = 0.0
    disk_space_gb_required: float = 0.0
    validation_timestamp: str = ""


class ModelRegistry:
    """Collection of all configured model profiles with lookup and state management."""

    def __init__(self, profiles_path: Path = PROFILES_PATH):
        """Initialize registry by reading profiles from YAML configuration."""
        self.profiles_path = profiles_path
        self.profiles: list[ModelProfile] = []
        self._load_profiles()

    def _load_profiles(self):
        """Load model profiles from the YAML configuration file."""
        try:
            if not self.profiles_path.exists():
                logger.error(f"Profiles file not found: {self.profiles_path}")
                return

            with open(self.profiles_path, "r") as f:
                data = yaml.safe_load(f)

            if not data or "profiles" not in data:
                logger.warning("No profiles found in configuration file")
                return

            for profile_data in data["profiles"]:
                profile = ModelProfile(
                    name=profile_data.get("name", ""),
                    model_path=profile_data.get("model_path", ""),
                    description=profile_data.get("description"),
                    memory_estimate_gb=profile_data.get("memory_estimate_gb"),
                    quantization=profile_data.get("quantization", {}),
                    kv_cache=profile_data.get("kv_cache", {}),
                    inference_args=profile_data.get("inference_args", {}),
                )
                self.profiles.append(profile)

            logger.info(f"Loaded {len(self.profiles)} model profiles")

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse profiles YAML: {e}")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")

    def list_profiles(self) -> list[ModelProfile]:
        """Return all configured model profiles."""
        return self.profiles

    def get_profile(self, name: str) -> Optional[ModelProfile]:
        """Lookup a model profile by name."""
        for profile in self.profiles:
            if profile.name == name:
                return profile
        return None

    def validate_profile_exists(self, name: str) -> bool:
        """Check if a profile name exists in the registry."""
        return self.get_profile(name) is not None

    def validate_model_path(self, profile: ModelProfile) -> tuple[bool, str]:
        """Check if model_path exists and expand ~. Returns (exists, expanded_path)."""
        expanded_path = Path(profile.model_path).expanduser()
        exists = expanded_path.exists()
        return exists, str(expanded_path)

    def check_key_files(self, profile: ModelProfile) -> tuple[list[str], list[str]]:
        """Verify config.json and weight files exist. Returns (present, missing)."""
        expanded_path = Path(profile.model_path).expanduser()
        key_files = ["config.json"]
        present = []
        missing = []

        # Check for weight files
        if expanded_path.exists():
            weight_files = (
                list(expanded_path.glob("*.safetensors"))
                + list(expanded_path.glob("*.npz"))
                + list(expanded_path.glob("*.bin"))
            )
            if weight_files:
                key_files.extend([f.name for f in weight_files[:5]])  # Limit to first 5

        for file in key_files:
            file_path = expanded_path / file if not file.startswith("*.") else None
            if file_path and file_path.exists():
                present.append(file)
            else:
                missing.append(file)

        return present, missing

    def check_disk_space(self, profile: ModelProfile) -> tuple[float, float]:
        """Check available disk space vs required. Returns (available_gb, required_gb)."""
        expanded_path = Path(profile.model_path).expanduser()
        required = profile.memory_estimate_gb or 0.0

        try:
            # Get the disk where the model path resides
            if expanded_path.exists():
                disk_path = expanded_path
            else:
                # Check parent directories until we find an existing one
                disk_path = expanded_path
                while not disk_path.exists() and disk_path != disk_path.parent:
                    disk_path = disk_path.parent

            usage = psutil.disk_usage(str(disk_path))
            available_gb = usage.free / (1024**3)
            return available_gb, required
        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return 0.0, required

    def validate_profile(self, name: str) -> ValidationResult:
        """Run all validation checks and return ValidationResult."""
        result = ValidationResult(
            profile_name=name,
            validation_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Check if profile exists
        profile = self.get_profile(name)
        if not profile:
            result.errors.append(f"Profile '{name}' not found in registry")
            result.is_valid = False
            return result

        # Validate model path
        path_exists, expanded_path = self.validate_model_path(profile)
        result.path_exists = path_exists
        if not path_exists:
            result.errors.append(f"Model path does not exist: {expanded_path}")
            result.is_valid = False
            return result

        # Check key files
        present, missing = self.check_key_files(profile)
        result.key_files_present = present
        result.missing_files = missing
        if missing:
            result.warnings.append(f"Missing key files: {', '.join(missing)}")

        # Check disk space
        available, required = self.check_disk_space(profile)
        result.disk_space_gb_available = available
        result.disk_space_gb_required = required

        if available < required:
            if available < 1.0:
                result.errors.append(
                    f"Critical: Only {available:.1f} GB available, {required:.1f} GB required"
                )
                result.is_valid = False
            else:
                result.warnings.append(
                    f"Low disk space: {available:.1f} GB available, {required:.1f} GB required"
                )

        # Set final validity
        if not result.errors:
            result.is_valid = True

        return result


def get_active_profile() -> Optional[str]:
    """Read the currently active profile from state file."""
    try:
        if not STATE_FILE.exists():
            return None
        with open(STATE_FILE, "r") as f:
            profile_name = f.read().strip()
            return profile_name if profile_name else None
    except Exception as e:
        logger.error(f"Failed to read active profile: {e}")
        return None


def set_active_profile(name: str) -> bool:
    """Write the active profile name to state file with flock locking."""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(f"{name}\n")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        logger.info(f"Active profile set to: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to set active profile: {e}")
        return False


def format_validation_output(result: ValidationResult, verbose: bool = True) -> str:
    """Format validation result for human-readable output."""
    lines = []
    lines.append(f"Validation for profile: {result.profile_name}")
    lines.append("─" * 50)

    # Path check
    if result.path_exists:
        lines.append("✓ Model path exists")
    else:
        lines.append("✗ Model path does not exist")

    # Key files
    if result.key_files_present:
        lines.append(f"✓ Key files present: {', '.join(result.key_files_present)}")
    if result.missing_files:
        lines.append(f"⚠ Missing files: {', '.join(result.missing_files)}")

    # Disk space
    if result.disk_space_gb_available > 0:
        lines.append(
            f"{'✓' if result.disk_space_gb_available >= result.disk_space_gb_required else '⚠'} "
            f"Disk space: {result.disk_space_gb_available:.1f} GB available, "
            f"{result.disk_space_gb_required:.1f} GB required"
        )

    # Errors and warnings
    if result.errors:
        lines.append("\nErrors:")
        for error in result.errors:
            lines.append(f"  ✗ {error}")

    if result.warnings:
        lines.append("\nWarnings:")
        for warning in result.warnings:
            lines.append(f"  ⚠ {warning}")

    lines.append("─" * 50)
    lines.append(f"Validation: {'PASSED' if result.is_valid else 'FAILED'}")

    return "\n".join(lines)


def list_models_cli(json_output: bool = False):
    """List all available model profiles with formatted output."""
    registry = ModelRegistry()
    active_profile = get_active_profile()

    if json_output:
        output = {
            "profiles": [],
            "active_profile": active_profile,
            "total_count": len(registry.profiles),
        }
        for profile in registry.profiles:
            output["profiles"].append(
                {
                    "name": profile.name,
                    "model_path": profile.model_path,
                    "memory_estimate_gb": profile.memory_estimate_gb,
                    "description": profile.description,
                    "is_active": profile.name == active_profile,
                }
            )
        print(json.dumps(output, indent=2))
    else:
        print("Available Model Profiles:")
        print("─" * 50)
        for profile in registry.profiles:
            status = "Active" if profile.name == active_profile else "Inactive"
            print(f"Name: {profile.name}")
            print(f"Path: {profile.model_path}")
            if profile.memory_estimate_gb:
                print(f"Memory: {profile.memory_estimate_gb} GB")
            if profile.description:
                print(f"Description: {profile.description}")
            print(f"Status: {status}")
            print()
        print(f"Total: {len(registry.profiles)} profiles")
        print(f"Active: {active_profile or 'None'}")


def activate_model_cli(profile_name: str, validate: bool = True, force: bool = False):
    """Activate a model profile with optional validation."""
    registry = ModelRegistry()

    # Check if profile exists
    if not registry.validate_profile_exists(profile_name):
        print(f"✗ Profile not found: {profile_name}")
        print("\nAvailable profiles:")
        for p in registry.list_profiles():
            print(f"  - {p.name}")
        print("\nUse 'just models-list' to see all available profiles.")
        return False

    # Run validation unless force is used
    if validate and not force:
        print(f"Activating model profile: {profile_name}")
        result = registry.validate_profile(profile_name)
        print(format_validation_output(result))

        if not result.is_valid:
            print("\n✗ Validation failed. Use --force to activate anyway.")
            return False
    elif force:
        print(f"Force activating model profile: {profile_name}")

    # Set active profile
    if set_active_profile(profile_name):
        print("✓ Profile activated successfully")
        if result.warnings if validate and not force else False:
            print("(with warnings)")
        print(f"\nActive model: {profile_name}")
        return True
    else:
        print(f"✗ Failed to activate profile: {profile_name}")
        return False


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Model Management for Local MLX Server"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available model profiles")
    list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # Use command
    use_parser = subparsers.add_parser("use", help="Activate a model profile")
    use_parser.add_argument("profile", help="Profile name to activate")
    use_parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run validation before activation (default: true)",
    )
    use_parser.add_argument(
        "--force", action="store_true", help="Skip validation and force activation"
    )
    use_parser.add_argument(
        "--quant-profile",
        help="Quantization profile name or path (e.g., tq3a-tq2e-g32)",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show current active profile")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a model profile")
    validate_parser.add_argument("profile", help="Profile name to validate")

    args = parser.parse_args()

    if args.command == "list":
        list_models_cli(json_output=args.json)
    elif args.command == "use":
        activate_model_cli(args.profile, validate=args.validate, force=args.force, quant_profile=args.quant_profile if hasattr(args, 'quant_profile') else None)
    elif args.command == "status":
        active = get_active_profile()
        if active:
            registry = ModelRegistry()
            profile = registry.get_profile(active)
            print(f"Current Model Profile: {active}")
            if profile:
                print(f"Path: {profile.model_path}")
                if profile.memory_estimate_gb:
                    print(f"Memory: {profile.memory_estimate_gb} GB")
                if profile.description:
                    print(f"Description: {profile.description}")
        else:
            print("No model profile currently active.")
            print("\nUse 'just models-list' to see available profiles.")
            print("Use 'just model-use <profile>' to activate a profile.")
    elif args.command == "validate":
        registry = ModelRegistry()
        result = registry.validate_profile(args.profile)
        print(format_validation_output(result))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
