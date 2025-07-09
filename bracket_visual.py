from PIL import Image, ImageDraw, ImageFont
import os

# Пути
BACKGROUND_PATH = "background.png"  # Заранее положи туда красивый фон в стиле Dota 2
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Или путь к своему шрифту
OUTPUT_PATH = "bracket.png"

# Настройки
BOX_WIDTH = 280
BOX_HEIGHT = 60
H_SPACING = 220
V_SPACING = 40
FONT_SIZE = 20
LINE_WIDTH = 4

def draw_match(draw, x, y, team1, team2, font):
    box1 = [x, y, x + BOX_WIDTH, y + BOX_HEIGHT]
    box2 = [x, y + BOX_HEIGHT + V_SPACING, x + BOX_WIDTH, y + 2 * BOX_HEIGHT + V_SPACING]
    draw.rectangle(box1, outline="white", width=2)
    draw.rectangle(box2, outline="white", width=2)
    draw.text((x + 10, y + 15), team1, font=font, fill="white")
    draw.text((x + 10, y + BOX_HEIGHT + V_SPACING + 15), team2, font=font, fill="white")

    mid_x = x + BOX_WIDTH
    mid_y1 = y + BOX_HEIGHT // 2
    mid_y2 = y + BOX_HEIGHT + V_SPACING + BOX_HEIGHT // 2
    mid_y = (mid_y1 + mid_y2) // 2
    draw.line([(mid_x, mid_y1), (mid_x + 30, mid_y)], fill="white", width=LINE_WIDTH)
    draw.line([(mid_x, mid_y2), (mid_x + 30, mid_y)], fill="white", width=LINE_WIDTH)

    return mid_x + 30, mid_y

def generate_bracket_image(bracket):
    if not os.path.exists(BACKGROUND_PATH):
        img = Image.new("RGB", (1600, 900), color=(10, 10, 10))
    else:
        img = Image.open(BACKGROUND_PATH).convert("RGBA")
        img = img.resize((1600, 900))

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()

    positions = {}
    start_x = 50
    start_y = 50

    for round_index, round_matches in enumerate(bracket):
        max_matches = len(round_matches)
        round_height = (2 * BOX_HEIGHT + V_SPACING) * max_matches + V_SPACING * (max_matches - 1)
        offset_y = (img.height - round_height) // 2
        current_x = start_x + round_index * (BOX_WIDTH + H_SPACING)

        for match_index, match in enumerate(round_matches):
            team1, team2 = match
            y = offset_y + match_index * (2 * BOX_HEIGHT + 2 * V_SPACING)
            mid_x, mid_y = draw_match(draw, current_x, y, team1, team2, font)
            positions[(round_index, match_index)] = (mid_x, mid_y)

            if round_index > 0:
                prev_match1 = positions.get((round_index - 1, match_index * 2))
                prev_match2 = positions.get((round_index - 1, match_index * 2 + 1))
                if prev_match1 and prev_match2:
                    px, py1 = prev_match1
                    _, py2 = prev_match2
                    draw.line([(px, py1), (current_x, mid_y)], fill="white", width=LINE_WIDTH)
                    draw.line([(px, py2), (current_x, mid_y)], fill="white", width=LINE_WIDTH)

    img.save(OUTPUT_PATH)
    return OUTPUT_PATH
