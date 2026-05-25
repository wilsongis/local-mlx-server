"""Preflight checker orchestrator for MLX server startup.

This module contains the core dataclasses and orchestrator for preflight checks
that run before starting the MLX server.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PreflightCheck:
    """Represents a single validation step in the preflight process.

    Attributes:
        name: Unique identifier for the check (e.g., "memory_budget", "wired_limit")
        check_type: Category - "critical" or "non_critical"
        status: Result - "pass", "fail", "warning", "skip"
        details: Human-readable description of the result
        timestamp: When the check was executed
        error_code: Optional error code if check failed (e.g., "ERR-MEM-001")
    """

    name: str
    check_type: str
    status: str
    details: str
    timestamp: datetime = field(default_factory=datetime.now)
    error_code: Optional[str] = None

    def __post_init__(self):
        """Validate fields after initialization."""
        if self.check_type not in ("critical", "non_critical"):
            raise ValueError(
                f"check_type must be 'critical' or 'non_critical', got '{self.check_type}'"
            )
        if self.status not in ("pass", "fail", "warning", "skip"):
            raise ValueError(
                f"status must be 'pass', 'fail', 'warning', or 'skip', got '{self.status}'"
            )


@dataclass
class PreflightResult:
    """Aggregated result of all preflight checks with the final decision.

    Attributes:
        checks: All individual check results
        overall_status: "ready", "degraded", "blocked"
        critical_failures: Names of failed critical checks
        non_critical_failures: Names of failed non-critical checks
        degraded_mode: Whether system should enter degraded mode
        block_startup: Whether startup should be blocked
        execution_time_ms: Total preflight execution time in milliseconds
    """

    checks: List[PreflightCheck]
    overall_status: str = "ready"
    critical_failures: List[str] = field(default_factory=list)
    non_critical_failures: List[str] = field(default_factory=list)
    degraded_mode: bool = False
    block_startup: bool = False
    execution_time_ms: int = 0

    def __post_init__(self):
        """Calculate derived fields based on check results."""
        self.critical_failures = [
            c.name
            for c in self.checks
            if c.check_type == "critical" and c.status == "fail"
        ]
        self.non_critical_failures = [
            c.name
            for c in self.checks
            if c.check_type == "non_critical" and c.status == "fail"
        ]

        # Decision logic
        if self.critical_failures:
            self.overall_status = "blocked"
            self.block_startup = True
        elif self.non_critical_failures:
            self.overall_status = "degraded"
            self.degraded_mode = True
        else:
            self.overall_status = "ready"


@dataclass
class DegradedModeConfig:
    """Configuration for operating in degraded mode with reduced capabilities.

    Attributes:
        enabled: Whether degraded mode is active
        disabled_features: Features to disable (e.g., "turboquant", "kv_cache_compression")
        fallback_quantization: Quantization to use (e.g., "4bit-standard")
        fallback_profile: Profile name to use in degraded mode
        warnings: User-facing warning messages
    """

    enabled: bool = False
    disabled_features: List[str] = field(default_factory=list)
    fallback_quantization: str = "4bit-standard"
    fallback_profile: str = "120b-balanced"
    warnings: List[str] = field(default_factory=list)


class PreflightChecker:
    """Orchestrates preflight checks before server startup.

    This class coordinates all preflight checks and makes the final decision
    about whether to proceed with server startup, enter degraded mode,
    or block startup entirely.
    """

    def __init__(self, model_path: str, config_path: Optional[str] = None):
        """Initialize preflight checker.

        Args:
            model_path: Path to the model directory
            config_path: Optional path to preflight-config.yaml
        """
        self.model_path = model_path
        self.config_path = config_path or "scripts/wrapper-config/preflight-config.yaml"
        self.config = self._load_config()
        self.checks: List[PreflightCheck] = []
        self.result: Optional[PreflightResult] = None
        self.degraded_config: Optional[DegradedModeConfig] = None

    def _load_config(self) -> dict:
        """Load preflight configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        import yaml

        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return self._default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "memory": {
                "critical_120b": 48,
                "standard_120b": 64,
                "warning_threshold": 56,
                "wired_limit": 12,
            },
            "disk": {"min_required": 50, "check_path": "."},
            "dependencies": {
                "mlx_lm_min_version": "0.19.0",
                "check_turboquant": True,
                "check_kv_cache": True,
            },
            "degraded_mode": {
                "disabled_features": [
                    "turboquant",
                    "kv_cache_compression",
                    "advanced_profiling",
                ],
                "fallback_quantization": "4bit-standard",
            },
        }

    def run_all_checks(self) -> PreflightResult:
        """Run all preflight checks and return aggregated result.

        Returns:
            PreflightResult with all check results and decision

        Raises:
            Exception: If checks cannot be executed
        """
        start_time = time.time()
        self.checks = []

        try:
            # Import check modules here to avoid circular imports
            from scripts.preflight.dependency_check import check_dependencies
            from scripts.preflight.disk_check import check_disk_space
            from scripts.preflight.memory_check import (
                check_memory_budget,
                check_wired_limit,
            )
            from scripts.preflight.profile_fallback import determine_fallback_profile

            # Run all checks
            self.checks.append(check_memory_budget(self.model_path))
            self.checks.append(check_wired_limit())
            self.checks.append(
                check_disk_space(self.config.get("disk", {}).get("check_path", "."))
            )
            self.checks.append(check_dependencies())

            # Determine fallback profile (non-critical, for degraded mode)
            try:
                fallback_profile = determine_fallback_profile(self.model_path)
                logger.info(f"Determined fallback profile: {fallback_profile}")
            except Exception as e:
                logger.warning(f"Could not determine fallback profile: {e}")

            # Check if selected profile is safe for this system
            self._check_profile_safety()

            # Create result
            self.result = PreflightResult(
                checks=self.checks,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

            # Log all check results
            self._log_results(self.result)

            return self.result

        except Exception as e:
            logger.error(f"Failed to run preflight checks: {e}")
            raise

    def _check_profile_safety(self) -> None:
        """Check if the selected/fallback profile is safe for current system.

        Adds a profile_safety check to self.checks if the profile is unsafe.
        An unsafe profile requires more memory than available.
        """
        try:
            import psutil

            from scripts.preflight.profile_fallback import determine_fallback_profile

            # Get available memory
            total_memory_gb = psutil.virtual_memory().total / (1024**3)

            # Get the fallback profile (safe default)
            fallback_profile = determine_fallback_profile(self.model_path)

            # Check if fallback profile is in presets and get its memory requirement
            from pathlib import Path

            import yaml

            presets_path = Path("scripts/wrapper-config/presets.yaml")
            if presets_path.exists():
                with open(presets_path, "r") as f:
                    presets_config = yaml.safe_load(f)
                    presets = presets_config.get("presets", [])

                    # Find the preset that matches our fallback profile
                    target_memory_gb = None
                    for preset in presets:
                        if preset.get("name") == fallback_profile:
                            target_memory_gb = preset.get("target_memory_gb", 0)
                            break

                    if target_memory_gb and total_memory_gb < target_memory_gb:
                        # Profile is unsafe - add a check failure
                        from datetime import datetime

                        from scripts.preflight.checker import PreflightCheck

                        unsafe_check = PreflightCheck(
                            name="profile_safety",
                            check_type="critical",
                            status="fail",
                            details=(
                                f"Selected profile '{fallback_profile}' requires {target_memory_gb}GB, "
                                f"but only {total_memory_gb:.1f}GB available. "
                                f"Action: Use 'just models-list' to see available profiles, or "
                                f"select '120b-extreme' for systems with ~45GB memory."
                            ),
                            timestamp=datetime.now(),
                            error_code="ERR-PROFILE-001",
                        )
                        self.checks.append(unsafe_check)
                        logger.warning(
                            f"Unsafe profile detected: {unsafe_check.details}"
                        )
        except ImportError:
            logger.warning("psutil not available for profile safety check")
        except Exception as e:
            logger.warning(f"Profile safety check failed: {e}")

    def should_block_startup(self) -> bool:
        """Check if startup should be blocked due to critical failures.

        Returns:
            True if startup should be blocked, False otherwise
        """
        if not self.result:
            return False
        return self.result.block_startup

    def should_enter_degraded_mode(self) -> bool:
        """Check if system should enter degraded mode.

        Returns:
            True if degraded mode should be activated, False otherwise
        """
        if not self.result:
            return False
        return self.result.degraded_mode

    def get_degraded_config(self) -> Optional[DegradedModeConfig]:
        """Get the degraded mode configuration if applicable.

        Returns:
            DegradedModeConfig if in degraded mode, None otherwise
        """
        if not self.result or not self.result.degraded_mode:
            return None

        if self.degraded_config:
            return self.degraded_config

        # Create degraded config based on failures
        disabled_features = self.config.get("degraded_mode", {}).get(
            "disabled_features",
            ["turboquant", "kv_cache_compression", "advanced_profiling"],
        )

        fallback_quant = self.config.get("degraded_mode", {}).get(
            "fallback_quantization", "4bit-standard"
        )

        self.degraded_config = DegradedModeConfig(
            enabled=True,
            disabled_features=disabled_features,
            fallback_quantization=fallback_quant,
            fallback_profile="120b-balanced",  # Safe default
            warnings=[
                f"Non-critical check failed: {name}"
                for name in self.result.non_critical_failures
            ],
        )

        return self.degraded_config

    def _log_results(self, result: PreflightResult) -> None:
        """Log all check results with timestamps.

        Args:
            result: The preflight check results to log
        """
        logger.info("=== Preflight Check Results ===")
        logger.info(f"Overall Status: {result.overall_status}")
        logger.info(f"Execution Time: {result.execution_time_ms}ms")

        for check in result.checks:
            status_symbol = "✓" if check.status == "pass" else "✗"
            log_level = logging.INFO if check.status == "pass" else logging.WARNING
            if check.status == "fail" and check.check_type == "critical":
                log_level = logging.ERROR

            msg = f"{status_symbol} [{check.check_type.upper()}] {check.name}: {check.status} - {check.details}"
            logger.log(log_level, msg)

        if result.critical_failures:
            logger.error(f"Critical failures: {', '.join(result.critical_failures)}")
        if result.non_critical_failures:
            logger.warning(
                f"Non-critical failures: {', '.join(result.non_critical_failures)}"
            )

        if result.degraded_mode:
            logger.warning("System entering DEGRADED MODE - reduced capabilities")
        elif result.block_startup:
            logger.error("Startup BLOCKED due to critical failures")
        else:
            logger.info("System READY for startup")

        # Save preflight status to file for GUI (T026, T027)
        self._save_preflight_status(result)

    def _save_preflight_status(self, result: PreflightResult) -> None:
        """Save preflight status to JSON file for GUI consumption."""
        import json
        from pathlib import Path

        status_file = Path("/tmp/mlx-preflight-status.json")
        try:
            status_data = {
                "overall_status": result.overall_status,
                "block_startup": result.block_startup,
                "degraded_mode": {
                    "active": result.degraded_mode,
                    "disabled_features": [],
                    "fallback_quantization": None,
                    "fallback_profile": None,
                },
                "checks": [
                    {
                        "name": c.name,
                        "check_type": c.check_type,
                        "status": c.status,
                        "details": c.details,
                        "error_code": c.error_code,
                    }
                    for c in result.checks
                ],
                "timestamp": datetime.now().isoformat(),
            }

            # Add degraded mode config if available
            if result.degraded_mode and self.degraded_config:
                status_data["degraded_mode"]["disabled_features"] = (
                    self.degraded_config.disabled_features
                )
                status_data["degraded_mode"]["fallback_quantization"] = (
                    self.degraded_config.fallback_quantization
                )
                status_data["degraded_mode"]["fallback_profile"] = (
                    self.degraded_config.fallback_profile
                )

            with open(status_file, "w") as f:
                json.dump(status_data, f, indent=2)
            logger.info(f"Saved preflight status to {status_file}")
        except Exception as e:
            logger.warning(f"Failed to save preflight status: {e}")
