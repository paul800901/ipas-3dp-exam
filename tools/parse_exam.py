"""從官方公告試題 PDF（115 年第一次）擷取題目與答案；有附圖的題目截成圖片。

用法：python -I tools/parse_exam.py
輸出：tools/exam115.json、app/img/e115-*.png
"""
import json
import re
from pathlib import Path

import fitz  # pymupdf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "exam115"
IMG = ROOT / "app" / "img"
OUT = ROOT / "tools" / "exam115.json"

ANS_RE = re.compile(r"^\s*([A-D])\s*$")
Q_RE = re.compile(r"^\s*(\d+)\.\s*(.*)$")
OPT_RE = re.compile(r"^\s*\(([A-D])\)\s*(.*)$")
HEADER_RE = re.compile(r"^\s*(115 年第一次.*|第.科：.*|考試日期：.*|\d+|答案|題目)\s*$")


def join(parts):
    s = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if s and re.match(r"[A-Za-z0-9(（]", p[:1]) and re.search(r"[A-Za-z0-9,.)）]$", s):
            s += " "
        s += p
    return s.strip()


def parse(doc):
    items, cur, opt = [], None, None
    pending_ans = None
    for pno, page in enumerate(doc, start=1):
        for raw in page.get_text().splitlines():
            if HEADER_RE.match(raw) and not ANS_RE.match(raw):
                continue
            m = ANS_RE.match(raw)
            if m:
                pending_ans = m.group(1)
                continue
            m = Q_RE.match(raw)
            if m and pending_ans:
                cur = {"num": int(m.group(1)), "answer": pending_ans, "page": pno,
                       "stem": [m.group(2)], "opts": {}}
                items.append(cur)
                pending_ans, opt = None, None
                continue
            if cur is None:
                continue
            m = OPT_RE.match(raw)
            if m:
                opt = m.group(1)
                cur["opts"][opt] = [m.group(2)]
            elif opt:
                cur["opts"][opt].append(raw)
            else:
                cur["stem"].append(raw)
    out = []
    for it in items:
        options = [re.sub(r"[；;。]\s*$", "", join(it["opts"].get(k, []))) for k in "ABCD"]
        out.append({"num": it["num"], "answer": it["answer"], "page": it["page"],
                    "q": join(it["stem"]), "options": options})
    return out


def question_spans(doc, items):
    """回傳每題 (起始頁, 起始 y)；用頁面上「N.」開頭的文字行定位。"""
    pos = {}
    for pno, page in enumerate(doc, start=1):
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                m = re.match(r"^(\d+)\.", text)
                if m and line["bbox"][0] < 150:
                    n = int(m.group(1))
                    if n not in pos and any(i["num"] == n for i in items):
                        pos[n] = (pno, line["bbox"][1])
    return pos


def crop(doc, items, prefix):
    pos = question_spans(doc, items)
    for idx, it in enumerate(items):
        if it["num"] not in pos:
            print("[warn] 找不到", prefix, it["num"])
            continue
        pno, y0 = pos[it["num"]]
        nxt = items[idx + 1]["num"] if idx + 1 < len(items) else None
        end = pos.get(nxt)
        regions = []
        if end and end[0] == pno:
            regions.append((pno, y0, end[1]))
        else:
            page = doc[pno - 1]
            regions.append((pno, y0, page.rect.height - 30))
            if end and end[0] > pno:
                regions.append((end[0], 115, end[1]))
            elif not end and pno < len(doc):
                regions.append((pno + 1, 115, doc[pno].rect.height - 30))
        has_img = False
        for rp, a, b in regions:
            page = doc[rp - 1]
            for info in page.get_image_info():
                r = fitz.Rect(info["bbox"])
                if r.width > page.rect.width * 0.9:  # 每頁都有的浮水印
                    continue
                if r.y1 > a + 2 and r.y0 < b - 2 and r.width > 20 and r.height > 20:
                    has_img = True
        if not has_img:
            continue
        imgs = []
        for k, (rp, a, b) in enumerate(regions):
            if b - a < 15:
                continue
            page = doc[rp - 1]
            clip = fitz.Rect(88, a - 4,  # 左側 49~79 是答案欄，不能截進去
                               page.rect.x1 - 20, b - 2)
            name = f"{prefix}-{it['num']:02d}{'' if k == 0 else 'b'}.png"
            page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip).save(IMG / name)
            imgs.append(f"img/{name}")
        it["imgs"] = imgs


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    result = []
    for subj in (1, 2):
        doc = fitz.open(SRC / f"exam115_{subj}.pdf")
        items = parse(doc)
        crop(doc, items, f"e115-{subj}")
        for it in items:
            it["id"] = f"e115-{subj}-{it['num']:02d}"
            it["subject"] = subj
        print(f"科目{subj}: {len(items)} 題，附圖 {sum(1 for i in items if i.get('imgs'))} 題")
        result += items
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
