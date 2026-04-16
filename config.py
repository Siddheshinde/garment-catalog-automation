"""
Configuration file for Garment Catalog Automation
Edit these settings to customize your catalog
"""

# ============== API CONFIGURATION ==============
# Get your free API key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "AIzaSyAekIcAC_3CJYE2T9_Fbg4P1vjkztL-prA"

# Alternative: Use environment variable (recommended for security)
# import os
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')


# ============== FOLDER PATHS ==============
INPUT_FOLDER = "input_images"              # Where you put raw photos
OUTPUT_FOLDER = "output"                   # Where processed files go
PROCESSED_FOLDER = "output/processed_images"
LAYOUT_FOLDER = "output/layout_pages"
FINAL_PDF = "output/final_catalog.pdf"     # Final catalog name


# ============== IMAGE DIMENSIONS ==============
# Individual image sizes (in pixels)
IMAGE_WIDTH = 600                          # Width of each product photo
IMAGE_HEIGHT = 800                         # Height of each product photo

# Layout page dimensions
LAYOUT_WIDTH = 2100                        # Width of catalog page
LAYOUT_HEIGHT = 1500                       # Height of catalog page


# ============== IMAGE PROCESSING SETTINGS ==============
# Enhancement factors (1.0 = no change, >1.0 = increase, <1.0 = decrease)
CONTRAST_FACTOR = 1.2                      # Image contrast (1.0 - 2.0)
BRIGHTNESS_FACTOR = 1.1                    # Image brightness (0.8 - 1.3)

# Image quality
JPEG_QUALITY = 95                          # JPEG compression (1-100, higher = better)

# Border settings
BORDER_COLOR = '#cccccc'                   # Border color (hex code)
BORDER_WIDTH = 2                           # Border thickness in pixels


# ============== LAYOUT CUSTOMIZATION ==============
# Colors (use hex codes)
BACKGROUND_COLOR = 'white'                 # Layout background
TITLE_COLOR = 'black'                      # Product title color
DESCRIPTION_BOX_COLOR = '#f9f9f9'         # Description background
DESCRIPTION_TEXT_COLOR = 'black'           # Description text color

# Fonts (system fonts or paths to TTF files)
TITLE_FONT = "arial.ttf"                   # Font for titles
TITLE_FONT_SIZE = 60                       # Title font size
DESCRIPTION_FONT = "arial.ttf"             # Font for descriptions
DESCRIPTION_FONT_SIZE = 32                 # Description font size

# Layout spacing
TOP_MARGIN = 50                            # Space from top
SIDE_MARGIN = 50                           # Space from sides
IMAGE_SPACING = 150                        # Space between images
DESCRIPTION_HEIGHT = 200                   # Height of description box


# ============== AI DESCRIPTION SETTINGS ==============
# Gemini model to use
AI_MODEL = "gemini-1.5-flash"              # Options: gemini-1.5-flash, gemini-1.5-pro

# Description style
DESCRIPTION_STYLE = "professional"         # Options: professional, casual, luxury, minimal

# Custom prompts for different styles
AI_PROMPTS = {
    "professional": """You are a professional fashion copywriter for a garment catalog.
    
Based on the images provided, write a concise 2-3 sentence product description that includes:
- Fabric type and material composition (if visible on label)
- Design style, patterns, or notable features
- Key selling points (comfort, style, occasion)
- Size information (if visible)

Keep it professional, engaging, and suitable for a sales catalog.
Do not use markdown or special formatting.""",
    
    "luxury": """You are a luxury fashion copywriter for high-end clientele.
    
Based on the images, craft an elegant 2-3 sentence description that emphasizes:
- Premium quality and craftsmanship
- Sophisticated design elements
- Exclusive appeal and refinement
- Fabric luxury and texture

Use elevated language. Avoid markdown.""",
    
    "casual": """You are writing product descriptions for an online boutique.
    
Based on the images, write a friendly 2-3 sentence description:
- What makes this piece special
- The vibe/style it gives
- Perfect occasions to wear it
- Fabric and fit info

Keep it conversational and relatable. No markdown.""",
    
    "minimal": """Based on the images, write a brief 1-2 sentence description:
- Fabric type
- Key feature
Keep it short and factual. No markdown."""
}

# Maximum description length (in characters)
MAX_DESCRIPTION_LENGTH = 500


# ============== PDF SETTINGS ==============
# Page size options: A4, LETTER, LEGAL
from reportlab.lib.pagesizes import A4, LETTER, LEGAL
PDF_PAGE_SIZE = A4                         # Standard paper size

# PDF metadata
PDF_TITLE = "Product Catalog"              # PDF document title
PDF_AUTHOR = "Your Business Name"          # PDF author
PDF_SUBJECT = "Garment Collection"         # PDF subject


# ============== NAMING CONVENTION ==============
# Expected image naming pattern
# Default: garment_001_front.jpg, garment_001_back.jpg, etc.
GARMENT_PREFIX = "garment"                 # First part of filename
ID_LENGTH = 3                              # Number of digits in ID (001, 002, etc.)
VALID_VIEW_TYPES = ['front', 'back', 'design', 'label']  # Required photo types


# ============== OPTIONAL FEATURES ==============
# Background removal (requires 'rembg' package)
REMOVE_BACKGROUND = False                  # True/False

# Add watermark (set path to your watermark image)
ADD_WATERMARK = False
WATERMARK_PATH = "watermark.png"
WATERMARK_OPACITY = 0.3                    # 0.0 (invisible) to 1.0 (opaque)

# Add company logo
ADD_LOGO = False
LOGO_PATH = "company_logo.png"
LOGO_SIZE = (200, 200)                     # Width, Height in pixels
LOGO_POSITION = "top-right"                # Options: top-left, top-right, bottom-left, bottom-right


# ============== ADVANCED SETTINGS ==============
# Error handling
SKIP_MISSING_IMAGES = True                 # Continue if some images are missing
REQUIRE_LABEL_IMAGE = False                # Make label image optional

# Processing options
USE_MULTIPROCESSING = False                # Speed up with parallel processing (advanced)
MAX_WORKERS = 4                            # Number of parallel workers

# Logging
VERBOSE_OUTPUT = True                      # Show detailed progress
LOG_TO_FILE = False                        # Save log to file
LOG_FILE = "output/catalog_generation.log"


# ============== VALIDATION ==============
def validate_config():
    """Check if configuration is valid"""
    errors = []
    
    if GEMINI_API_KEY == "AIzaSyAekIcAC_3CJYE2T9_Fbg4P1vjkztL-prA":
        errors.append("Please set your Gemini API key!")
    
    if IMAGE_WIDTH <= 0 or IMAGE_HEIGHT <= 0:
        errors.append("Image dimensions must be positive!")
    
    if JPEG_QUALITY < 1 or JPEG_QUALITY > 100:
        errors.append("JPEG quality must be between 1 and 100!")
    
    if DESCRIPTION_STYLE not in AI_PROMPTS:
        errors.append(f"Invalid description style: {DESCRIPTION_STYLE}")
    
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True


# Run validation when imported
if __name__ != "__main__":
    validate_config()