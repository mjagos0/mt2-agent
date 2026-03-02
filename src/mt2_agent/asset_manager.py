from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = (".png",)


@dataclass(frozen=True)
class Asset:
    name: str


@dataclass(frozen=True)
class AssetImage(Asset):
    image: np.ndarray  # grayscale, uint8


@dataclass(frozen=True)
class AssetGroup:
    name: str
    assets: list[Asset]

    def __len__(self) -> int:
        return len(self.assets)

    def __iter__(self):
        return iter(self.assets)


class AssetManager:
    groups: dict[str, AssetGroup]

    def __init__(self, asset_icon_dir: str):
        self.groups = {}

        logger.debug("Pre-loading Metin2 icons")
        self.load_icons(Path(asset_icon_dir))

    def load_icons(self, icons_dir: str | Path) -> None:
        icons_dir = Path(icons_dir)
        if not icons_dir.is_dir():
            raise FileNotFoundError(f"Icons directory not found: {icons_dir}")

        for subdir in sorted(icons_dir.iterdir()):
            if not subdir.is_dir():
                continue
            self.groups[subdir.name] = self._load_image_group(subdir)

    def get_group(self, name: str) -> AssetGroup:
        if name not in self.groups:
            raise KeyError(
                f"Unknown group: '{name}'. Available: {list(self.groups.keys())}"
            )
        return self.groups[name]

    def get_all_assets(self) -> list[Asset]:
        return [asset for group in self.groups.values() for asset in group]

    def _load_image_group(self, directory: Path) -> AssetGroup:
        assets: list[Asset] = []
        for f in sorted(directory.iterdir()):
            if f.suffix.lower() not in _IMAGE_EXTENSIONS:
                continue
            bgr = cv2.imread(str(f))
            if bgr is None:
                logger.warning("Could not load: %s", f)
                continue
            assets.append(
                AssetImage(name=f.stem, image=cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
            )

        logger.info("Loaded %d icons from '%s'", len(assets), directory.name)
        return AssetGroup(name=directory.name, assets=assets)
