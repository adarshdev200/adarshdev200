from pathlib import Path
import html

import cv2
import numpy as np
from PIL import Image


INPUT = Path("source-prepped.png")
OUTPUT = Path("avi-ascii.svg")


# Dark → light density ramp.
# The darkest tones (eyes, nostrils, lips, hair) get the
# densest glyphs; lightest skin gets the sparsest. A finer
# ramp preserves far more facial structure than 6 levels.
CHARS = "@%#*+=-:. "

# Pixels at/above this are treated as clean background and
# left blank, so the silhouette stays crisp.
BG_THRESHOLD = 232


def enhance_face(gray):
    """
    Sharpen and locally boost contrast across the face so
    the eyes, nose and lips read as distinct features
    instead of melting into flat mid-tone skin.
    """

    h, w = gray.shape

    # -----------------------------------------
    # FACE REGION (eyes → chin)
    # -----------------------------------------
    x1 = int(w * 0.30)
    x2 = int(w * 0.70)

    y1 = int(h * 0.18)
    y2 = int(h * 0.68)

    face = gray[y1:y2, x1:x2].copy()

    # -----------------------------------------
    # 0. Smooth the skin (edge-preserving)
    #
    # Removes blotchy mid-tone noise so flat
    # cheeks/forehead read clean, while keeping
    # the hard edges of eyes, nose and lips.
    # -----------------------------------------

    face = cv2.bilateralFilter(
        face,
        d=9,
        sigmaColor=60,
        sigmaSpace=60
    )

    # -----------------------------------------
    # 1. Local contrast (CLAHE)
    #
    # Spreads the compressed skin tones so the
    # subtle shading around the nose, lips and
    # eye sockets becomes visible.
    # -----------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    face = clahe.apply(face)

    # -----------------------------------------
    # 2. Stronger unsharp mask
    #
    # Crisp edges on eyelids, lip line and the
    # bridge/sides of the nose.
    # -----------------------------------------

    blur = cv2.GaussianBlur(
        face,
        (0, 0),
        1.4
    )

    sharp = cv2.addWeighted(
        face,
        1.85,
        blur,
        -0.85,
        0
    )

    sharp = np.clip(
        sharp,
        0,
        255
    ).astype(np.uint8)

    # -----------------------------------------
    # 3. BLACK-HAT FILTER
    #
    # Finds dark details surrounded by lighter
    # regions: eyes, eyebrows, nostrils, lips.
    # A smaller kernel catches finer features.
    # -----------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (9, 9)
    )

    blackhat = cv2.morphologyEx(
        sharp,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    blackhat = cv2.normalize(
        blackhat,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )

    # -----------------------------------------
    # 4. Darken exactly where features live
    # -----------------------------------------

    enhanced = sharp.astype(np.float32)

    feature_strength = blackhat.astype(
        np.float32
    )

    enhanced -= feature_strength * 0.95

    enhanced = np.clip(
        enhanced,
        0,
        255
    ).astype(np.uint8)

    gray[y1:y2, x1:x2] = enhanced

    return gray


def stretch_tones(gray):
    """
    Spread the subject's tonal range across the full
    0–255 scale (ignoring the white background) so the
    character ramp uses all of its levels on the face.
    """

    subject = gray[gray < BG_THRESHOLD]

    if subject.size == 0:
        return gray

    # Robust min/max so a few extreme pixels don't
    # waste the whole range.
    lo = np.percentile(subject, 2)
    hi = np.percentile(subject, 98)

    if hi <= lo:
        return gray

    stretched = (gray.astype(np.float32) - lo) * (
        255.0 / (hi - lo)
    )

    stretched = np.clip(stretched, 0, 255).astype(np.uint8)

    # Preserve the clean background.
    stretched[gray >= BG_THRESHOLD] = 255

    return stretched


def tone_map(gray):
    """
    Region-aware tone curve.

    FACE / HEAD  – strong S-curve around a high pivot:
                   lifts light skin toward blank (clean skin)
                   and crushes shadows (punchy eyes/nose/lips).

    SHOULDERS /  – gentle contrast plus a darken, so the
    COLLAR         shirt and shoulders stay dense instead of
                   washing out to blank.
    """

    h, w = gray.shape
    boundary = int(h * 0.66)   # chin-ish line

    out = gray.astype(np.float32)

    # ---- Face / head: clean skin, punchy features ----
    head = out[:boundary]
    head = (head - 140.0) * 1.85 + 140.0
    out[:boundary] = head

    # ---- Shoulders / collar: keep it dense ----
    torso = out[boundary:]
    torso = (torso - 128.0) * 1.15 + 128.0 - 22.0
    out[boundary:] = torso

    out = np.clip(out, 0, 255).astype(np.uint8)

    # Keep the background perfectly clean.
    out[gray >= BG_THRESHOLD] = 255

    return out


def image_to_ascii(image, width=200):

    # -----------------------------------------
    # Convert to grayscale
    # -----------------------------------------

    gray = np.array(
        image.convert("L")
    )

    # -----------------------------------------
    # Enhance facial details
    # -----------------------------------------

    gray = enhance_face(gray)

    gray = stretch_tones(gray)

    gray = tone_map(gray)

    # -----------------------------------------
    # Resize (taller ratio keeps more vertical
    # detail in eyes / nose / lips)
    # -----------------------------------------

    h, w = gray.shape

    aspect_ratio = h / w

    height = int(
        width *
        aspect_ratio *
        0.50
    )

    gray = cv2.resize(
        gray,
        (width, height),
        interpolation=cv2.INTER_AREA
    )

    # -----------------------------------------
    # ASCII conversion via the density ramp
    # -----------------------------------------

    ramp = CHARS                 # dark → light
    n = len(ramp)

    lines = []

    for y in range(height):

        line = ""

        for x in range(width):

            pixel = int(gray[y, x])

            # Clean background
            if pixel >= BG_THRESHOLD:
                line += " "
                continue

            # Darker pixel → denser glyph (low index)
            t = (pixel / BG_THRESHOLD)
            idx = int(t * (n - 1) + 0.5)
            idx = max(0, min(n - 1, idx))

            line += ramp[idx]

        lines.append(line)

    return lines


def create_svg(lines):

    width = len(lines[0])
    height = len(lines)

    # -----------------------------------------
    # Character sizing
    # -----------------------------------------

    font_size = 7

    char_width = 4.1

    line_height = 8

    svg_width = int(
        width * char_width
    )

    svg_height = int(
        height * line_height
    )

    elements = []

    char_index = 0

    # -----------------------------------------
    # Generate characters
    # -----------------------------------------

    for row, line in enumerate(lines):

        for col, char in enumerate(line):

            if char == " ":
                continue

            x = col * char_width

            y = (
                row + 1
            ) * line_height

            # Staggered animation
            delay = (
                char_index % 200
            ) * 0.005

            elements.append(
                f'''
                <text
                    x="{x:.1f}"
                    y="{y}"
                    class="ascii"
                    style="animation-delay:{delay:.3f}s"
                >{html.escape(char)}</text>
                '''
            )

            char_index += 1

    # -----------------------------------------
    # SVG
    # -----------------------------------------

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{svg_width}"
    height="{svg_height}"
    viewBox="0 0 {svg_width} {svg_height}"
>

<style>

.ascii {{
    font-family: monospace;
    font-size: {font_size}px;
    font-weight: bold;

    fill: white;

    opacity: 0;

    animation:
        appear 1.5s ease forwards;
}}

@keyframes appear {{

    from {{
        opacity: 0;
    }}

    to {{
        opacity: 1;
    }}

}}

</style>


<rect
    width="100%"
    height="100%"
    fill="#0d1117"
/>


{''.join(elements)}


</svg>
'''

    return svg


def main():

    # -----------------------------------------
    # Check input
    # -----------------------------------------

    if not INPUT.exists():

        print(
            f"ERROR: {INPUT} not found."
        )

        return

    print(
        "Creating enhanced facial ASCII..."
    )

    # -----------------------------------------
    # Load image
    # -----------------------------------------

    image = Image.open(
        INPUT
    )

    # -----------------------------------------
    # Convert
    # -----------------------------------------

    lines = image_to_ascii(
        image,
        width=200
    )

    # -----------------------------------------
    # Generate SVG
    # -----------------------------------------

    svg = create_svg(
        lines
    )

    # -----------------------------------------
    # Save
    # -----------------------------------------

    OUTPUT.write_text(
        svg,
        encoding="utf-8"
    )

    print(
        f"Created: {OUTPUT}"
    )


if __name__ == "__main__":
    main()