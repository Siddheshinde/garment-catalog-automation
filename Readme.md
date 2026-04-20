# Garment Catalog Studio — Desktop App

A professional PyQt6 desktop application for generating garment catalog PDFs.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python main.py
```

## File Structure

```
catalog_app/
├── main.py              # Entry point — run this
├── ui_main.py           # Main window, sidebar, work area
├── widgets.py           # ImageUploadBox, GarmentPageCard, StyledLineEdit
├── backend_wrapper.py   # Bridge to your catalog_automation.py backend
├── requirements.txt
│
├── temp_uploads/        # Auto-created — staged images
└── output/              # Auto-created — final PDFs
```

## Plugging In Your Backend

1. Copy `catalog_automation.py` into the `catalog_app/` folder.
2. Open `backend_wrapper.py`.
3. In `generate_catalog()`, uncomment the block labelled
   `# ┌─ UNCOMMENT & ADAPT when plugging in your backend`.
4. Remove (or comment out) the `_stub_generate(pages)` call below it.

The wrapper already:
- Stages uploaded images into the folder layout your backend expects  
  (`garment_001_front.jpg`, `garment_001_back.jpg`, …)
- Passes style / fabric / GSM overrides via `backend._PAGE_DETAILS`

## Workflow

1. Enter an optional catalog title in the top bar.
2. For each garment, click the **＋** boxes to upload Front / Back / Fabric Closeup photos.
3. Fill in Style No, Fabric composition, and GSM.
4. Click **＋ Add Garment** to add more pages.
5. Click **⬇ Generate PDF** — the catalog is built in the background.
6. Use **Open PDF** or **Show in Folder** from the success dialog.

## Future Extensions (ready hooks)

- **Drag & drop**: subclass `ImageUploadBox.dragEnterEvent` / `dropEvent`
- **Rotation slider**: add a `QSlider` to `GarmentPageCard`; pass angle into `_stage_images_for_backend`
- **Preview page**: add a `QDialog` that renders the layout PNG before PDF export