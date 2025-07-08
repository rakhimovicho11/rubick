from PIL import Image, ImageDraw, ImageFont
import os

WIDTH = 1200
HEIGHT = 700
LINE_COLOR = (255, 255, 255)
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)
FONT_PATH = "arial.ttf"  # или путь к другому шрифту
FONT_SIZE = 16

# Пример данных
example_bracket = [
    # Раунд 1
    [("Team A", "Team B"), ("Team C", "Team D"),
     ("Team E", "Team F"), ("Team G", "Team H"),
     ("Team I", "Team J"), ("Team K", "Team L"),
     ("Team M", "Team N"), ("Team O", "Team P")]
]

def generate_bracket_image(bracket, output_path="bracket.png"):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    round_x_spacing = WIDTH // (len(bracket) + 1)
    start_y = 50
    match_height = 40
    vertical_spacing = 40

    for rnd_idx, round_matches in enumerate(bracket):
        x = (rnd_idx + 1) * round_x_spacing
        for match_idx, (team1, team2) in enumerate(round_matches):
            y = start_y + match_idx * (match_height * 2 + vertical_spacing)
            draw.text((x, y), f"{team1}", fill=TEXT_COLOR, font=font)
            draw.text((x, y + match_height), f"{team2}", fill=TEXT_COLOR, font=font)
            # Соединительные линии
            draw.line([(x - 20, y + match_height // 2), (x, y + match_height // 2)], fill=LINE_COLOR)
            draw.line([(x - 20, y + match_height + match_height // 2), (x, y + match_height + match_height // 2)], fill=LINE_COLOR)
            draw.line([(x - 20, y + match_height // 2), (x - 20, y + match_height + match_height // 2)], fill=LINE_COLOR)

    img.save(output_path)
    print(f"✅ Сетка сохранена как {output_path}")

if __name__ == "__main__":
    generate_bracket_image(example_bracket)
