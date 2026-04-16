"""
Garment Catalog Automation - BALANCED PROFESSIONAL QUALITY
Features: Subtle Enhancement, Natural Look, Full-Page PDF Layout
"""

import os
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import google.generativeai as genai
from collections import defaultdict

# ============== CONFIGURATION ==============
GEMINI_API_KEY = "AIzaSyAekIcAC_3CJYE2T9_Fbg4P1vjkztL-prA"
INPUT_FOLDER = "input_images"
OUTPUT_FOLDER = "output"
ENHANCED_FOLDER = os.path.join(OUTPUT_FOLDER, "enhanced_studio_quality")
LAYOUT_FOLDER = os.path.join(OUTPUT_FOLDER, "layout_pages")
FINAL_PDF = os.path.join(OUTPUT_FOLDER, "final_catalog.pdf")

# Balanced enhancement settings (not too strong!)
BACKGROUND_THRESHOLD = 170  # Lower = more aggressive whitening
WRINKLE_STRENGTH = 0.4      # 0.0-1.0, higher = more smoothing
COLOR_BOOST = 1.15          # 1.0-1.5, higher = more vibrant
CONTRAST_BOOST = 1.15       # 1.0-1.5, higher = more dramatic
SHARPNESS_BOOST = 1.3       # 1.0-2.0, higher = sharper

# ============== SETUP ==============
def setup_folders():
    """Create output folders"""
    for folder in [OUTPUT_FOLDER, ENHANCED_FOLDER, LAYOUT_FOLDER]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    print("✓ Folders created")

def setup_gemini():
    """Initialize Gemini AI"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✓ Gemini AI initialized")
    return model

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

# ============== GENTLE BACKGROUND WHITENING ==============
def make_background_white_gentle(img):
    """
    Gentle background whitening - looks natural
    Only whitens obvious background areas
    """
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            avg = (r + g + b) / 3
            
            # Only whiten very light pixels (obvious background)
            if avg > BACKGROUND_THRESHOLD:
                # Gradually transition to white
                factor = (avg - BACKGROUND_THRESHOLD) / (255 - BACKGROUND_THRESHOLD)
                new_r = int(r + (255 - r) * factor)
                new_g = int(g + (255 - g) * factor)
                new_b = int(b + (255 - b) * factor)
                pixels[x, y] = (new_r, new_g, new_b)
    
    return img

# ============== GENTLE WRINKLE SMOOTHING ==============
def smooth_wrinkles_gentle(img):
    """
    Gentle wrinkle smoothing - maintains natural fabric texture
    """
    # Very light smoothing
    smoothed = img.filter(ImageFilter.SMOOTH)
    
    # Blend just a little with original (keeps texture)
    img = Image.blend(img, smoothed, alpha=WRINKLE_STRENGTH)
    
    # Light median filter for tiny imperfections only
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # Restore sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(SHARPNESS_BOOST)
    
    return img

# ============== NATURAL COLOR ENHANCEMENT ==============
def enhance_colors_natural(img):
    """
    Natural color enhancement - subtle improvements
    """
    # Gentle auto-contrast
    img = ImageOps.autocontrast(img, cutoff=1)
    
    # Subtle color boost
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(COLOR_BOOST)
    
    # Gentle contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(CONTRAST_BOOST)
    
    # Slight brightness adjustment
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    
    return img

# ============== MASTER ENHANCEMENT FUNCTION ==============
def enhance_image_studio_quality(image_path, garment_id, view_type):
    """
    Apply gentle professional enhancements
    """
    print(f"    🎨 Processing {view_type} view...")
    
    # Load image
    img = Image.open(image_path)
    
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Step 1: Gentle background whitening
    print(f"       ⚪ Whitening background (gentle)...")
    img = make_background_white_gentle(img)
    
    # Step 2: Gentle wrinkle smoothing
    print(f"       🧹 Smoothing fabric (gentle)...")
    img = smooth_wrinkles_gentle(img)
    
    # Step 3: Natural color enhancement
    print(f"       🌈 Enhancing colors (natural)...")
    img = enhance_colors_natural(img)
    
    # Step 4: Final light polish
    print(f"       ✨ Final polish...")
    
    # Very subtle edge enhancement
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.1)
    
    # Save enhanced image
    output_path = os.path.join(ENHANCED_FOLDER, f"{garment_id}_{view_type}_enhanced.jpg")
    img.save(output_path, quality=95, optimize=True)
    
    print(f"       ✅ Saved!")
    return output_path

# ============== FULL-PAGE PDF LAYOUT ==============
def create_fullpage_layout(garment_id, images_dict, description):
    """
    Create FULL A4 page layout with large, uncropped images
    """
    # A4 size in pixels at 300 DPI
    dpi = 300
    a4_width_inches = 8.27
    a4_height_inches = 11.69
    
    width = int(a4_width_inches * dpi)
    height = int(a4_height_inches * dpi)
    
    # Create white canvas
    layout = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(layout)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 100)
        label_font = ImageFont.truetype("arial.ttf", 60)
        desc_font = ImageFont.truetype("arial.ttf", 50)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        desc_font = ImageFont.load_default()
    
    # Title section (top 10%)
    title_height = int(height * 0.1)
    
    # Elegant gradient background
    for i in range(title_height):
        gray = int(250 - (i * 0.1))
        draw.line([(0, i), (width, i)], fill=(gray, gray, gray))
    
    # Title text
    title_text = garment_id.upper().replace('_', ' ')
    try:
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
    except:
        title_width = len(title_text) * 50
    title_x = (width - title_width) // 2
    draw.text((title_x, 30), title_text, fill='#1a1a1a', font=title_font)
    
    # Images section (70% of page)
    images_top = title_height + 20
    images_height = int(height * 0.7)
    
    # Calculate image sizes (LARGE!)
    margin = 50
    spacing = 40
    img_width = (width - (2 * margin) - (2 * spacing)) // 3
    img_height = images_height - 150
    
    # Position images
    y_pos = images_top
    x_positions = [
        margin,
        margin + img_width + spacing,
        margin + 2 * (img_width + spacing)
    ]
    
    labels = ['FRONT', 'BACK', 'DETAIL']
    views = ['front', 'back', 'design']
    
    for idx, (view, x_pos, label) in enumerate(zip(views, x_positions, labels)):
        if view in images_dict:
            # Load image
            img = Image.open(images_dict[view])
            
            # Resize maintaining aspect ratio (NO CROPPING)
            img.thumbnail((img_width, img_height), Image.Resampling.LANCZOS)
            
            # Center image
            img_x = x_pos + (img_width - img.width) // 2
            img_y = y_pos + (img_height - img.height) // 2
            
            # Paste image
            layout.paste(img, (img_x, img_y))
            
            # Label below image
            label_y = y_pos + img_height + 20
            try:
                label_bbox = draw.textbbox((0, 0), label, font=label_font)
                label_width = label_bbox[2] - label_bbox[0]
            except:
                label_width = len(label) * 30
            label_x = x_pos + (img_width - label_width) // 2
            draw.text((label_x, label_y), label, fill='#333333', font=label_font)
    
    # Description section (bottom 20%)
    desc_top = images_top + images_height + 100
    desc_height = height - desc_top - margin
    
    # Description box
    box_margin = 80
    draw.rectangle(
        [(box_margin, desc_top), (width - box_margin, desc_top + desc_height)],
        outline='#cccccc',
        width=3
    )
    
    # Subtle background gradient
    for i in range(desc_height):
        gray = 252 - int(i * 0.01)
        draw.line(
            [(box_margin, desc_top + i), (width - box_margin, desc_top + i)],
            fill=(gray, gray, gray)
        )
    
    # Description title
    draw.text((box_margin + 30, desc_top + 20), 
              "PRODUCT DESCRIPTION", 
              fill='#444444', 
              font=label_font)
    
    # Separator line
    draw.line(
        [(box_margin + 30, desc_top + 90), (width - box_margin - 30, desc_top + 90)],
        fill='#999999',
        width=2
    )
    
    # Word wrap description
    words = description.split()
    lines = []
    current_line = []
    max_width = width - (2 * box_margin) - 100
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        try:
            bbox = draw.textbbox((0, 0), test_line, font=desc_font)
            line_width = bbox[2] - bbox[0]
        except:
            line_width = len(test_line) * 25
            
        if line_width > max_width:
            current_line.pop()
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw description
    text_y = desc_top + 120
    for line in lines[:3]:
        draw.text((box_margin + 30, text_y), line, fill='#1a1a1a', font=desc_font)
        text_y += 70
    
    return layout

# ============== AI DESCRIPTION ==============
def generate_description(model, images_dict):
    """Generate AI product description"""
    prompt = """You are a professional fashion copywriter for a premium garment catalog.

Write a compelling 2-3 sentence product description that includes:
- Fabric type and quality
- Design style and special features
- Perfect occasion or styling tip

Make it sound premium and attractive to buyers. No markdown."""
    
    images_to_send = []
    for view in ['front', 'design', 'back', 'label']:
        if view in images_dict:
            try:
                img = Image.open(images_dict[view])
                images_to_send.append(img)
            except:
                pass
    
    if not images_to_send:
        return "Premium quality garment featuring elegant design. Perfect for any occasion with superior comfort and style."
    
    try:
        response = model.generate_content([prompt] + images_to_send)
        description = response.text.strip()
        return description
    except Exception as e:
        print(f"  ⚠ AI description failed: {e}")
        return "Premium quality garment featuring elegant design and superior craftsmanship. Perfect for any occasion with exceptional comfort and timeless style."

# ============== PDF GENERATION ==============
def create_pdf_fullpage(layout_pages):
    """Create PDF with full-page layouts"""
    c = canvas.Canvas(FINAL_PDF, pagesize=A4)
    page_width, page_height = A4
    
    for layout_path in layout_pages:
        img_reader = ImageReader(layout_path)
        
        # Draw at full A4 size
        c.drawImage(img_reader, 0, 0, 
                   width=page_width, 
                   height=page_height,
                   preserveAspectRatio=True)
        
        c.showPage()
    
    c.save()
    print(f"✓ PDF created: {FINAL_PDF}")

# ============== MAIN WORKFLOW ==============
def main():
    """Main workflow"""
    print("="*80)
    print("GARMENT CATALOG - PROFESSIONAL STUDIO QUALITY EDITION")
    print("="*80)
    
    # Setup
    print("\n[1/5] Setting up...")
    setup_folders()
    model = setup_gemini()
    
    # Organize
    print("\n[2/5] Organizing images...")
    garments = organize_images(INPUT_FOLDER)
    
    if not garments:
        print("❌ No images found!")
        print("   Place images in input_images/ folder")
        print("   Name them: garment_001_front.jpg, garment_001_back.jpg, etc.")
        return
    
    # Process
    print("\n[3/5] Applying gentle professional enhancement...")
    layout_pages = []
    
    for idx, (garment_id, images) in enumerate(garments.items(), 1):
        print(f"\n{'='*80}")
        print(f"📦 Processing {garment_id} ({idx}/{len(garments)})")
        print(f"{'='*80}")
        
        # Enhance images
        enhanced_images = {}
        for view_type, image_path in images.items():
            enhanced_path = enhance_image_studio_quality(image_path, garment_id, view_type)
            enhanced_images[view_type] = enhanced_path
        
        # Generate description
        print(f"\n  📝 Generating AI description...")
        description = generate_description(model, enhanced_images)
        print(f"  ✅ Description generated")
        
        # Create layout
        print(f"\n  🎨 Creating full-page layout...")
        layout = create_fullpage_layout(garment_id, enhanced_images, description)
        layout_path = os.path.join(LAYOUT_FOLDER, f"{garment_id}_layout.jpg")
        layout.save(layout_path, quality=95, optimize=True, dpi=(300, 300))
        layout_pages.append(layout_path)
        
        print(f"  ✅ Layout complete!")
    
    # Generate PDF
    print(f"\n[4/5] Creating professional PDF catalog...")
    create_pdf_fullpage(layout_pages)
    
    # Complete
    print(f"\n[5/5] 🎉 SUCCESS!")
    print("="*80)
    print(f"✅ Processed {len(garments)} garments")
    print(f"✅ Gentle enhancements applied (natural look)")
    print(f"✅ White backgrounds created")
    print(f"✅ Smooth fabric appearance")
    print(f"✅ Full-page PDF layouts (no cropping)")
    print(f"✅ Final catalog ready: {FINAL_PDF}")
    print("="*80)
    print("\n💡 TIP: Check output/enhanced_studio_quality/ to see enhanced images")
    print("💡 TIP: Adjust BACKGROUND_THRESHOLD, WRINKLE_STRENGTH in script if needed")

if __name__ == "__main__":
    main()