import sys
from pathlib import Path

import cv2
import numpy as np


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 prep_photo.py source-photo.png")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path("source-prepped.png")

    image = cv2.imread(str(input_path))

    if image is None:
        print(f"Could not open {input_path}")
        sys.exit(1)

    h, w = image.shape[:2]

    # Start with the whole image as probable background
    mask = np.zeros((h, w), np.uint8)

    # Rectangle containing the person
    rect = (
        int(w * 0.18),
        0,
        int(w * 0.64),
        h
    )

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Separate foreground from background
    cv2.grabCut(
        image,
        mask,
        rect,
        bgd_model,
        fgd_model,
        5,
        cv2.GC_INIT_WITH_RECT
    )

    # Foreground + probable foreground
    foreground = np.where(
        (mask == cv2.GC_FGD) |
        (mask == cv2.GC_PR_FGD),
        255,
        0
    ).astype("uint8")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Remove background
    gray[foreground == 0] = 255

    # Improve contrast
    gray = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    ).apply(gray)

    # Keep background completely white
    gray[foreground == 0] = 255

    cv2.imwrite(str(output_path), gray)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()