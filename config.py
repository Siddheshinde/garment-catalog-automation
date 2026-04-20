import os
from reportlab.lib.pagesizes import A4

# get your key from https://aistudio.google.com/app/apikey
# set it as an environment variable: set GEMINI_API_KEY=your_key_here
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

INPUT_FOLDER      = "input_images"
OUTPUT_FOLDER     = "output"
PROCESSED_FOLDER  = "output/processed_images"
LAYOUT_FOLDER     = "output/layout_pages"
FINAL_PDF         = "output/final_catalog.pdf"

IMAGE_WIDTH   = 600
IMAGE_HEIGHT  = 800
LAYOUT_WIDTH  = 2100
LAYOUT_HEIGHT = 1500

CONTRAST_FACTOR   = 1.2
BRIGHTNESS_FACTOR = 1.1
JPEG_QUALITY      = 95

BORDER_COLOR = "#cccccc"
BORDER_WIDTH = 2

BACKGROUND_COLOR       = "white"
TITLE_COLOR            = "black"
DESCRIPTION_BOX_COLOR  = "#f9f9f9"
DESCRIPTION_TEXT_COLOR = "black"

TITLE_FONT            = "arial.ttf"
TITLE_FONT_SIZE       = 60
DESCRIPTION_FONT      = "arial.ttf"
DESCRIPTION_FONT_SIZE = 32

TOP_MARGIN          = 50
SIDE_MARGIN         = 50
IMAGE_SPACING       = 150
DESCRIPTION_HEIGHT  = 200

AI_MODEL          = "gemini-1.5-flash"
DESCRIPTION_STYLE = "professional"

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
Keep it short and factual. No markdown.""",
}

MAX_DESCRIPTION_LENGTH = 500

PDF_PAGE_SIZE = A4
PDF_TITLE     = "Product Catalog"
PDF_AUTHOR    = "Your Business Name"
PDF_SUBJECT   = "Garment Collection"

GARMENT_PREFIX    = "garment"
ID_LENGTH         = 3
VALID_VIEW_TYPES  = ["front", "back", "design", "label"]

REMOVE_BACKGROUND = False

ADD_WATERMARK     = False
WATERMARK_PATH    = "watermark.png"
WATERMARK_OPACITY = 0.3

ADD_LOGO       = False
LOGO_PATH      = "company_logo.png"
LOGO_SIZE      = (200, 200)
LOGO_POSITION  = "top-right"

SKIP_MISSING_IMAGES = True
REQUIRE_LABEL_IMAGE = False
USE_MULTIPROCESSING = False
MAX_WORKERS         = 4

VERBOSE_OUTPUT = True
LOG_TO_FILE    = False
LOG_FILE       = "output/catalog_generation.log"
