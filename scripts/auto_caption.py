"""
自动配文系统 v0.1
用画面局部像素方差，自动找出"最安静"(最适合放文字)的区域，
不再依赖人眼判断——这是让 typography-spec.md 从"文档"变成"可执行系统"的第一步。

局限性在脚本末尾诚实列出，不夸大能力。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_LIGHT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Light.ttc"


def find_quiet_region(img, block=40, margin_frac=0.08, avoid_center_penalty=1.6):
    """
    把画面切成网格，计算每块的像素标准差(方差)作为"忙碌度"评分。
    方差低 = 大片留白/纯色；方差高 = 主体/网点密集区。
    返回评分最低（最安静）、且不在画面正中央、不贴边的区域坐标。
    """
    gray = np.array(img.convert("L"), dtype=np.float32)
    h, w = gray.shape
    margin = int(min(w, h) * margin_frac)

    best_score = None
    best_xy = None

    cx, cy = w / 2, h / 2
    max_dist = ((w / 2) ** 2 + (h / 2) ** 2) ** 0.5

    for y in range(margin, h - margin - block, block // 2):
        for x in range(margin, w - margin - block, block // 2):
            patch = gray[y:y + block * 3, x:x + block * 6]  # 给文字留够横向空间的采样窗
            if patch.size == 0:
                continue
            variance = float(np.std(patch))

            # 离中心越近，惩罚越重——避免文字堆在画面正中央压主体
            dist_to_center = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            center_penalty = (1 - dist_to_center / max_dist) * avoid_center_penalty

            score = variance + center_penalty * 10  # variance 权重需要和 penalty 同量级

            if best_score is None or score < best_score:
                best_score = score
                best_xy = (x, y)

    return best_xy, best_score


def sample_local_color(img, xy, block=60):
    x, y = xy
    region = img.crop((x, y, x + block, y + block))
    arr = np.array(region).reshape(-1, 3)
    return tuple(int(v) for v in arr.mean(axis=0))


def pick_text_color(bg_rgb, ink_rgb, mist_rgb):
    """在 Ink 和 Mist 两个候选色里，选和背景亮度对比更大的那个，保证可读性"""
    def luminance(rgb):
        r, g, b = rgb
        return 0.299 * r + 0.587 * g + 0.114 * b

    bg_lum = luminance(bg_rgb)
    ink_contrast = abs(luminance(ink_rgb) - bg_lum)
    mist_contrast = abs(luminance(mist_rgb) - bg_lum)
    return ink_rgb if ink_contrast > mist_contrast else mist_rgb


def draw_tracked_text(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    cur_x = x
    for ch in text:
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0]
        draw.text((cur_x, y), ch, font=font, fill=fill)
        cur_x += w + tracking
    return cur_x - x


def draw_vertical_text(draw, xy, text, font, fill, tracking=0):
    x, y = xy
    cur_y = y
    for ch in text:
        bbox = font.getbbox(ch)
        ch_h = bbox[3] - bbox[1]
        draw.text((x, cur_y), ch, font=font, fill=fill)
        cur_y += ch_h + tracking
    return cur_y - y


def text_block_size(text, font, tracking=0, orientation="horizontal"):
    """估算文字块的宽高，用于判断安静区域够不够放、以及自动选横竖排"""
    sizes = [font.getbbox(ch) for ch in text]
    if orientation == "horizontal":
        total = sum(b[2] - b[0] for b in sizes) + tracking * (len(text) - 1)
        return total, font.size
    else:
        total = sum(b[3] - b[1] for b in sizes) + tracking * (len(text) - 1)
        return font.size, total


def choose_orientation(region_w, region_h, text, font, tracking):
    """
    自动选横排还是竖排：分别估算两种排法需要的空间，
    选择能被安静区域完整容纳、且更贴合该区域长宽比的一种。
    横排优先（更符合默认阅读习惯），只有安静区域明显偏纵长、
    横排放不下时才切竖排。
    """
    h_w, h_h = text_block_size(text, font, tracking, "horizontal")
    v_w, v_h = text_block_size(text, font, tracking, "vertical")

    h_fits = h_w <= region_w and h_h <= region_h
    v_fits = v_w <= region_w and v_h <= region_h

    if h_fits and not v_fits:
        return "horizontal"
    if v_fits and not h_fits:
        return "vertical"
    if not h_fits and not v_fits:
        # 两种都放不下，说明这个区域太小或字号太大，返回横排让上层逻辑决定是否报错/缩字号
        return "horizontal"

    # 两种都放得下：安静区域的长宽比明显偏纵长（高远大于宽）时选竖排，否则横排
    if region_h > region_w * 1.8:
        return "vertical"
    return "horizontal"


def auto_caption(image_path, text, ink_rgb, mist_rgb, output_path, font_size_frac=0.026):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    margin = int(min(w, h) * 0.08)

    xy, score = find_quiet_region(img)
    if xy is None:
        raise RuntimeError("没找到足够安静的区域，这张图可能留白不够，不适合自动配文")

    bg_color = sample_local_color(img, xy)
    text_color = pick_text_color(bg_color, ink_rgb, mist_rgb)

    font_size = int(w * font_size_frac)
    font = ImageFont.truetype(FONT_LIGHT, font_size)
    tracking_h = int(font_size * 0.5)   # 横排字距更宽，编辑感更强
    tracking_v = int(font_size * 0.35)  # 竖排字距略窄，避免拉得过长

    # 估算从选中点到画面边缘（减去安全边距）还有多少可用空间，用来判断横竖排哪个装得下
    x, y = xy
    region_w = (w - margin) - x
    region_h = (h - margin) - y

    orientation = choose_orientation(region_w, region_h, text, font, tracking_h)

    draw = ImageDraw.Draw(img)
    if orientation == "vertical":
        draw_vertical_text(draw, xy, text, font, text_color, tracking=tracking_v)
    else:
        draw_tracked_text(draw, xy, text, font, text_color, tracking=tracking_h)

    img.save(output_path)
    return xy, bg_color, text_color, orientation


if __name__ == "__main__":
    # 测试一：河灯图，安静区域偏横向，预期自动选横排
    result1 = auto_caption(
        "/home/claude/indigo-riso-poster/assets/examples/07-vertical-river-lanterns.png",
        "每盏灯都在往看不见的地方去",
        ink_rgb=(237, 228, 208),
        mist_rgb=(90, 123, 168),
        output_path="/home/claude/indigo-riso-poster/assets/examples/demo-auto-h.png",
    )
    print("河灯图 -> 位置:", result1[0], "文字色:", result1[2], "排版:", result1[3])

    # 测试二：裂痕图，找一个偏纵长的安静区域，预期可能触发竖排
    result2 = auto_caption(
        "/home/claude/indigo-riso-poster/assets/examples/03-organic-crack-ice.png",
        "冰还没碎但已经决定了往哪个方向碎",
        ink_rgb=(237, 228, 208),
        mist_rgb=(90, 123, 168),
        output_path="/home/claude/indigo-riso-poster/assets/examples/demo-auto-v.png",
    )
    print("裂痕图 -> 位置:", result2[0], "文字色:", result2[2], "排版:", result2[3])
