import math
from PIL import Image, ImageDraw, ImageFont

SRC = r"course_materials\git_graph.png"
DST = r"course_materials\git_graph_annotated.png"

S = 3                                   # upscale factor for the screenshot
LEFT, RIGHT, TOP, BOT = 480, 560, 34, 34

src = Image.open(SRC).convert("RGB")
w, h = src.size
big = src.resize((w * S, h * S), Image.LANCZOS)

W, H = LEFT + w * S + RIGHT, TOP + h * S + BOT
canvas = Image.new("RGB", (W, H), "white")
canvas.paste(big, (LEFT, TOP))
d = ImageDraw.Draw(canvas)
d.rectangle([LEFT - 1, TOP - 1, LEFT + w * S, TOP + h * S], outline="#BBBBBB", width=2)

f_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 31)
f_body = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)


def cx(ox):                             # screenshot px -> canvas px
    return LEFT + ox * S


def cy(oy):
    return TOP + oy * S


def box(o, color):
    x0, y0, x1, y1 = cx(o[0]), cy(o[1]), cx(o[2]), cy(o[3])
    d.rounded_rectangle([x0, y0, x1, y1], radius=8, outline=color, width=5)
    return (x0, y0, x1, y1)


def arrow(p0, p1, color):
    d.line([p0, p1], fill=color, width=5)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L, sp = 24, 0.42
    d.polygon([p1,
               (p1[0] - L * math.cos(ang - sp), p1[1] - L * math.sin(ang - sp)),
               (p1[0] - L * math.cos(ang + sp), p1[1] - L * math.sin(ang + sp))],
              fill=color)


def label(x, y, num, title, lines, color, anchor="la"):
    d.text((x, y), f"{num}.  {title}", font=f_title, fill=color, anchor=anchor)
    yy = y + 42
    for ln in lines:
        d.text((x, yy), ln, font=f_body, fill="#2B2B2B", anchor=anchor)
        yy += 33


C1, C2, C3, C4, C5 = "#D81B60", "#00897B", "#2E7D32", "#6A1B9A", "#C62828"

# --- boxes over the screenshot ------------------------------------------------
b1 = box((9, 0, 203, 20), C1)            # a commit: message + author
b2 = box((28, 65, 292, 153), C2)         # the files that commit changed
b3 = box((181, 43, 238, 63), C3)         # local branch badge "main"
b4 = box((203, 0, 292, 19), C4)          # remote branch badge "origin/main"
b5 = box((221, 22, 269, 41), C5)         # HEAD badge "bj147"
d.ellipse([cx(27.5) - 21, cy(31.5) - 21, cx(27.5) + 21, cy(31.5) + 21],
          outline=C5, width=5)           # ... and the hollow ring for that commit

# --- left-hand labels ---------------------------------------------------------
LX = LEFT - 56
label(LX, TOP + 4, "1", "A commit", [
    "One saved snapshot of the project:",
    "the commit message, then who",
    "made it. The dot on the line is this",
    "commit; the line joins it to the",
    "commit it was built from (parent).",
], C1, anchor="ra")
arrow((LX + 14, cy(9)), (b1[0] - 9, cy(9)), C1)

label(LX, cy(95), "2", "Files in a commit", [
    "Exactly what this commit changed.",
    "Click a commit to expand the list.",
    "M = modified, D = deleted,",
    "A = added.",
], C2, anchor="ra")
arrow((LX + 14, cy(108)), (b2[0] - 9, cy(108)), C2)

# --- right-hand labels --------------------------------------------------------
RX = LEFT + w * S + 40
label(RX, TOP + 4, "4", "A remote branch", [
    "origin/main - the branch as it exists on",
    "the server (GitHub). The cloud icon",
    "marks a branch on a remote.",
], C4)
arrow((RX - 16, TOP + 18), (b4[2] + 9, cy(9)), C4)

label(RX, cy(45), "5", "HEAD", [
    "Where you are right now. The target icon",
    "marks the branch you have checked out",
    "(bj147); the hollow ring on the graph",
    "marks the commit HEAD points at.",
], C5)
arrow((RX - 16, cy(59)), (b5[2] + 4, cy(31)), C5)

label(RX, cy(110), "3", "A local branch", [
    "main - a branch in the copy of the",
    "repository on your own computer. The",
    "fork icon marks a local branch. This one",
    "sits 2 commits behind origin/main.",
], C3)
arrow((RX - 16, cy(124)), (b3[2] + 4, cy(53)), C3)

canvas.save(DST)
print("wrote", DST, canvas.size)
