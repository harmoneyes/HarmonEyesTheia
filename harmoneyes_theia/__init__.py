"""
HarmonEyes Theia SDK - Platform-agnostic wrapper for compiled binaries.

This package automatically detects your platform and loads the appropriate
compiled binary for the Theia SDK.
"""

import sys
import platform
import importlib.util
import importlib.machinery
from pathlib import Path
from typing import Any


def _get_platform_info() -> tuple[str, str]:
    """
    Detect the current platform and architecture.

    Returns:
        tuple: (platform_name, binary_filename)

    Raises:
        RuntimeError: If the platform is not supported
    """
    system = platform.system()
    machine = platform.machine()

    if system == "Linux":
        if machine in ("x86_64", "AMD64"):
            return ("linux-x86_64", "harmoneyes_theia-linux-x86_64.so")
        else:
            raise RuntimeError(
                f"Unsupported Linux architecture: {machine}. "
                "Only x86_64 is supported."
            )

    elif system == "Darwin":  # macOS
        if machine == "arm64":
            return ("macos-arm64", "harmoneyes_theia-macos-arm64.so")
        elif machine == "x86_64":
            # Intel Mac - you might want to add support for this
            raise RuntimeError(
                "Intel Macs (x86_64) are not currently supported. "
                "Only Apple Silicon (arm64) is supported."
            )
        else:
            raise RuntimeError(
                f"Unsupported macOS architecture: {machine}. "
                "Only arm64 is supported."
            )

    elif system == "Windows":
        if machine in ("x86_64", "AMD64"):
            return ("windows-x86_64", "harmoneyes_theia-windows-x86_64.pyd")
        else:
            raise RuntimeError(
                f"Unsupported Windows architecture: {machine}. "
                "Only x86_64 is supported."
            )

    else:
        raise RuntimeError(
            f"Unsupported operating system: {system}. "
            "Supported platforms: Linux (x86_64), macOS (arm64), Windows (x86_64)"
        )


def _load_binary_module(binary_path: Path) -> Any:
    """
    Dynamically load the compiled binary module.

    Args:
        binary_path: Path to the binary file (.so or .pyd)

    Returns:
        The loaded module

    Raises:
        FileNotFoundError: If the binary file doesn't exist
        ImportError: If the binary cannot be loaded
    """
    if not binary_path.exists():
        raise FileNotFoundError(
            f"Binary file not found: {binary_path}\n"
            f"Expected location: {binary_path.absolute()}\n"
            "Please ensure the correct binaries are installed."
        )

    # The Nuitka binary was compiled from 'harmoneyes_theia.py'
    # So it has PyInit_harmoneyes_theia as its init function
    # We MUST use this exact name when loading
    actual_module_name = "harmoneyes_theia"
    internal_module_name = "_harmoneyes_theia_compiled"

    # Create loader with the actual module name (must match PyInit function)
    loader = importlib.machinery.ExtensionFileLoader(actual_module_name, str(binary_path))

    # Create module manually without using spec_from_loader to avoid auto-registration
    spec = importlib.machinery.ModuleSpec(actual_module_name, loader, origin=str(binary_path))
    module = importlib.util.module_from_spec(spec)

    # Register under our internal name BEFORE executing
    # This prevents conflicts with the current package
    sys.modules[internal_module_name] = module

    # Now execute the module (calls PyInit_harmoneyes_theia)
    loader.exec_module(module)

    return module


# Detect platform and load the appropriate binary
_platform_name, _binary_filename = _get_platform_info()
_bin_dir = Path(__file__).parent / "_bin"
_binary_path = _bin_dir / _binary_filename

try:
    _binary_module = _load_binary_module(_binary_path)
except Exception as e:
    raise ImportError(
        f"Failed to load HarmonEyes Theia SDK binary for {_platform_name}.\n"
        f"Error: {e}\n\n"
        "Please ensure you have installed the package correctly and that "
        "the compiled binaries are present in the _bin directory."
    ) from e


# Re-export all public symbols from the binary module
# This makes the API available as: from harmoneyes_theia import TheiaSDK
__all__ = [name for name in dir(_binary_module) if not name.startswith("_")]

for name in __all__:
    globals()[name] = getattr(_binary_module, name)


# Add version and platform info
__version__ = "1.0.0"
__platform__ = _platform_name


def get_platform_info() -> dict[str, str]:
    """
    Get information about the loaded platform binary.

    Returns:
        dict: Platform information including OS, architecture, and binary path
    """
    return {
        "platform": _platform_name,
        "binary_path": str(_binary_path.absolute()),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "version": __version__,
    }
