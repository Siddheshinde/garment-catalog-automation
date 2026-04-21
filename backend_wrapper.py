import sys
import shutil
import importlib
import datetime
from pathlib import Path

APP_ROOT   = Path(__file__).parent.resolve()
INPUT_DIR  = APP_ROOT / "temp_uploads"
STAGE_DIR  = INPUT_DIR / "staged"
OUTPUT_DIR = APP_ROOT / "output"

for _d in [INPUT_DIR, STAGE_DIR, OUTPUT_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# when True, text fields from the UI are used directly and Gemini is skipped
USE_UI_DETAILS = True


def generate_catalog(pages: list, title: str = "") -> tuple[str, list[str]]:
    if not pages:
        raise ValueError("No garment pages provided.")

    total_images = sum(len(p.get("images", {})) for p in pages)
    if total_images == 0:
        raise ValueError("Please upload at least one garment image before generating.")

    garment_map = _stage_images(pages)

    backend = _load_backend()
    _patch_backend_paths(backend)
    backend.setup_folders()

    # use title as filename, fall back to a timestamped default
    safe_name = _safe_filename(title) if title.strip() else \
        f"catalog_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    backend.FINAL_PDF = str(OUTPUT_DIR / f"{safe_name}.pdf")

    model = None if USE_UI_DETAILS else backend.setup_gemini()

    layout_paths = []

    for idx, (garment_id, views) in enumerate(garment_map.items()):
        page_data = pages[idx]

        enhanced = {}
        for view_type, src_path in views.items():
            enhanced[view_type] = backend.enhance_image_ultimate(src_path, garment_id, view_type)

        if USE_UI_DETAILS:
            fabric = page_data.get("fabric") or "95% Poly 5% Spandex"
            style  = page_data.get("style")  or ""
            gsm    = page_data.get("gsm")    or "180"
        else:
            fabric, style, gsm = backend.generate_description(model, enhanced)
            if page_data.get("style"):
                style = page_data["style"]
            if page_data.get("fabric"):
                fabric = page_data["fabric"]
            if page_data.get("gsm"):
                gsm = page_data["gsm"]

        layout_img = backend.create_landscape_layout(
            garment_id,
            enhanced,
            description="",
            style_number=style,
            fabric_info=fabric,
            gsm_info=gsm,
        )

        layout_path = str(Path(backend.LAYOUT_FOLDER) / f"{garment_id}_catalog.jpg")
        layout_img.save(layout_path, quality=98, optimize=True)
        layout_paths.append(layout_path)

    if not layout_paths:
        raise RuntimeError("No layout pages were produced — check your images.")

    backend.create_pdf_landscape(layout_paths)

    pdf_path = Path(backend.FINAL_PDF).resolve()
    if not pdf_path.exists():
        raise RuntimeError(f"PDF expected at {pdf_path} but was not created.")

    # save a small thumbnail next to the PDF so the sidebar can show a preview
    _save_thumbnail(layout_paths[0], str(OUTPUT_DIR / f"{safe_name}_thumb.jpg"))

    return str(pdf_path), layout_paths


def _safe_filename(text: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in " -_" else "" for c in text).strip()
    return cleaned.replace(" ", "_") or "catalog"


def _save_thumbnail(src_path: str, dst_path: str):
    try:
        from PIL import Image as PILImage
        img = PILImage.open(src_path)
        img.thumbnail((300, 200))
        img.save(dst_path, "JPEG", quality=82)
    except Exception as e:
        print(f"[wrapper] thumbnail failed: {e}")


def _stage_images(pages: list) -> dict:
    # clear previous run's staged files so stale images don't carry over
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True)

    garment_map = {}

    for i, page in enumerate(pages, start=1):
        garment_id = f"garment_{i:03d}"
        garment_map[garment_id] = {}

        for view, src_path in page.get("images", {}).items():
            if not src_path:
                continue
            src = Path(src_path)
            if not src.exists():
                print(f"[wrapper] WARNING: image not found: {src_path}")
                continue

            dst = STAGE_DIR / f"{garment_id}_{view}.jpg"

            try:
                from PIL import Image as PILImage
                img = PILImage.open(src)
                # flatten RGBA/P onto white — JPEG doesn't support transparency
                if img.mode in ("RGBA", "P"):
                    bg   = PILImage.new("RGB", img.size, (255, 255, 255))
                    mask = img.split()[-1] if img.mode == "RGBA" else None
                    bg.paste(img, mask=mask)
                    img = bg
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(str(dst), "JPEG", quality=97)
            except Exception as conv_err:
                print(f"[wrapper] PIL conversion failed ({conv_err}), raw copy")
                shutil.copy2(src, dst)

            garment_map[garment_id][view] = str(dst)

    return garment_map


def _load_backend():
    backend_file = APP_ROOT / "catalog_automation.py"
    if not backend_file.exists():
        raise FileNotFoundError(
            "catalog_automation.py not found.\n\n"
            f"Please place it in:\n  {APP_ROOT}"
        )

    app_root_str = str(APP_ROOT)
    if app_root_str not in sys.path:
        sys.path.insert(0, app_root_str)

    # force reload so the path patches below always take effect
    if "catalog_automation" in sys.modules:
        backend = importlib.reload(sys.modules["catalog_automation"])
    else:
        import catalog_automation as _be  # type: ignore  # noqa: PLC0415
        backend = _be

    return backend


def _patch_backend_paths(backend):
    backend.INPUT_FOLDER    = str(STAGE_DIR)
    backend.OUTPUT_FOLDER   = str(OUTPUT_DIR)
    backend.ENHANCED_FOLDER = str(OUTPUT_DIR / "enhanced_final")
    backend.LAYOUT_FOLDER   = str(OUTPUT_DIR / "layout_pages")
    backend.FINAL_PDF       = str(OUTPUT_DIR / "final_catalog.pdf")

    Path(backend.ENHANCED_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(backend.LAYOUT_FOLDER).mkdir(parents=True, exist_ok=True)
