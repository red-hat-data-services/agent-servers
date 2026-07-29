from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("codex-a2a")
except PackageNotFoundError:
    __version__ = "0.1.0"
