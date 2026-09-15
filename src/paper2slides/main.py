import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass
class ExtractedImage:
    page_num: int
    path: Path
    width: int
    height: int
    caption: str


def read_pdf_text(pdf_path: Path) -> tuple[int, str]:
    """Read text from all pages of a PDF file"""
    with pymupdf.open(pdf_path) as doc:
        pages = []

        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text").strip()
            pages.append(
                f"\n--- Page {page_num} ---\n"
                f"{page_text}"
            )

        return doc.page_count, "\n".join(pages)


def find_caption(page: pymupdf.Page, xref: int) -> str:
    """Find a likely figure caption bellow an image"""
    image_rectangles = page.get_image_rects(xref)
    if not image_rectangles:
        return "Caption not found"

    image_bottom = image_rectangles[0].y1
    text_blocks = page.get_text("blocks")

    possible_captions = []
    for block in text_blocks:
        block_top = block[1]
        block_text = block[4].strip()

        is_below_image = block_top >= image_bottom
        looks_like_caption = re.match(
            r"^(Figure|Fig\.)\s*\d+",
            block_text,
            re.IGNORECASE,
        )

        if is_below_image and looks_like_caption:
            possible_captions.append(block_text.replace("\n", " "))

    if not possible_captions:
        return "Caption not found"

    return possible_captions[0]


def extract_images(pdf_path: Path, output_dir: Path) -> list[ExtractedImage]:
    """Extract images from a PDF file"""
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted_images = []
    seen_xrefs = set()
    with pymupdf.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            page_images = page.get_images(full=True)
            for image_num, image in enumerate(page_images, start=1):
                xref = image[0]
                if xref in seen_xrefs:
                    continue

                seen_xrefs.add(xref)

                image_info = doc.extract_image(xref)
                width, height = image_info["width"], image_info["height"]

                if width < 120 or height < 120:
                    continue

                caption = find_caption(page, xref)

                extension = image_info["ext"]
                image_path = output_dir / f"page_{page_num}_image_{image_num}.{extension}"

                image_path.write_bytes(image_info["image"])

                extracted_images.append(
                    ExtractedImage(
                        page_num=page_num,
                        path=image_path,
                        width=width,
                        height=height,
                        caption=caption,
                    )
                )

    return extracted_images


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from PDF"
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("data/extracted_images"),
        help="Directory to save extracted images",
    )

    args = parser.parse_args()

    if not args.pdf_path.exists():
        parser.error(f"PDF file '{args.pdf_path}' does not exist")

    if args.pdf_path.suffix.lower() != ".pdf":
        parser.error(f"file '{args.pdf_path}' is not a PDF file")

    page_count, text = read_pdf_text(args.pdf_path)
    images = extract_images(args.pdf_path, args.images_dir)

    print(f"\nPages: {page_count}")
    print(f"Characters extracted: {len(text)}")
    print(f"Images extracted: {len(images)}")

    print("\n--- Extracted images ---")
    for image in images:
        print(
            f"\nPage {image.page_num}: "
            f"{image.path} ({image.width} x {image.height})"
        )
        print(f"Caption: {image.caption}")

    print("\n--- Text preview ---")
    print(text[:2000])


if __name__ == "__main__":
    main()
