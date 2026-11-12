"""把題目、官方答案、白話解說與重點卡片合併成 app/data.js。

先跑 parse_guides.py、parse_exam.py，再跑本檔：python -I tools/build_data.py
"""
import json
import re
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
APP = TOOLS.parent / "app"

TOPICS = {
    "name": "七大技術名稱", "tech": "技術原理與機器", "vpp": "光固化參數",
    "fdm": "FDM 參數", "place": "擺放與支撐", "fix": "印壞了怎麼修",
    "file": "檔案格式", "matF": "FDM 線材", "matR": "光固化樹脂",
    "post": "後處理", "safe": "安全與急救", "adv": "優勢與應用",
}

# 官方解析尾端混進章節總結的段落，從這些字開始截掉
OFFICIAL_CUT = {
    "s2-010": "1. G-Code", "s2-020": "模型的底部不平整", "s2-030": "在熔融擠製成型技術",
    "s2-040": "在熱塑性高分子材料", "s2-050": "3D 列印製程缺陷的成因", "s2-060": "在光聚合光敏樹脂中",
    "s2-070": "PLA 材料本身",
}
OFFICIAL_REPLACE = {
    "s2-064": "PEEK：Tg 約 143℃；ABS：Tg 約 100～105℃；PLA：Tg 約 55～60℃。因此由高至低為 PEEK > ABS > PLA。",
}


def clean_q(text):
    # 題幹尾端的圖片來源網址、圖註
    text = re.sub(r"(？|\?)[^？?]*$", r"\1", text) if re.search(r"[？?][^？?]*(https?:|troubleshooting|sticking|in-top|printed-pieces|\(a\))", text) else text
    text = text.replace("(A) 當線徑誤差過大時暫停列印", "")
    return text.strip()


def ai_questions():
    """AI 依學習指引出的模擬題（tools/ai_questions.json，已經過另一家模型核對）。

    每科分成兩份模擬卷：同一位出題者的題目依主題排好後輪流分給第 1、2 份，兩份主題比例一樣。
    """
    path = TOOLS / "ai_questions.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for group in sorted({q["id"].rsplit("-", 1)[0] for q in items}):
        qs = sorted((q for q in items if q["id"].startswith(group + "-")), key=lambda q: (q["topic"], q["id"]))
        for i, q in enumerate(qs):
            assert q["topic"] in TOPICS and q["answer"] in "ABCD" and len(q["options"]) == 4, q["id"]
            out.append({
                "id": q["id"], "src": "AI模擬題", "subject": q["subject"], "topic": q["topic"],
                "q": q["q"], "options": q["options"], "answer": q["answer"],
                "plain": q["plain"], "tip": q["tip"], "paper": i % 2 + 1,
            })
    return out


def main():
    guide = json.loads((TOOLS / "official_questions.json").read_text(encoding="utf-8"))
    exam = json.loads((TOOLS / "exam115.json").read_text(encoding="utf-8"))
    ex = json.loads((TOOLS / "explain_exam.json").read_text(encoding="utf-8"))
    ex.update(json.loads((TOOLS / "explain_guide.json").read_text(encoding="utf-8")))
    lessons = json.loads((TOOLS / "lessons.json").read_text(encoding="utf-8"))

    out, missing = [], []
    for q in exam + guide:
        qid = q["id"]
        if qid not in ex:
            missing.append(qid)
            continue
        topic, plain, tip, *fig = ex[qid]
        assert topic in TOPICS, (qid, topic)
        options = [re.sub(r"；\s*\(E\).*$", "", o) for o in q["options"]]
        item = {
            "id": qid,
            "src": "115真題" if qid.startswith("e115") else "官方樣題",
            "subject": q["subject"],
            "topic": topic,
            "q": clean_q(q["q"]),
            "options": options,
            "answer": q["answer"],
            "plain": plain,
            "tip": tip,
        }
        imgs = q.get("imgs") or [x for x in (q.get("img"), q.get("img2")) if x]
        if imgs:
            item["imgs"] = imgs
        if fig:
            item["fig"] = fig[0]
        if "official" in q:
            off = q["official"]
            if qid in OFFICIAL_CUT:
                off = off.split(OFFICIAL_CUT[qid])[0].strip()
            off = OFFICIAL_REPLACE.get(qid, off)
            item["official"] = re.sub(r"^題目解析：", "", off)
        out.append(item)
    out += ai_questions()
    if missing:
        raise SystemExit(f"缺白話解說：{missing}")
    extra = set(ex) - {q["id"] for q in out}
    if extra:
        raise SystemExit(f"解說對不到題目：{sorted(extra)}")

    data = {"topics": TOPICS, "lessons": lessons, "questions": out, "examDate": "2026-11-14"}
    APP.joinpath("data.js").write_text(
        "// 由 tools/build_data.py 產生，請勿手動修改\nwindow.EXAM_DATA = "
        + json.dumps(data, ensure_ascii=False, indent=0) + ";\n",
        encoding="utf-8",
    )
    print(f"題目 {len(out)} 題（真題 {sum(1 for q in out if q['src'] == '115真題')}、樣題 {sum(1 for q in out if q['src'] == '官方樣題')}、AI 模擬題 {sum(1 for q in out if q['src'] == 'AI模擬題')}）")


if __name__ == "__main__":
    main()
