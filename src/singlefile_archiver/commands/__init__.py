"""Commands package for singlefile_archiver."""

# Defer import to avoid RuntimeWarning when running as module
__all__ = ["optimize_filenames_command"]


def __getattr__(name):
    """Lazy loading to prevent import conflicts when running as module."""
    if name == "optimize_filenames_command":
        from .optimize import optimize_filenames_command
        return optimize_filenames_command
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")