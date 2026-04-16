"""
Test Single Image Enhancement - BALANCED VERSION
Natural-looking enhancement that doesn't overprocess
"""

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

# ADJUSTABLE SETTINGS - Change these to control enhancement strength
BACKGROUND_THRESHOLD = 170  # 150-200, lower = more whitening
WRINKLE_STRENGTH = 0.4      # 0.0-1.0, higher = more smoothing  
COLOR_BOOST = 1.15          # 1.0-1.5, higher = more vibrant
CONTRAST_BOOST = 1.15       # 1.0-1.5, higher = more dramatic
SHARPNESS = 1.3             # 1.0-2.0, higher = sharper

def make_background_white_gentle(img):
    """Gentle background whitening"""
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            avg = (r + g + b) / 3
            
            # Only whiten light pixels
            if avg > BACKGROUND_THRESHOLD:
                factor = (avg - BACKGROUND_THRESHOLD) / (255 - BACKGROUND_THRESHOLD)
                new_r = int(r + (255 - r) * factor)
                new_g = int(g + (255 - g) * factor)
                new_b = int(b + (255 - b) * factor)
                pixels[x, y] = (new_r, new_g, new_b)
    
    return img

def smooth_wrinkles_gentle(img):
    """Gentle wrinkle smoothing"""
    # Light smoothing only
    smoothed = img.filter(ImageFilter.SMOOTH)
    
    # Blend just a little (keeps fabric texture)
    img = Image.blend(img, smoothed, alpha=WRINKLE_STRENGTH)
    
    # Remove tiny imperfections
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # Restore sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(SHARPNESS)
    
    return img

def enhance_colors_natural(img):
    """Natural color enhancement"""
    # Gentle auto-contrast
    img = ImageOps.autocontrast(img, cutoff=1)
    
    # Subtle color boost
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(COLOR_BOOST)
    
    # Gentle contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(CONTRAST_BOOST)
    
    # Slight brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    
    return img

def enhance_image(input_path, output_path):
    """Full enhancement pipeline - BALANCED"""
    print(f"\nProcessing: {input_path}")
    print("="*60)
    
    img = Image.open(input_path)
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    print("Step 1: Whitening background (gentle)...")
    img = make_background_white_gentle(img)
    
    print("Step 2: Smoothing wrinkles (gentle)...")
    img = smooth_wrinkles_gentle(img)
    
    print("Step 3: Enhancing colors (natural)...")
    img = enhance_colors_natural(img)
    
    print("Step 4: Final polish...")
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.1)
    
    print(f"Saving: {output_path}")
    img.save(output_path, quality=95, optimize=True)
    
    print("\n" + "="*60)
    print("✅ Done! Compare the images:")
    print(f"   Original: {input_path}")
    print(f"   Enhanced: {output_path}")
    print("="*60)
    print("\n💡 ADJUSTMENT TIPS:")
    print("   • Still too strong? Decrease COLOR_BOOST and CONTRAST_BOOST")
    print("   • Not white enough? Decrease BACKGROUND_THRESHOLD (try 160)")
    print("   • Still wrinkled? Increase WRINKLE_STRENGTH (try 0.5-0.6)")
    print("   • Looks blurry? Increase SHARPNESS (try 1.5)")

if __name__ == "__main__":
    # CHANGE THIS TO YOUR IMAGE PATH
    input_image = "input_images/garment_001_front.jpg"
    output_image = "test_enhanced_balanced.jpg"
    
    try:
        enhance_image(input_image, output_image)
    except FileNotFoundError:
        print(f"\n❌ Error: Could not find {input_image}")
        print("   Please update the 'input_image' path in the script")
    except Exception as e:
        print(f"\n❌ Error: {e}")