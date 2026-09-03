"""Image preprocessing pipeline tailored for video frames and screen captures."""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat


def compute_average_luminance(image: Image.Image) -> float:
    """Calculate the average pixel brightness (0-255) of a grayscale image."""
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    return stat.mean[0]


def preprocess_image(
    image: Image.Image,
    upscale_factor: float = 2.0,
    auto_invert: bool = True,
    enhance_contrast: bool = True,
    binarize: bool = False,
) -> Image.Image:
    """
    Preprocess image to maximize Tesseract OCR accuracy.
    
    1. Upscale low-resolution crops using Lanczos interpolation.
    2. Convert to Grayscale.
    3. Auto-detect dark mode / video slides (light text on dark background) and invert.
    4. Enhance contrast.
    5. Optional thresholding/binarization.
    """
    # 1. Upscale if image is relatively small
    w, h = image.size
    if w < 1000 and h < 600 and upscale_factor > 1.0:
        new_w = int(w * upscale_factor)
        new_h = int(h * upscale_factor)
        processed = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        processed = image.copy()

    # 2. Convert to Grayscale
    processed = processed.convert("L")

    # 3. Auto-Invert: Tesseract works best with dark text on a light background.
    # If the average brightness is < 120, it is likely light text on a dark background.
    if auto_invert:
        avg_brightness = compute_average_luminance(processed)
        if avg_brightness < 120:
            processed = ImageOps.invert(processed)

    # 4. Enhance Contrast
    if enhance_contrast:
        # Autocontrast maximizes dynamic range
        processed = ImageOps.autocontrast(processed, cutoff=2)
        enhancer = ImageEnhance.Contrast(processed)
        processed = enhancer.enhance(1.5)

    # 5. Optional Binarization (Otsu threshold approximation)
    if binarize:
        # Subtle unsharp mask to crispen edges
        processed = processed.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
        # Threshold at 140
        processed = processed.point(lambda p: 255 if p > 140 else 0)

    return processed
