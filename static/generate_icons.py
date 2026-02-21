"""
Generate PWA icons for CampusBite
Run: python generate_icons.py
Requires: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont

def create_icon(size):
    """Create CampusBite icon with deck color theme"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factor
    s = size / 512

    corner_radius = int(108 * s)

    # Background: forest green from deck (#2d6a4f)
    bg_color = (45, 106, 79)  # #2d6a4f

    # Draw rounded rectangle background
    draw.rounded_rectangle(
        [(0, 0), (size-1, size-1)],
        radius=corner_radius,
        fill=bg_color
    )

    # Fork elements in white
    white = (255, 255, 255)

    # Fork tines (4 vertical bars)
    tine_width = int(24 * s)
    tine_height = int(120 * s)
    tine_radius = int(12 * s)
    tine_y = int(92 * s)

    tine_positions = [172, 212, 276, 316]
    for x in tine_positions:
        x_scaled = int(x * s)
        draw.rounded_rectangle(
            [(x_scaled, tine_y), (x_scaled + tine_width, tine_y + tine_height)],
            radius=tine_radius,
            fill=white
        )

    # Fork base (horizontal bar connecting tines)
    base_y = int(188 * s)
    base_height = int(48 * s)
    draw.rounded_rectangle(
        [(int(172 * s), base_y), (int(340 * s), base_y + base_height)],
        radius=int(24 * s),
        fill=white
    )

    # Connector piece
    conn_y = int(212 * s)
    conn_height = int(80 * s)
    draw.rounded_rectangle(
        [(int(220 * s), conn_y), (int(292 * s), conn_y + conn_height)],
        radius=int(24 * s),
        fill=white
    )

    # Fork handle
    handle_x = int(232 * s)
    handle_y = int(280 * s)
    handle_width = int(48 * s)
    handle_height = int(140 * s)
    draw.rounded_rectangle(
        [(handle_x, handle_y), (handle_x + handle_width, handle_y + handle_height)],
        radius=int(24 * s),
        fill=white
    )

    # Small coral accent dot at bottom of handle
    coral = (232, 93, 4)  # #e85d04
    dot_x = int(256 * s)
    dot_y = int(400 * s)
    dot_r = int(16 * s)
    draw.ellipse(
        [(dot_x - dot_r, dot_y - dot_r), (dot_x + dot_r, dot_y + dot_r)],
        fill=coral
    )

    return img

def main():
    sizes = {
        'icon-180.png': 180,  # iOS
        'icon-192.png': 192,  # Android
        'icon-512.png': 512,  # Splash/Store
    }

    for filename, size in sizes.items():
        print(f"Generating {filename} ({size}x{size})...")
        icon = create_icon(size)
        icon.save(filename, 'PNG')
        print(f"  Saved {filename}")

    print("\nDone! Icons generated successfully.")

if __name__ == '__main__':
    main()
