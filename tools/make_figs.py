"""重點卡示意圖：產生 app/fig/*.svg（自繪示意，非官方圖）。

python -I tools/make_figs.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "fig"

INK, BRAND, HEAT, UV, RESIN, POWDER, PART, BED, GOOD, BAD, GRAY = (
    "#2d2a26", "#d9673b", "#e04b3a", "#7b5cff", "#f4c25a", "#e3d5b8", "#4f86e8", "#8f969c", "#2f9e5b", "#d63b3b", "#b8b2aa")


def svg(w, h, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="Microsoft JhengHei,PingFang TC,Noto Sans TC,sans-serif" font-size="14">
<defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{INK}"/></marker>
<marker id="u" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{UV}"/></marker></defs>
<rect width="{w}" height="{h}" fill="#fff"/>
{body}
</svg>
'''


def t(x, y, s, size=14, anchor="start", color=INK, bold=False):
    weight = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}"{weight}>{s}</text>'


def line(x1, y1, x2, y2, color=INK, w=1.5, arrow=False, dash=None, marker="a"):
    extra = f' marker-end="url(#{marker})"' if arrow else ""
    extra += f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{extra}/>'


def rect(x, y, w, h, fill="none", stroke=INK, sw=1.5, rx=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" rx="{rx}" {extra}/>'


def mark(x, y, ok):
    return t(x, y, "✓ 好" if ok else "✗ 不好", 16, "middle", GOOD if ok else BAD, True)


def nozzle(cx, top, heat_w=30):
    return (rect(cx - heat_w / 2, top, heat_w, 22, HEAT, INK, 1.2, 3)
            + f'<path d="M{cx-9} {top+22}H{cx+9}L{cx+3} {top+34}H{cx-3}Z" fill="#c9a227" stroke="{INK}" stroke-width="1.2"/>')


FIGS = {}

# ---------- 各技術原理 ----------
FIGS["fdm"] = svg(480, 250, "".join([
    f'<circle cx="62" cy="62" r="34" fill="#f6e3d8" stroke="{INK}" stroke-width="1.5"/><circle cx="62" cy="62" r="9" fill="#fff" stroke="{INK}"/>',
    f'<path d="M62 28C150 20 236 20 240 46" fill="none" stroke="{BRAND}" stroke-width="3"/>',
    line(240, 46, 240, 104, BRAND, 3),
    f'<circle cx="227" cy="74" r="11" fill="#ddd" stroke="{INK}"/><circle cx="253" cy="74" r="11" fill="#ddd" stroke="{INK}"/>',
    nozzle(240, 104),
    rect(120, 214, 260, 12, BED, INK, 1.2, 2),
    "".join(rect(170, y, 140, 8, "#f0a07f", INK, .8) for y in (206, 198, 190, 182, 174, 166, 158)),
    rect(170, 150, 66, 8, "#f0a07f", INK, .8),
    t(20, 118, "線材（塑膠線）"), t(272, 79, "送料齒輪（馬達推線）"),
    t(272, 120, "加熱塊：電阻加熱融化"), t(272, 145, "噴嘴擠出一條線"),
    t(388, 225, "熱床（平台）"),
    t(20, 245, "像熱熔膠槍。噴頭靠滑軌、皮帶、螺桿移動；沒有雷射。", 13, color="#7a7166"),
]))

FIGS["feed"] = svg(480, 250, "".join([
    t(120, 22, "近端送料（Direct）", 15, "middle", bold=True),
    line(120, 34, 120, 62, BRAND, 3),
    rect(92, 62, 56, 40, "#ddd", INK, 1.5, 4), t(120, 87, "馬達", 13, "middle"),
    nozzle(120, 102),
    t(120, 172, "馬達就在噴頭上", 13, "middle"), t(120, 192, "✓ 回抽準、推力好", 13, "middle", GOOD),
    t(120, 212, "✓ 軟料 TPU 推得動", 13, "middle", GOOD), t(120, 232, "△ 噴頭重、慣性大", 13, "middle", "#7a7166"),
    line(240, 14, 240, 236, GRAY, 1, dash="4 4"),
    t(360, 22, "遠端送料（Bowden）", 15, "middle", bold=True),
    rect(262, 46, 48, 40, "#ddd", INK, 1.5, 4), t(286, 71, "馬達", 13, "middle"),
    t(286, 104, "（裝在機架上）", 12, "middle", "#7a7166"),
    f'<path d="M310 66C380 40 420 60 410 102" fill="none" stroke="#9cc3e6" stroke-width="7"/>',
    f'<path d="M310 66C380 40 420 60 410 102" fill="none" stroke="{BRAND}" stroke-width="2"/>',
    t(392, 46, "長管子", 12),
    nozzle(410, 102, 24),
    t(360, 172, "線穿過長管才到噴頭", 13, "middle"), t(360, 192, "✓ 噴頭輕", 13, "middle", GOOD),
    t(360, 212, "✗ 摩擦大、回抽不準", 13, "middle", BAD), t(360, 232, "✗ 軟料會卡住", 13, "middle", BAD),
]))

def powder_bed(x, y, w, h, part):
    dots = "".join(f'<circle cx="{x+6+i*9+(j%2)*4}" cy="{y+5+j*8}" r="2" fill="#c8b48e"/>'
                   for j in range(int(h // 8)) for i in range(int((w - 10) // 9)))
    px, py, pw, ph = part
    return rect(x, y, w, h, POWDER, INK, 1.5) + dots + rect(px, py, pw, ph, BRAND, INK, 1.2)


FIGS["pbf"] = svg(480, 260, "".join([
    powder_bed(110, 140, 260, 84, (195, 170, 90, 54)),
    rect(110, 224, 260, 10, BED, INK, 1.2), line(240, 238, 240, 256, INK, 1.5, True), t(250, 254, "平台每層下降一點", 12),
    rect(30, 30, 80, 30, "#ddd", INK, 1.5, 4), t(70, 50, "雷射", 13, "middle"),
    line(110, 45, 236, 45, HEAT, 2.5), f'<rect x="230" y="36" width="16" height="18" fill="#cfd8e3" stroke="{INK}" transform="rotate(45 238 45)"/>',
    line(238, 52, 225, 168, HEAT, 2.5), f'<circle cx="225" cy="170" r="5" fill="#ffcf4a" stroke="{HEAT}"/>',
    t(252, 40, "反射鏡掃描", 12),
    f'<circle cx="392" cy="130" r="10" fill="#ddd" stroke="{INK}"/>', line(378, 116, 330, 116, INK, 1.5, True),
    t(330, 112, "鋪粉滾輪／刮刀", 12),
    t(120, 132, "粉床", 13), t(240, 202, "成品", 13, "middle", "#fff", True),
    t(10, 20, "① 鋪一層粉 → ② 燒熔 → ③ 下降、再鋪", 13),
    t(300, 72, "金屬 SLM：充氬／氮氣", 12, color="#7a7166"), t(300, 88, "電子束 EBM：要真空", 12, color="#7a7166"),
    t(10, 250, "塑膠粉 SLS：周圍粉可當支撐", 12, color="#7a7166"),
]))

FIGS["bjt"] = svg(480, 250, "".join([
    powder_bed(110, 130, 260, 90, (170, 150, 120, 50)),
    rect(110, 220, 260, 10, BED, INK, 1.2),
    rect(190, 40, 100, 32, "#ddd", INK, 1.5, 4), t(240, 61, "噴頭", 13, "middle"),
    "".join(f'<circle cx="{205+i*14}" cy="{90+(i%2)*14}" r="4" fill="{PART}"/>' for i in range(6)),
    t(300, 62, "噴「液體膠水」黏住粉", 13), t(120, 122, "粉床（石膏／金屬／陶瓷粉）", 12),
    t(230, 180, "成品", 13, "middle", "#fff", True),
    t(20, 246, "模型埋在粉裡 → 粉就是支撐，不用另外加。金屬件之後要再燒結才夠強。", 13, color="#7a7166"),
]))

FIGS["mjt"] = svg(480, 240, "".join([
    rect(150, 36, 110, 32, "#ddd", INK, 1.5, 4), t(205, 57, "噴頭", 13, "middle"),
    "".join(f'<circle cx="{164+i*14}" cy="{84+(i%2)*12}" r="4" fill="{BRAND}"/>' for i in range(7)),
    rect(272, 36, 60, 26, "#e9e3ff", UV, 1.5, 4), t(302, 54, "UV 燈", 12, "middle", UV),
    "".join(line(282 + i * 14, 64, 276 + i * 14, 120, UV, 1.5, True, marker="u") for i in range(3)),
    rect(150, 200, 220, 10, BED, INK, 1.2),
    "".join(rect(160, y, 160, 8, "#f0a07f", INK, .8) for y in (192, 184, 176, 168, 160, 152)),
    rect(320, 152, 40, 48, "#eee", GRAY, 1, extra='stroke-dasharray="3 3"'), rect(280, 136, 80, 16, "#f0a07f", INK, .8),
    t(366, 186, "支撐：蠟", 12), t(366, 202, "（加熱就掉）", 12),
    t(10, 230, "像噴墨印表機：噴一滴滴樹脂，UV 照硬。可彩色、軟硬混合；只能噴稀的液體。", 13, color="#7a7166"),
]))

FIGS["ded"] = svg(480, 262, "".join([
    f'<path d="M200 30H280L256 140H224Z" fill="#ddd" stroke="{INK}" stroke-width="1.5"/>',
    line(240, 20, 240, 172, HEAT, 3),
    line(206, 60, 236, 168, "#8a7a5a", 1.5, dash="2 4"), line(274, 60, 244, 168, "#8a7a5a", 1.5, dash="2 4"),
    f'<path d="M80 220Q240 190 400 220V236H80Z" fill="#b9c2cc" stroke="{INK}" stroke-width="1.5"/>',
    f'<path d="M150 208Q240 176 330 208Q240 190 150 208Z" fill="#f0a07f" stroke="{INK}"/>',
    f'<ellipse cx="240" cy="182" rx="16" ry="6" fill="#ffb02e" stroke="{HEAT}"/>',
    t(290, 34, "雷射／電子束／電弧"), t(292, 84, "送金屬粉（或金屬線）"), t(292, 104, "＋惰性氣體保護"),
    t(260, 170, "熔池", 13), t(84, 256, "原本的零件（可在舊件、曲面上補料）", 12),
    t(20, 150, "常裝在機械手臂上", 12, color="#7a7166"), t(20, 168, "WAAM（電弧熔絲）也是 DED", 12, color="#7a7166"),
]))

FIGS["clip"] = svg(480, 250, "".join([
    rect(100, 120, 280, 92, RESIN, INK, 1.5),
    rect(102, 196, 276, 12, "#fff6d8", "none", 0), t(388, 205, "死區（不會硬）", 12),
    rect(100, 208, 280, 8, "#bfe3ff", INK, 1.2), t(388, 222, "透氧窗", 12),
    rect(170, 40, 140, 12, BED, INK, 1.2), t(320, 50, "平台", 12),
    rect(200, 52, 80, 144, PART, INK, 1.2),
    line(300, 110, 300, 62, INK, 2, True), t(310, 80, "連續往上拉", 13), t(310, 98, "不用一層層撕開", 12, color="#7a7166"),
    "".join(line(170 + i * 35, 246, 170 + i * 35, 222, UV, 1.6, True, marker="u") for i in range(5)),
    t(20, 238, "光從下面照", 12, color=UV),
    t(20, 30, "氧氣從槽底透進來，讓最底一層樹脂「厭氧」不硬化 → 不黏槽底", 13, color="#7a7166"),
]))

# ---------- 光固化 ----------
def vat_layer(x, y, w):
    return rect(x, y, w, 14, RESIN, INK, 1.2)


FIGS["vpp-light"] = svg(480, 230, "".join([
    # SLA
    f'<circle cx="80" cy="30" r="8" fill="#ddd" stroke="{INK}"/>', line(80, 38, 60, 132, UV, 2),
    vat_layer(15, 132, 130),
    f'<path d="M25 139H55V136H25V142H60" fill="none" stroke="{PART}" stroke-width="2" stroke-dasharray="3 2"/>',
    f'<circle cx="60" cy="139" r="4" fill="{UV}"/>',
    t(80, 172, "SLA：雷射", 14, "middle", bold=True), t(80, 192, "一點一點描（點）", 13, "middle"),
    t(80, 212, "雙光子也是「點」", 12, "middle", "#7a7166"),
    # DLP
    rect(222, 18, 36, 24, "#ddd", INK, 1.5, 3), t(240, 34, "投影", 11, "middle"),
    f'<path d="M232 42L175 132H305L248 42Z" fill="{UV}" fill-opacity=".18" stroke="{UV}"/>',
    vat_layer(175, 132, 130),
    t(240, 172, "DLP：投影機", 14, "middle", bold=True), t(240, 192, "一次照整層（面）", 13, "middle"),
    t(240, 212, "投影會變形，要校正", 12, "middle", "#7a7166"),
    # LCD
    vat_layer(335, 40, 130),
    "".join(rect(339 + i * 16, 64, 14, 12, "#fff" if i in (2, 3, 4) else "#333", INK, .6) for i in range(8)),
    t(470, 74, "", 1),
    "".join(line(383 + i * 16, 112, 383 + i * 16, 58, UV, 1.6, True, marker="u") for i in range(3)),
    rect(345, 112, 110, 12, "#e9e3ff", UV, 1.2, 3), t(400, 140, "UV 燈", 12, "middle", UV),
    t(400, 172, "LCD：螢幕當遮罩", 14, "middle", bold=True), t(400, 192, "透光處才變硬（面）", 13, "middle"),
    t(400, 212, "沒有投影鏡頭的變形", 12, "middle", "#7a7166"),
]))

FIGS["vpp-updown"] = svg(480, 270, "".join([
    t(120, 20, "上照式（Top-down）", 15, "middle", bold=True),
    "".join(line(90 + i * 30, 30, 90 + i * 30, 66, UV, 1.6, True, marker="u") for i in range(3)),
    rect(40, 70, 160, 140, RESIN, INK, 1.5),
    rect(80, 98, 80, 40, PART, INK, 1.2), rect(70, 138, 100, 8, BED, INK, 1), line(120, 146, 120, 200, INK, 1.5),
    line(186, 110, 186, 150, INK, 2, True), t(120, 232, "光從上照，平台往下沉", 13, "middle"),
    t(120, 252, "槽要很深；不用撕開，適合大件", 12, "middle", "#7a7166"),
    line(240, 10, 240, 260, GRAY, 1, dash="4 4"),
    t(360, 20, "下照式（Bottom-up）", 15, "middle", bold=True),
    rect(300, 40, 120, 10, BED, INK, 1.2), line(360, 28, 360, 40, INK, 1.5),
    rect(320, 50, 80, 110, PART, INK, 1.2),
    rect(290, 150, 140, 26, RESIN, INK, 1.5), rect(320, 150, 80, 10, PART, INK, 1.2),
    "".join(line(330 + i * 30, 206, 330 + i * 30, 180, UV, 1.6, True, marker="u") for i in range(3)),
    line(438, 120, 438, 70, INK, 2, True), t(436, 140, "撕開", 12, "end"),
    t(360, 232, "光從槽底往上照，模型倒掛", 13, "middle"),
    t(360, 252, "每層都要從槽底撕開（拉拔力）", 12, "middle", "#7a7166"),
]))

# ---------- FDM ----------
def infill(x, y, size, gap, label):
    lines = "".join(line(x + 6 + k, y + 6, x + 6 + k, y + size - 6, "#f0a07f", 1.3) for k in range(gap, size - 12, gap))
    lines += "".join(line(x + 6, y + 6 + k, x + size - 6, y + 6 + k, "#f0a07f", 1.3) for k in range(gap, size - 12, gap))
    return (rect(x, y, size, size, "#fff", BRAND, 3) + rect(x + 5, y + 5, size - 10, size - 10, "none", BRAND, 2)
            + lines + t(x + size / 2, y + size + 22, label, 14, "middle", bold=True))


FIGS["infill"] = svg(480, 220, "".join([
    infill(30, 20, 120, 34, "低填充"), infill(180, 20, 120, 16, "中填充"), infill(330, 20, 120, 7, "高填充"),
    line(60, 182, 420, 182, INK, 2, True),
    t(240, 206, "越密 → 越強、越重、越久、越費料、頂面封得越好", 13, "middle"),
]))


def stair(x0, y0, R, step, color):
    out = ""
    y = 0
    while y < R - 0.1:
        mid = min(y + step / 2, R)
        wdt = math.sqrt(max(R * R - mid * mid, 0))
        out += rect(x0, y0 - y - step, wdt, step, color, INK, .8)
        y += step
    arc = f'<path d="M{x0} {y0-R}A{R} {R} 0 0 1 {x0+R} {y0}" fill="none" stroke="{INK}" stroke-width="1.5" stroke-dasharray="4 3"/>'
    return out + arc


FIGS["layer"] = svg(480, 220, "".join([
    stair(40, 160, 130, 26, "#f0a07f"), stair(270, 160, 130, 8, "#f0a07f"),
    t(105, 186, "層厚：快，階梯明顯", 14, "middle", bold=True),
    t(335, 186, "層薄：慢，表面平滑", 14, "middle", bold=True),
    t(240, 212, "虛線＝原本想要的曲面。好用口訣：層厚 ≈ 噴嘴直徑的一半", 13, "middle", "#7a7166"),
]))

FIGS["bridge"] = svg(480, 180, "".join([
    rect(80, 60, 50, 90, "#f0a07f", INK, 1.2), rect(350, 60, 50, 90, "#f0a07f", INK, 1.2),
    rect(60, 150, 360, 10, BED, INK, 1.2),
    f'<path d="M130 62Q240 76 350 62" fill="none" stroke="{BRAND}" stroke-width="4"/>',
    t(240, 50, "架橋：在空中直接拉線，跨過去", 14, "middle", bold=True),
    t(240, 110, "溫度低一點、速度快一點", 13, "middle"), t(240, 130, "→ 跨得更遠、不下垂", 13, "middle"),
]))

# ---------- 擺放與支撐 ----------
FIGS["support"] = svg(480, 230, "".join([
    rect(40, 196, 400, 10, BED, INK, 1.2),
    f'<path d="M120 196V70H340V110H170V196Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.5"/>',
    "".join(rect(184 + i * 26, 110, 10, 86, "#eee", GRAY, 1, extra='stroke-dasharray="3 2"') for i in range(6)),
    t(350, 92, "懸空（懸臂）", 13), t(270, 156, "支撐", 13, "middle", "#7a7166"),
    f'<path d="M30 196L90 140L90 196Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.5"/>',
    t(20, 128, "緩斜面：不用支撐", 12),
    t(240, 226, "支撐是暫時的，印完拆掉；不會讓模型變強，還多花時間和材料", 13, "middle", "#7a7166"),
]))

def adhesion(cx, kind):
    top = 30
    s = 56
    x, y = cx - s / 2, top + 22
    out = ""
    if kind == "raft":
        out += rect(x - 16, y - 16, s + 32, s + 32, "#f6d9cb", INK, 1, extra='stroke-dasharray="2 2"')
    if kind == "brim":
        out += "".join(rect(x - k, y - k, s + 2 * k, s + 2 * k, "none", BRAND, 1.3) for k in (4, 8, 12, 16))
    if kind == "skirt":
        out += rect(x - 22, y - 22, s + 44, s + 44, "none", BRAND, 1.5, 6)
    out += rect(x, y, s, s, PART, INK, 1.2)
    # 側面
    by = 182
    out += rect(cx - 64, by + 14, 128, 6, BED, INK, 1)
    if kind == "raft":
        out += rect(cx - 44, by + 6, 88, 8, "#f6d9cb", INK, 1) + rect(cx - 28, by - 22, 56, 28, PART, INK, 1.2)
    elif kind == "brim":
        out += rect(cx - 44, by + 10, 88, 4, BRAND, INK, .8) + rect(cx - 28, by - 18, 56, 28, PART, INK, 1.2)
    else:
        out += rect(cx - 56, by + 10, 8, 4, BRAND, INK, .8) + rect(cx + 48, by + 10, 8, 4, BRAND, INK, .8)
        out += rect(cx - 28, by - 18, 56, 32, PART, INK, 1.2)
    return out


FIGS["adhesion"] = svg(480, 290, "".join([
    adhesion(80, "raft"), adhesion(240, "brim"), adhesion(400, "skirt"),
    t(10, 18, "上面看", 12, color="#7a7166"), t(10, 160, "側面看", 12, color="#7a7166"),
    t(80, 232, "Raft 木筏", 15, "middle", bold=True), t(80, 252, "整片墊在模型底下", 12, "middle"), t(80, 270, "底部不平時用", 12, "middle"),
    t(240, 232, "Brim 邊緣", 15, "middle", bold=True), t(240, 252, "貼著模型外圍一圈圈", 12, "middle"), t(240, 270, "防翹曲", 12, "middle"),
    t(400, 232, "Skirt 裙邊", 15, "middle", bold=True), t(400, 252, "不碰模型的外圈", 12, "middle"), t(400, 270, "只是試出料", 12, "middle"),
]))

FIGS["place-fdm"] = svg(480, 220, "".join([
    rect(10, 150, 220, 6, BED, INK, 1), rect(250, 150, 220, 6, BED, INK, 1),
    f'<path d="M30 150V96H44V136H86V96H100V150Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    mark(65, 180, True), t(65, 200, "盒子開口朝上", 12, "middle"),
    f'<path d="M140 150V96H210V150H196V110H154V150Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    "".join(rect(158 + i * 12, 110, 6, 40, "#eee", GRAY, 1, extra='stroke-dasharray="2 2"') for i in range(3)),
    mark(175, 180, False), t(175, 200, "開口朝下要撐", 12, "middle"),
    f'<path d="M270 150V138H340V150ZM276 138V100H284V138ZM326 138V100H334V138Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    mark(305, 180, True), t(305, 200, "桌面貼平台", 12, "middle"),
    f'<path d="M370 112H450V100H370ZM376 112V150H384V112ZM436 112V150H444V112Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    "".join(rect(392 + i * 12, 112, 6, 38, "#eee", GRAY, 1, extra='stroke-dasharray="2 2"') for i in range(3)),
    mark(410, 180, False), t(410, 200, "桌面懸空要撐", 12, "middle"),
    t(240, 30, "FDM：讓東西直直往上長，沒有懸空就不用支撐", 14, "middle", bold=True),
]))

FIGS["place-bottomup"] = svg(480, 240, "".join([
    t(240, 20, "下照式光固化：切片軟體裡的擺法（平台在下，往上長）", 13, "middle", "#7a7166"),
    "".join(rect(x, 150, 120, 6, BED, INK, 1) for x in (20, 180, 340)),
    # 杯子開口朝下
    f'<path d="M40 150V80H120V150H106V94H54V150Z" fill="{PART}" stroke="{INK}" stroke-width="1.3"/>',
    t(80, 128, "封住", 11, "middle", "#fff"), mark(80, 182, False), t(80, 202, "開口朝下", 12, "middle"), t(80, 220, "吸盤效應，會扯壞", 12, "middle", BAD),
    # 開口朝上
    f'<path d="M200 150V80H214V136H266V80H280V150Z" fill="{PART}" stroke="{INK}" stroke-width="1.3"/>',
    mark(240, 182, True), t(240, 202, "開口朝上", 12, "middle"), t(240, 220, "實心底先印", 12, "middle"),
    # 大平面斜放
    f'<path d="M362 126L432 60L442 70L372 136Z" fill="{PART}" stroke="{INK}" stroke-width="1.3"/>',
    "".join(line(372 + i * 16, 134 - i * 15, 372 + i * 16, 150, GRAY, 1.5) for i in range(5)),
    mark(400, 182, True), t(400, 202, "大平面斜放", 12, "middle"), t(400, 220, "每層面積小、好撕開", 12, "middle"),
]))

FIGS["hole"] = svg(480, 220, "".join([
    rect(30, 150, 180, 6, BED, INK, 1), rect(270, 150, 180, 6, BED, INK, 1),
    f'<ellipse cx="120" cy="80" rx="60" ry="18" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    f'<path d="M60 80V140A60 18 0 0 0 180 140V80" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    f'<ellipse cx="120" cy="80" rx="22" ry="7" fill="#fff" stroke="{INK}"/>',
    mark(120, 182, True), t(120, 202, "孔朝上下：每層都直接畫出圓", 12, "middle"),
    f'<circle cx="360" cy="94" r="50" fill="#f0a07f" stroke="{INK}" stroke-width="1.3"/>',
    "".join(rect(360 - math.sqrt(max(22 ** 2 - (yy + 4) ** 2, 0)), 94 + yy, 2 * math.sqrt(max(22 ** 2 - (yy + 4) ** 2, 0)), 8, "#fff", INK, .6)
            for yy in range(-24, 24, 8)),
    mark(360, 182, False), t(360, 202, "孔躺平：圓被切成階梯", 12, "middle"),
]))

FIGS["strength"] = svg(480, 220, "".join([
    "".join(rect(40, 40 + i * 12, 140, 12, "#f0a07f", INK, .8) for i in range(9)),
    line(30, 100, 4, 100, INK, 2.5, True), line(190, 100, 216, 100, INK, 2.5, True),
    mark(110, 180, True), t(110, 202, "順著層拉：每層完整受力", 12, "middle"),
    "".join(rect(280 + i * 0, 40 + i * 12, 140, 12, "#f0a07f", INK, .8) for i in range(9)),
    line(350, 36, 350, 10, INK, 2.5, True), line(350, 152, 350, 172, INK, 2.5, True),
    line(280, 112, 420, 112, BAD, 2, dash="5 3"),
    mark(350, 192, False), t(350, 212, "拉開層與層的縫：最弱", 12, "middle"),
]))

# ---------- 印壞了 ----------
FIGS["warp"] = svg(480, 210, "".join([
    rect(40, 150, 400, 10, BED, INK, 1.2),
    f'<path d="M100 132Q240 150 380 132L384 100Q240 116 96 100Z" fill="#f0a07f" stroke="{INK}" stroke-width="1.5"/>',
    line(240, 120, 150, 112, INK, 1.5, True), line(240, 120, 330, 112, INK, 1.5, True), t(240, 96, "冷卻收縮", 13, "middle"),
    t(70, 128, "邊角翹起", 13, "end", BAD),
    t(240, 184, "修：熱床加熱、封閉機殼保溫、加 Brim／Raft、塗膠", 13, "middle", GOOD),
    t(240, 204, "✗ 風扇猛吹（尤其 ABS）、關熱床會更糟", 13, "middle", BAD),
]))

FIGS["string"] = svg(480, 200, "".join([
    rect(40, 150, 400, 8, BED, INK, 1.2),
    rect(90, 50, 60, 100, "#f0a07f", INK, 1.2), rect(330, 50, 60, 100, "#f0a07f", INK, 1.2),
    "".join(f'<path d="M150 {60+i*16}Q240 {72+i*16} 330 {58+i*16}" fill="none" stroke="{BRAND}" stroke-width=".8"/>' for i in range(5)),
    t(240, 40, "牽絲：噴頭移動時拉出細絲", 14, "middle", bold=True),
    t(240, 176, "原因：噴嘴太熱、沒回抽好", 13, "middle"),
    t(240, 194, "修：降噴嘴溫度、加大回抽距離／速度", 13, "middle", GOOD),
]))

# ---------- 檔案 ----------
FIGS["stl"] = svg(480, 220, "".join([
    f'<path d="M50 170L190 150L110 50Z" fill="#dce8fb" stroke="{INK}" stroke-width="1.5"/>',
    "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="{INK}"/>' for x, y in ((50, 170), (190, 150), (110, 50))),
    t(30, 192, "頂點 1"), t(190, 172, "頂點 2"), t(118, 44, "頂點 3"),
    line(117, 123, 175, 75, BRAND, 2.5, True), t(178, 72, "法線（往外指）", 13, color=BRAND),
    t(110, 212, "1 個三角形 = 3 頂點 + 1 法線", 13, "middle", bold=True),
    "".join(f'<path d="M{360+70*math.cos(a)} {110+70*math.sin(a)}L{360+70*math.cos(a+math.pi/5)} {110+70*math.sin(a+math.pi/5)}L360 110Z" fill="#dce8fb" stroke="{INK}" stroke-width="1"/>'
            for a in [k * math.pi / 5 for k in range(10)]),
    f'<circle cx="360" cy="110" r="70" fill="none" stroke="{BRAND}" stroke-dasharray="4 3"/>',
    t(360, 212, "曲面用三角形拼，一定有誤差", 13, "middle", bold=True),
]))

FIGS["cube"] = svg(480, 210, "".join([
    f'<path d="M150 70L250 70L250 170L150 170Z" fill="#dce8fb" stroke="{INK}" stroke-width="1.5"/>',
    f'<path d="M150 70L190 40L290 40L250 70Z" fill="#c4d8f5" stroke="{INK}" stroke-width="1.5"/>',
    f'<path d="M250 70L290 40L290 140L250 170Z" fill="#aac6ee" stroke="{INK}" stroke-width="1.5"/>',
    line(150, 170, 250, 70, BRAND, 1.5), line(150, 70, 290, 40, BRAND, 1.5), line(250, 170, 290, 40, BRAND, 1.5),
    t(330, 80, "每個面切成 2 個三角形", 14), t(330, 108, "6 面 × 2 = 12 個", 16, bold=True, color=BRAND),
    t(330, 136, "每個三角形 12 個數字", 13), t(330, 156, "（法線 3＋頂點 3×3）", 12, color="#7a7166"),
    t(330, 180, "12 × 12 = 144", 14, bold=True),
]))

# ---------- 材料 ----------
TG = [("PEEK", 143), ("ABS", 105), ("PETG", 80), ("PLA", 60), ("尼龍", 47)]
FIGS["tg"] = svg(480, 230, "".join(
    [t(240, 22, "玻璃轉化溫度 Tg（開始變軟的溫度）", 14, "middle", bold=True)]
    + [rect(90, 40 + i * 34, v * 2.2, 22, BRAND if i == 0 else "#f0a07f", "none", 0, 4)
       + t(80, 56 + i * 34, n, 14, "end", bold=True)
       + t(98 + v * 2.2, 56 + i * 34, "35~60°C" if n == "尼龍" else f"{v}°C", 13)
       for i, (n, v) in enumerate(TG)]
    + [t(240, 222, "PEEK 最耐熱；尼龍最低；PLA 約 60°C 就軟", 12, "middle", "#7a7166")]))

# ---------- 題目專用 ----------
def _peel_sup(x, y1, y2, broken=False):
    if not broken:
        return line(x, y1, x, y2, GRAY, 2.5)
    m = (y1 + y2) / 2
    return line(x, y1, x, m - 6, GRAY, 2.5) + line(x, m + 6, x, y2, GRAY, 2.5) + t(x, m + 5, "✗", 13, "middle", BAD, True)


FIGS["peel"] = svg(480, 330, "".join([
    t(240, 20, "下照式：每印一層，機器就把模型往上拉，從盤底「撕」起來", 13, "middle", bold=True),
    # 左：平放
    rect(40, 52, 160, 10, BED, INK, 1.2), line(120, 48, 120, 30, INK, 2.5, True), t(130, 42, "往上拉", 12),
    "".join(_peel_sup(52 + i * 17, 62, 154, i in (2, 5, 7)) for i in range(9)),
    rect(45, 154, 150, 50, PART, INK, 1.2),
    rect(20, 170, 200, 40, RESIN, INK, 1.5, extra='fill-opacity=".55"'),
    line(45, 205, 195, 205, BAD, 4), t(120, 226, "整片黏在盤底", 12, "middle", BAD),
    "".join(line(50 + i * 35, 252, 50 + i * 35, 232, UV, 1.5, True, marker="u") for i in range(5)),
    t(120, 278, "B：大面平放", 15, "middle", BAD, True),
    t(120, 298, "每層都是整片 30×30", 12, "middle"), t(120, 316, "撕很用力 → 支撐被扯斷、掉下來", 12, "middle"),
    line(240, 40, 240, 320, GRAY, 1, dash="4 4"),
    # 右：斜放
    rect(280, 52, 160, 10, BED, INK, 1.2), line(360, 48, 360, 30, INK, 2.5, True), t(370, 42, "往上拉", 12),
    "".join(line(x, 62, x, 88 + (x - 283) * 75 / 106, GRAY, 2.5) for x in range(292, 388, 14)),
    '<path d="M360 204L254 129L283 88L389 163Z" fill="%s" stroke="%s" stroke-width="1.2"/>' % (PART, INK),
    rect(246, 170, 226, 40, RESIN, INK, 1.5, extra='fill-opacity=".55"'),
    line(350, 205, 370, 205, BAD, 4), t(372, 226, "只黏一小條", 12, "middle", BAD),
    "".join(line(290 + i * 35, 252, 290 + i * 35, 232, UV, 1.5, True, marker="u") for i in range(5)),
    t(360, 278, "A、C、D：立起或斜放", 15, "middle", GOOD, True),
    t(360, 298, "每層面積小", 12, "middle"), t(360, 316, "好撕 → 支撐不會斷", 12, "middle"),
]))


def main():
    OUT.mkdir(exist_ok=True)
    for k, v in FIGS.items():
        (OUT / f"{k}.svg").write_text(v, encoding="utf-8")
    print(len(FIGS), "張圖")


if __name__ == "__main__":
    main()
