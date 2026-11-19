"""Create a new theme by copying an existing one.

A theme is self-contained, so the copy is a plain copy of the base theme's folder.
"""

import logging
import shutil
from pathlib import Path

from slider.errors import DeckError

logger = logging.getLogger(__name__)


def create_theme(name: str, base: str, themes_dir: Path, bundled_dir: Path) -> Path:
    """Copy theme `base` to themes_dir/name and return the new folder.

    The base is looked up in themes_dir first, then in bundled_dir, so a custom
    theme can be the starting point for another.
    """
    if not name or Path(name).name != name or name in (".", ".."):
        raise DeckError(f"'{name}' is not a valid theme name")
    target = themes_dir / name
    if target.exists():
        raise DeckError(f"Theme '{name}' already exists in {themes_dir}")

    source = next(
        (d / base for d in (themes_dir, bundled_dir) if (d / base).is_dir()), None
    )
    if source is None:
        raise DeckError(
            f"Base theme '{base}' not found in {themes_dir} or {bundled_dir}"
        )

    shutil.copytree(source, target)
    logger.info("Created theme '%s' from '%s' in %s", name, base, target)
    return target
