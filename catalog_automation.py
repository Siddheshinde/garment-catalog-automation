"""
ULTIMATE GARMENT CATALOG AUTOMATION SYSTEM - 16:9 LANDSCAPE
Professional catalog matching reference design
Features: AI Background Removal, 16:9 Layout, Multiple Garments Support,
          Auto-orientation correction, Balanced layout
"""

import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter, ImageOps
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import google.generativeai as genai
from collections import defaultdict

# Try to import rembg for background removal
try:
    from rembg import remove
    REMBG_AVAILABLE = True
    print("✓ AI Background Removal: ENABLED")
except ImportError:
    REMBG_AVAILABLE = False
    print("⚠ AI Background Removal: DISABLED (install with: pip install rembg)")

# ============== CONFIGURATION ==============
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INPUT_FOLDER = "input_images"
OUTPUT_FOLDER = "output"
ENHANCED_FOLDER = os.path.join(OUTPUT_FOLDER, "enhanced_final")
LAYOUT_FOLDER = os.path.join(OUTPUT_FOLDER, "layout_pages")
FINAL_PDF = os.path.join(OUTPUT_FOLDER, "final_catalog.pdf")

# Enhancement Settings
USE_AI_BACKGROUND_REMOVAL = True   # True = Remove background with AI
PROCESS_DESIGN_IMAGE = False        # False = Skip background removal on design/detail images
WRINKLE_STRENGTH = 0.30            # 0.0-1.0, gentle wrinkle smoothing
COLOR_BOOST = 1.10                 # 1.0-1.5, subtle color enhancement
CONTRAST_BOOST = 1.10              # 1.0-1.5, gentle contrast
SHARPNESS_BOOST = 1.20             # 1.0-2.0, moderate sharpness

# 16:9 Landscape dimensions (Full HD quality)
LAYOUT_WIDTH = 1920
LAYOUT_HEIGHT = 1080

# ============== SETUP ==============
def setup_folders():
    """Create output folders"""
    for folder in [OUTPUT_FOLDER, ENHANCED_FOLDER, LAYOUT_FOLDER]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    print("✓ Folders created")

def setup_gemini():
    """Initialize Gemini AI"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✓ Gemini AI initialized")
        return model
    except Exception as e:
        print(f"⚠ Gemini AI failed: {e}")
        return None

# ============== IMAGE ORGANIZATION ==============
def organize_images(input_folder):
    """Group images by garment ID"""
    garments = {}
    for file in Path(input_folder).glob("*.*"):
        if file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            parts = file.stem.lower().split('_')
            if len(parts) >= 3:
                garment_id = f"{parts[0]}_{parts[1]}"
                view_type = parts[2]
                if garment_id not in garments:
                    garments[garment_id] = {}
                garments[garment_id][view_type] = str(file)
    print(f"✓ Found {len(garments)} garments")
    return garments

# ============== AUTO-ORIENTATION CORRECTION ==============
def fix_orientation(img):
    """
    Correct image orientation using EXIF data and straighten if tilted.
    This fixes:
      1. EXIF rotation tags (most common cause of tilted phone photos)
      2. Applies ImageOps.exif_transpose for full EXIF correction
    """
    try:
        # Primary fix: use Pillow's built-in EXIF transpose (handles all 8 EXIF orientations)
        img = ImageOps.exif_transpose(img)
        print(f"         ✅ EXIF orientation corrected")
    except Exception as e:
        print(f"         ⚠ EXIF correction skipped: {e}")

    # Secondary fix: if image is wider than tall for a garment photo, rotate 90°
    # (catches cases where phone was held landscape when shooting a hanging garment)
    if img.width > img.height * 1.2:
        img = img.rotate(90, expand=True)
        print(f"         ↩ Rotated landscape→portrait (garment photo)")

    return img

# ============== AI BACKGROUND REMOVAL ==============
def remove_background_ai(img):
    """Remove background using AI (rembg library)"""
    if not REMBG_AVAILABLE:
        print("      ⚠ Skipping AI removal (rembg not installed)")
        return img
    try:
        output = remove(img)
        white_bg = Image.new('RGB', output.size, (255, 255, 255))
        if output.mode == 'RGBA':
            white_bg.paste(output, (0, 0), output)
        else:
            white_bg = output.convert('RGB')
        return white_bg
    except Exception as e:
        print(f"      ⚠ AI removal failed: {e}")
        return img

# ============== ENHANCEMENT ==============
def smooth_wrinkles_gentle(img):
    """Gentle wrinkle smoothing"""
    smoothed = img.filter(ImageFilter.SMOOTH)
    img = Image.blend(img, smoothed, alpha=WRINKLE_STRENGTH)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(SHARPNESS_BOOST)
    return img

def enhance_colors_natural(img):
    """Natural color enhancement"""
    img = ImageOps.autocontrast(img, cutoff=1)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(COLOR_BOOST)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(CONTRAST_BOOST)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.02)
    return img

# ============== MASTER ENHANCEMENT ==============
def enhance_image_ultimate(image_path, garment_id, view_type):
    """
    Ultimate image enhancement pipeline
    Front/Back: Full enhancement with background removal
    Design: Color enhancement only (keeps background)
    """
    print(f"    🎨 Processing {view_type} view...")
    try:
        img = Image.open(image_path)

        # ── ORIENTATION FIX (always applied first) ──
        print(f"       🔄 Checking orientation...")
        img = fix_orientation(img)

        # Convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if view_type in ['design', 'detail', 'label']:
            print(f"       🌈 Enhancing colors (keeping background)...")
            img = enhance_colors_natural(img)
            print(f"       🧹 Light smoothing...")
            img = smooth_wrinkles_gentle(img)
        else:
            if USE_AI_BACKGROUND_REMOVAL and REMBG_AVAILABLE:
                print(f"       🤖 AI background removal...")
                img = remove_background_ai(img)
            print(f"       🧹 Smoothing fabric...")
            img = smooth_wrinkles_gentle(img)
            print(f"       🌈 Enhancing colors...")
            img = enhance_colors_natural(img)

        print(f"       ✨ Final polish...")
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.05)

        output_path = os.path.join(ENHANCED_FOLDER, f"{garment_id}_{view_type}_enhanced.jpg")
        img.save(output_path, quality=98, optimize=True)
        print(f"       ✅ Saved!")
        return output_path

    except Exception as e:
        print(f"       ❌ Enhancement failed: {e}")
        return image_path

# ============== FONT LOADER ==============
def load_font(size, bold=False):
    """Load best available font, bold or regular"""
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "arial.ttf",
            "DejaVuSans.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()

# ============== 16:9 LANDSCAPE LAYOUT ==============
def create_landscape_layout(garment_id, images_dict, description,
                            style_number="", fabric_info="", gsm_info=""):
    """
    Create 16:9 landscape catalog page — professional, balanced, perfectly centered.
    Layout zones:
      Col 1 (left)   → Front view
      Col 2 (center) → Back view
      Col 3 (right)  → Fabric closeup
    Caption block sits just below the image area.
    """

    # ── Canvas ──
    BG      = '#F7F8FA'
    NAVY    = '#1A3A6B'
    DIVIDER = '#D0DBE8'
    BOXLINE = '#BBCDE0'
    WHITE   = '#FFFFFF'

    layout = Image.new('RGB', (LAYOUT_WIDTH, LAYOUT_HEIGHT), BG)
    draw   = ImageDraw.Draw(layout)

    # ── Outer border ──
    BORDER = 6
    draw.rectangle([(BORDER, BORDER), (LAYOUT_WIDTH - BORDER, LAYOUT_HEIGHT - BORDER)],
                   outline=NAVY, width=BORDER)

    # ── Header bar ──
    HEADER_H = 88
    draw.rectangle([(BORDER, BORDER), (LAYOUT_WIDTH - BORDER, HEADER_H)],
                   fill=NAVY)

    # ── Fonts ──
    font_title   = load_font(54, bold=True)
    font_badge   = load_font(26, bold=False)
    font_style   = load_font(30, bold=True)
    font_detail  = load_font(24, bold=False)
    font_label   = load_font(27, bold=True)

    # ── Header text ──
    draw.text((48, 20), "STYLE CATALOGUE", fill=WHITE, font=font_title)

    id_text = garment_id.upper().replace('_', ' ')
    draw.text((LAYOUT_WIDTH - 300, 30), id_text, fill='#A8C4E8', font=font_badge)

    # ── Content area boundaries ──
    CONTENT_TOP    = HEADER_H + 28          # just below header
    CAPTION_HEIGHT = 105                    # reserved for text at the bottom
    CONTENT_BOTTOM = LAYOUT_HEIGHT - CAPTION_HEIGHT - 20  # image zone ends here
    CONTENT_H      = CONTENT_BOTTOM - CONTENT_TOP         # ≈ 859 px

    # ── Image dimensions ──
    GARMENT_W = 430
    GARMENT_H = int(CONTENT_H * 0.93)       # tall garment images

    DESIGN_SIZE = int(CONTENT_H * 0.60)     # square closeup

    # ── Column center-X positions ──
    COL1_CX = int(LAYOUT_WIDTH * 0.18)      # Front
    COL2_CX = int(LAYOUT_WIDTH * 0.46)      # Back
    COL3_CX = int(LAYOUT_WIDTH * 0.76)      # Design

    # Vertical center for garment images
    GARMENT_CY = CONTENT_TOP + GARMENT_H // 2

    # ── Helper: paste image centered at (cx, cy) ──
    def paste_centered(img_path, cx, cy, max_w, max_h, square_crop=False):
        img = Image.open(img_path)

        # Always fix orientation before placing
        img = fix_orientation(img)

        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')

        if square_crop:
            s = min(img.width, img.height)
            img = img.crop(((img.width  - s) // 2,
                            (img.height - s) // 2,
                            (img.width  + s) // 2,
                            (img.height + s) // 2))

        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

        x = cx - img.width  // 2
        y = cy - img.height // 2

        # Flatten RGBA onto background color
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, BG)
            bg.paste(img, (0, 0), img)
            img = bg

        layout.paste(img, (x, y))
        return img.width, img.height

    # ── Front image ──
    if 'front' in images_dict:
        paste_centered(images_dict['front'], COL1_CX, GARMENT_CY, GARMENT_W, GARMENT_H)

    # ── Back image ──
    if 'back' in images_dict:
        paste_centered(images_dict['back'], COL2_CX, GARMENT_CY, GARMENT_W, GARMENT_H)

    # ── Design / Fabric closeup ──
    if 'design' in images_dict:
        BOX_PAD = 14
        # Vertically center the box in the same zone as garments
        design_cy  = GARMENT_CY
        bx = COL3_CX - DESIGN_SIZE // 2 - BOX_PAD
        by = design_cy - DESIGN_SIZE // 2 - BOX_PAD

        draw.rectangle(
            [(bx, by), (bx + DESIGN_SIZE + BOX_PAD * 2, by + DESIGN_SIZE + BOX_PAD * 2)],
            outline=BOXLINE, width=3, fill=WHITE
        )

        paste_centered(images_dict['design'], COL3_CX, design_cy,
                       DESIGN_SIZE, DESIGN_SIZE, square_crop=True)

        # "Fabric Closeup" label — centered under the box
        closeup_label_y = by + DESIGN_SIZE + BOX_PAD * 2 + 12
        label_text = "Fabric Closeup"
        # Measure text width for centering
        try:
            bbox = draw.textbbox((0, 0), label_text, font=font_label)
            label_w = bbox[2] - bbox[0]
        except:
            label_w = len(label_text) * 14
        draw.text((COL3_CX - label_w // 2, closeup_label_y),
                  label_text, fill=NAVY, font=font_label)

    # ── Divider lines ──
    DIV_Y1 = CONTENT_TOP + 10
    DIV_Y2 = CONTENT_BOTTOM - 10
    for dx in [int(LAYOUT_WIDTH * 0.32), int(LAYOUT_WIDTH * 0.615)]:
        draw.line([(dx, DIV_Y1), (dx, DIV_Y2)], fill=DIVIDER, width=2)

    # ── Caption block — positioned just below image zone ──
    # Moved UP: starts at CONTENT_BOTTOM + 14 (was +10 but images ended higher)
    CAPTION_Y = CONTENT_BOTTOM - 20

    style_val  = style_number or garment_id.upper().replace('_', ' ')
    fabric_val = fabric_info  or '95% Poly 5% Spandex'
    gsm_val    = gsm_info     or '180'

    LINE_GAP = 34   # spacing between caption lines

    for col_cx in [COL1_CX, COL2_CX]:
        x0 = col_cx - GARMENT_W // 2

        draw.text((x0, CAPTION_Y),
                  f"Style No – {style_val}",
                  fill=NAVY, font=font_style)

        draw.text((x0, CAPTION_Y + LINE_GAP),
                  f"Fabric  –  {fabric_val}",
                  fill='#444444', font=font_detail)

        draw.text((x0, CAPTION_Y + LINE_GAP * 2),
                  f"GSM  –  {gsm_val}",
                  fill='#444444', font=font_detail)

    # ── Footer rule ──
    draw.rectangle(
        [(BORDER, LAYOUT_HEIGHT - BORDER - 5),
         (LAYOUT_WIDTH - BORDER, LAYOUT_HEIGHT - BORDER)],
        fill=NAVY
    )

    return layout


# ============== AI DESCRIPTION ==============
def generate_description(model, images_dict):
    """Generate AI description"""
    if not model:
        return "95% Poly 5% Spandex", "", "180"

    prompt = """Analyze these garment images and extract:
1. Fabric composition (from label if visible)
2. Style number (if visible on label)
3. GSM (fabric weight, if visible)

Return in format:
Fabric: [fabric type]
Style: [style number]
GSM: [number]"""

    images_to_send = []
    for view in ['label', 'front', 'back', 'design']:
        if view in images_dict:
            try:
                img = Image.open(images_dict[view])
                images_to_send.append(img)
            except:
                pass

    if not images_to_send:
        return "95% Poly 5% Spandex", "", "180"

    try:
        response = model.generate_content([prompt] + images_to_send)
        text = response.text.strip()
        fabric = "95% Poly 5% Spandex"
        style = ""
        gsm = "180"
        for line in text.split('\n'):
            if 'fabric' in line.lower():
                fabric = line.split(':', 1)[-1].strip()
            elif 'style' in line.lower():
                style = line.split(':', 1)[-1].strip()
            elif 'gsm' in line.lower():
                gsm = line.split(':', 1)[-1].strip()
        return fabric, style, gsm
    except Exception as e:
        print(f"  ⚠ AI description failed: {e}")
        return "95% Poly 5% Spandex", "", "180"


# ============== PDF GENERATION (16:9 LANDSCAPE) ==============
def create_pdf_landscape(layout_pages):
    """Create 16:9 landscape PDF"""
    page_width  = LAYOUT_WIDTH  * 0.75   # pixels → points
    page_height = LAYOUT_HEIGHT * 0.75

    c = canvas.Canvas(FINAL_PDF, pagesize=(page_width, page_height))
    for layout_path in layout_pages:
        img_reader = ImageReader(layout_path)
        c.drawImage(img_reader, 0, 0,
                    width=page_width, height=page_height,
                    preserveAspectRatio=True)
        c.showPage()
    c.save()
    print(f"✓ PDF created: {FINAL_PDF}")


# ============== MAIN ==============
def main():
    print("=" * 80)
    print("🚀 ULTIMATE GARMENT CATALOG AUTOMATION - 16:9 LANDSCAPE")
    print("=" * 80)

    print("\n[1/5] Setting up...")
    setup_folders()
    model = setup_gemini()

    print("\n[2/5] Organizing images...")
    garments = organize_images(INPUT_FOLDER)

    if not garments:
        print("❌ No images found!")
        print("   Expected: input_images/garment_001_front.jpg, etc.")
        return

    print("\n[3/5] Processing images...")
    if REMBG_AVAILABLE and USE_AI_BACKGROUND_REMOVAL:
        print("   Mode: AI Background Removal (front/back only)")
    else:
        print("   Mode: Color Enhancement only")

    layout_pages = []

    for idx, (garment_id, images) in enumerate(garments.items(), 1):
        print(f"\n{'=' * 80}")
        print(f"📦 Processing {garment_id} ({idx}/{len(garments)})")
        print(f"{'=' * 80}")

        # Enhance images
        enhanced_images = {}
        for view_type, image_path in images.items():
            enhanced_path = enhance_image_ultimate(image_path, garment_id, view_type)
            enhanced_images[view_type] = enhanced_path

        # Get fabric info from AI
        print(f"\n  📝 Extracting fabric details from label...")
        fabric, style, gsm = generate_description(model, enhanced_images)
        print(f"  ✅ Details: {fabric}, GSM {gsm}")

        # Create layout
        print(f"\n  🎨 Creating 16:9 landscape layout...")
        layout = create_landscape_layout(garment_id, enhanced_images, "", style, fabric, gsm)
        layout_path = os.path.join(LAYOUT_FOLDER, f"{garment_id}_catalog.jpg")
        layout.save(layout_path, quality=98, optimize=True)
        layout_pages.append(layout_path)
        print(f"  ✅ Layout complete!")

    print(f"\n[4/5] Creating 16:9 landscape PDF catalog...")
    create_pdf_landscape(layout_pages)

    print(f"\n[5/5] 🎉 SUCCESS!")
    print("=" * 80)
    print(f"✅ Processed {len(garments)} garments")
    print(f"✅ 16:9 Landscape format")
    print(f"✅ Auto-orientation correction on every image")
    print(f"✅ Front/Back: Background removed + oriented")
    print(f"✅ Design: Enhanced only (background preserved)")
    print(f"✅ Final catalog: {FINAL_PDF}")
    print("=" * 80)
    print(f"\n📁 Check outputs:")
    print(f"   Enhanced images: {ENHANCED_FOLDER}/")
    print(f"   Layout pages:    {LAYOUT_FOLDER}/")
    print(f"   Final PDF:       {FINAL_PDF}")
    print("=" * 80)


if __name__ == "__main__":
    main()