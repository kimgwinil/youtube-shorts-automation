from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


PROJECT_ROOT = Path("/Users/kimgwonil/youtube-shorts-automation")
BACKGROUND_ROOT = PROJECT_ROOT / "content" / "backgrounds"


def main() -> int:
    dawn_base = Image.open(BACKGROUND_ROOT / "dawn" / "placeholder_dawn.png").convert("RGB")
    rain_base = Image.open(BACKGROUND_ROOT / "rain" / "placeholder_rain.png").convert("RGB")

    city_frame = Image.open(PROJECT_ROOT / "output" / "city_frame_seed.png").convert("RGB")

    recipes: list[tuple[Image.Image, Path, Callable[[Image.Image], Image.Image]]] = [
        (dawn_base, BACKGROUND_ROOT / "dawn" / "watercolor" / "dawn_wash_01.png", watercolor),
        (dawn_variant(dawn_base, "crop_left"), BACKGROUND_ROOT / "dawn" / "watercolor" / "dawn_wash_02.png", watercolor_soft),
        (dawn_variant(dawn_base, "flip"), BACKGROUND_ROOT / "dawn" / "watercolor" / "dawn_wash_03.png", watercolor_bright),
        (dawn_base, BACKGROUND_ROOT / "dawn" / "ink" / "dawn_ink_01.png", inkwash),
        (dawn_variant(dawn_base, "crop_center"), BACKGROUND_ROOT / "dawn" / "ink" / "dawn_ink_02.png", inkwash_soft),
        (dawn_variant(dawn_base, "flip"), BACKGROUND_ROOT / "dawn" / "ink" / "dawn_ink_03.png", inkwash_dark),
        (dawn_base, BACKGROUND_ROOT / "dawn" / "calligraphy" / "dawn_calligraphy_01.png", calligraphy),
        (dawn_variant(dawn_base, "crop_right"), BACKGROUND_ROOT / "dawn" / "calligraphy" / "dawn_calligraphy_02.png", calligraphy_warm),
        (dawn_variant(dawn_base, "flip"), BACKGROUND_ROOT / "dawn" / "calligraphy" / "dawn_calligraphy_03.png", calligraphy_soft),
        (rain_base, BACKGROUND_ROOT / "rain" / "photoreal" / "rain_real_01.png", photoreal_soft),
        (rain_variant(rain_base, "crop_left"), BACKGROUND_ROOT / "rain" / "photoreal" / "rain_real_02.png", photoreal_moody),
        (rain_variant(rain_base, "crop_center"), BACKGROUND_ROOT / "rain" / "photoreal" / "rain_real_03.png", photoreal_soft),
        (rain_base, BACKGROUND_ROOT / "rain" / "watercolor" / "rain_wash_01.png", watercolor),
        (rain_variant(rain_base, "flip"), BACKGROUND_ROOT / "rain" / "watercolor" / "rain_wash_02.png", watercolor_soft),
        (rain_variant(rain_base, "crop_right"), BACKGROUND_ROOT / "rain" / "watercolor" / "rain_wash_03.png", watercolor_deep),
        (rain_base, BACKGROUND_ROOT / "rain" / "ink" / "rain_ink_01.png", inkwash),
        (rain_variant(rain_base, "crop_center"), BACKGROUND_ROOT / "rain" / "ink" / "rain_ink_02.png", inkwash_dark),
        (rain_variant(rain_base, "flip"), BACKGROUND_ROOT / "rain" / "ink" / "rain_ink_03.png", inkwash_soft),
        (rain_base, BACKGROUND_ROOT / "rain" / "calligraphy" / "rain_calligraphy_01.png", calligraphy),
        (rain_variant(rain_base, "crop_left"), BACKGROUND_ROOT / "rain" / "calligraphy" / "rain_calligraphy_02.png", calligraphy_soft),
        (rain_variant(rain_base, "crop_right"), BACKGROUND_ROOT / "rain" / "calligraphy" / "rain_calligraphy_03.png", calligraphy_warm),
        (city_frame, BACKGROUND_ROOT / "city" / "watercolor" / "city_wash_01.png", watercolor),
        (city_variant(city_frame, "crop_left"), BACKGROUND_ROOT / "city" / "watercolor" / "city_wash_02.png", watercolor_soft),
        (city_variant(city_frame, "flip"), BACKGROUND_ROOT / "city" / "watercolor" / "city_wash_03.png", watercolor_bright),
        (city_frame, BACKGROUND_ROOT / "city" / "ink" / "city_ink_01.png", inkwash),
        (city_variant(city_frame, "crop_center"), BACKGROUND_ROOT / "city" / "ink" / "city_ink_02.png", inkwash_soft),
        (city_variant(city_frame, "flip"), BACKGROUND_ROOT / "city" / "ink" / "city_ink_03.png", inkwash_dark),
        (city_frame, BACKGROUND_ROOT / "city" / "calligraphy" / "city_calligraphy_01.png", calligraphy),
        (city_variant(city_frame, "crop_right"), BACKGROUND_ROOT / "city" / "calligraphy" / "city_calligraphy_02.png", calligraphy_warm),
        (city_variant(city_frame, "flip"), BACKGROUND_ROOT / "city" / "calligraphy" / "city_calligraphy_03.png", calligraphy_soft),
    ]

    for source, target, transform in recipes:
        target.parent.mkdir(parents=True, exist_ok=True)
        transformed = transform(source.copy())
        transformed.save(target)

    return 0


def photoreal_soft(image: Image.Image) -> Image.Image:
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Color(image).enhance(0.85)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    return image.filter(ImageFilter.GaussianBlur(0.4))


def photoreal_moody(image: Image.Image) -> Image.Image:
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Color(image).enhance(0.7)
    image = ImageEnhance.Brightness(image).enhance(0.9)
    image = ImageEnhance.Contrast(image).enhance(1.18)
    return image.filter(ImageFilter.GaussianBlur(0.7))


def watercolor(image: Image.Image) -> Image.Image:
    base = image.filter(ImageFilter.GaussianBlur(1.8))
    base = ImageOps.posterize(base, 5)
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    edges = ImageOps.invert(edges).filter(ImageFilter.GaussianBlur(1.2))
    edges_rgb = Image.merge("RGB", (edges, edges, edges))
    paper = Image.new("RGB", base.size, (245, 239, 229))
    blend = Image.blend(base, paper, 0.18)
    blend = ImageChops.multiply(blend, edges_rgb)
    return ImageEnhance.Color(blend).enhance(0.78)


def watercolor_soft(image: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(watercolor(image)).enhance(1.04)


def watercolor_bright(image: Image.Image) -> Image.Image:
    return ImageEnhance.Color(ImageEnhance.Brightness(watercolor(image)).enhance(1.08)).enhance(0.82)


def watercolor_deep(image: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(ImageEnhance.Color(watercolor(image)).enhance(0.68)).enhance(1.14)


def inkwash(image: Image.Image) -> Image.Image:
    gray = image.convert("L")
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.GaussianBlur(1.4))
    gray = ImageOps.posterize(gray.convert("RGB"), 3).convert("L")
    paper = Image.new("RGB", image.size, (241, 237, 228))
    ink = Image.merge("RGB", (gray, gray, gray))
    mixed = ImageChops.multiply(paper, ink)
    mixed = ImageEnhance.Contrast(mixed).enhance(1.25)
    return mixed


def inkwash_soft(image: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(inkwash(image)).enhance(1.05)


def inkwash_dark(image: Image.Image) -> Image.Image:
    return ImageEnhance.Contrast(ImageEnhance.Brightness(inkwash(image)).enhance(0.92)).enhance(1.18)


def calligraphy(image: Image.Image) -> Image.Image:
    base = inkwash(image)
    sepia = ImageOps.colorize(base.convert("L"), (70, 55, 35), (247, 242, 230))
    edges = image.convert("L").filter(ImageFilter.CONTOUR)
    edges = ImageOps.invert(edges).filter(ImageFilter.GaussianBlur(0.6))
    edges_rgb = Image.merge("RGB", (edges, edges, edges))
    brushed = ImageChops.multiply(sepia, edges_rgb)
    return ImageEnhance.Contrast(brushed).enhance(1.15)


def calligraphy_soft(image: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(calligraphy(image)).enhance(1.03)


def calligraphy_warm(image: Image.Image) -> Image.Image:
    return ImageEnhance.Color(ImageEnhance.Brightness(calligraphy(image)).enhance(1.04)).enhance(0.88)


def dawn_variant(image: Image.Image, mode: str) -> Image.Image:
    return _variant(image, mode)


def rain_variant(image: Image.Image, mode: str) -> Image.Image:
    tinted = ImageEnhance.Color(image).enhance(0.9)
    return _variant(tinted, mode)


def city_variant(image: Image.Image, mode: str) -> Image.Image:
    contrasted = ImageEnhance.Contrast(image).enhance(1.06)
    return _variant(contrasted, mode)


def _variant(image: Image.Image, mode: str) -> Image.Image:
    if mode == "flip":
        return ImageOps.mirror(image)
    if mode == "crop_left":
        return _crop_and_resize(image, 0.0)
    if mode == "crop_center":
        return _crop_and_resize(image, 0.17)
    if mode == "crop_right":
        return _crop_and_resize(image, 0.33)
    return image


def _crop_and_resize(image: Image.Image, offset_ratio: float) -> Image.Image:
    width, height = image.size
    crop_width = int(width * 0.72)
    left = int((width - crop_width) * offset_ratio)
    right = min(left + crop_width, width)
    if right - left < crop_width:
        left = width - crop_width
    cropped = image.crop((left, 0, right, height))
    return cropped.resize((width, height), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    raise SystemExit(main())
