"""Create a distinctive coding AI agent icon for GLM Code."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 PNG icon
size = 256
image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw a dark gradient background
for i in range(size):
    r = int(10 + (30 - 10) * i / size)
    g = int(12 + (20 - 12) * i / size)
    b = int(18 + (40 - 18) * i / size)
    draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b, 255))

center = size // 2

# Draw stylized code brackets < > with AI elements
bracket_size = 70
thickness = 20

# Left bracket
draw.rectangle(
    [(center - bracket_size - 12, center - bracket_size),
     (center - 5, center + bracket_size)],
    fill=(0, 220, 255, 255),
    outline=(0, 255, 255, 255),
    width=6
)

# Right bracket
draw.rectangle(
    [(center + 5, center - bracket_size),
     (center + bracket_size + 12, center + bracket_size)],
    fill=(0, 220, 255, 255),
    outline=(0, 255, 255, 255),
    width=6
)

# Draw a lightning bolt in the center (AI + speed)
bolt_points = [
    (center - 10, center - 50),
    (center + 5, center - 50),
    (center - 2, center - 10),
    (center + 15, center - 10),
    (center + 2, center + 20),
    (center + 10, center + 50),
    (center - 8, center + 50),
    (center + 0, center + 20),
    (center - 15, center + 20),
]
draw.polygon(bolt_points, fill=(255, 200, 0, 255), outline=(255, 220, 50, 255), width=4)

# Draw a neural network pattern
neural_radius = 50
for i in range(3):
    y_offset = (i - 1) * 35
    draw.ellipse(
        [(center - neural_radius, center + y_offset - 15),
         (center + neural_radius, center + y_offset + 15)],
        fill=(0, 180, 255, 100),
        outline=(0, 200, 255, 150),
        width=2
    )
    draw.line(
        [(center, center + y_offset - 15), (center, center + y_offset + 15)],
        fill=(0, 180, 255, 80),
        width=2
    )

# Draw "GLM" text
try:
    font_paths = [
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf",
    ]
    font = None
    for fp in font_paths:
        if Path(fp).exists():
            font = ImageFont.truetype(fp, 44)
            break
    if not font:
        font = ImageFont.load_default()
except:
    font = ImageFont.load_default()

text = "GLM"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
draw.text(
    ((size - text_width) // 2, (size - text_height) // 2),
    text,
    fill=(255, 255, 255, 255),
    font=font
)

# Save as PNG
icon_path = Path(__file__).parent / "glmcode" / "gui" / "app_icon.png"
icon_path.parent.mkdir(parents=True, exist_ok=True)
image.save(icon_path, "PNG")
print(f"Icon created: {icon_path}")
print(f"File size: {icon_path.stat().st_size} bytes")
print("[OK] Icon is now available in the desktop app!")