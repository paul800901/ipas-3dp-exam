// 3D 列印考試抱佛腳 APP：所有進度存在這台裝置的瀏覽器裡（localStorage），不需要帳號。
(function () {
  "use strict";

  const DATA = window.EXAM_DATA;
  const Q = DATA.questions;
  const QBY = Object.fromEntries(Q.map((q) => [q.id, q]));
  const LETTERS = ["A", "B", "C", "D"];
  const SESSION_SIZE = 20;
  const MOCK_SIZE = 50;
  const MOCK_MINUTES = 75;
  const KEY = "exam3dp_v1";
  const app = document.getElementById("app");

  // ---------- 進度儲存 ----------
  let store = load();
  function load() {
    try {
      const s = JSON.parse(localStorage.getItem(KEY));
      if (s && s.stats) return Object.assign({ days: {}, mocks: [], marks: {} }, s);
    } catch (e) { /* 壞掉就重來 */ }
    return { stats: {}, days: {}, mocks: [], marks: {} };
  }
  function save() { localStorage.setItem(KEY, JSON.stringify(store)); }
  function today() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  function record(id, ok) {
    const s = store.stats[id] || { r: 0, w: 0, streak: 0 };
    if (ok) { s.r++; s.streak++; } else { s.w++; s.streak = 0; }
    s.last = ok;
    store.stats[id] = s;
    const d = store.days[today()] || { done: 0, right: 0 };
    d.done++; if (ok) d.right++;
    store.days[today()] = d;
    save();
  }
  // 答錯過、而且還沒有連續答對 2 次，就留在錯題本
  const inWrongBook = (id) => { const s = store.stats[id]; return !!s && s.w > 0 && s.streak < 2; };
  const seen = (id) => !!store.stats[id];
  // 自己標記「不熟／用猜的」：要自己取消才會離開複習清單
  const marked = (id) => !!store.marks[id];
  const toReview = (id) => inWrongBook(id) || marked(id);
  function toggleMark(id) {
    if (marked(id)) delete store.marks[id]; else store.marks[id] = 1;
    save();
  }
  const markLabel = (id) => (marked(id) ? "🔖 已標記（再按一下取消）" : "🔖 標記這題：不熟／用猜的");
  const markBtn = (id) => `<button class="small mark ${marked(id) ? "on" : ""}" data-mark="${esc(id)}">${markLabel(id)}</button>`;
  // 按標記鈕只換按鈕本身，不重畫畫面（作答到一半也不會跳掉）
  function bindMarks(onChange) {
    app.querySelectorAll("[data-mark]").forEach((b) => {
      b.onclick = () => {
        const id = b.dataset.mark;
        toggleMark(id);
        b.classList.toggle("on", marked(id));
        b.textContent = markLabel(id);
        if (onChange) onChange(id);
      };
    });
  }

  // ---------- 小工具 ----------
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function shuffle(a) {
    a = a.slice();
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
  }
  function daysLeft() {
    const t = new Date(today() + "T00:00:00");
    const e = new Date(DATA.examDate + "T00:00:00");
    return Math.round((e - t) / 86400000);
  }
  const subjName = (s) => (s === 1 ? "科目一：3D 列印概論" : "科目二：製程與材料概論");
  // AI 依官方學習指引另外出的題目，跟官方題分開，不混進原本的模擬考與隨機練習
  const isAI = (q) => q.src === "AI模擬題";
  const OFFICIAL = Q.filter((q) => !isAI(q));
  const PAPERS = [];
  Q.filter(isAI).forEach((q) => {
    let p = PAPERS.find((x) => x.subject === q.subject && x.no === q.paper);
    if (!p) PAPERS.push((p = { subject: q.subject, no: q.paper, ids: [] }));
    p.ids.push(q.id);
  });
  // 第 5、6 份是照真題風格出的觀念判斷題，排最前面；第 3、4 份考講義細節，比真題難，排最後
  const paperRank = (no) => (no === 5 || no === 6 ? 0 : no === 3 || no === 4 ? 2 : 1);
  const paperNote = (no) => ["觀念判斷題，最接近真題，優先練", "綜合題", "講義細節題，比真題難，當補充就好"][paperRank(no)];
  PAPERS.sort((a, b) => a.subject - b.subject || paperRank(a.no) - paperRank(b.no) || a.no - b.no);
  const paperName = (p) => `AI 模擬卷・${p.subject === 1 ? "科目一" : "科目二"}・第 ${p.no} 份`;
  function tagsHtml(q) {
    const src = q.src === "115真題" ? ["real", "⭐ 115 年真題"] : isAI(q) ? ["ai", "🤖 AI 模擬題"] : ["", "官方樣題"];
    return `<div class="tags">
      <span class="tag ${src[0]}">${src[1]}</span>
      <span class="tag">${q.subject === 1 ? "科目一" : "科目二"}</span>
      <span class="tag">${esc(DATA.topics[q.topic])}</span></div>`;
  }
  function imgsHtml(q) {
    return (q.imgs || []).map((src) => `<img class="qimg" src="${esc(src)}" alt="題目附圖（點一下放大）">`).join("");
  }
  function optionText(q, i) {
    const t = q.options[i];
    return t ? esc(t) : '<span class="muted">（看上面的圖）</span>';
  }
  function bindZoom() {
    app.querySelectorAll(".qimg").forEach((img) => {
      img.onclick = () => {
        const z = document.getElementById("zoom");
        z.querySelector("img").src = img.src;
        z.classList.add("show");
      };
    });
  }
  document.getElementById("zoom").onclick = (e) => e.currentTarget.classList.remove("show");

  let keyHandler = null;
  document.addEventListener("keydown", (e) => { if (keyHandler) keyHandler(e); });
  let timerId = null;
  function stopTimer() { if (timerId) { clearInterval(timerId); timerId = null; } }

  function show(html, after) {
    stopTimer();
    keyHandler = null;
    app.innerHTML = html;
    window.scrollTo(0, 0);
    if (after) after();
  }
  function bind(sel, fn) { const el = app.querySelector(sel); if (el) el.onclick = fn; }
  function bindAll(sel, fn) { app.querySelectorAll(sel).forEach((el) => { el.onclick = () => fn(el); }); }

  // ---------- 首頁 ----------
  function home() {
    const done = Q.filter((q) => seen(q.id)).length;
    const wrong = Q.filter((q) => toReview(q.id)).length;
    const td = store.days[today()] || { done: 0, right: 0 };
    const left = daysLeft();
    const lastMock = store.mocks.filter((m) => !m.paper).pop();
    show(`
      <h1>3D 列印考試・抱佛腳</h1>
      <p class="muted">iPAS 3D 列印積層製造工程師（初級）</p>
      <div class="card countdown">
        ${left > 0 ? `距離考試（11/14 星期六）還有<div class="big">${left} 天</div>` : left === 0 ? `<div class="big">今天考試，加油！</div>` : `<div class="big">考試結束了 🎉</div>`}
        <div>兩科平均 70 分、每科至少 60 分就通過</div>
      </div>
      <div class="card stats">
        <div><b>${td.done}</b><span>今天做了幾題</span></div>
        <div><b>${td.done ? Math.round((td.right / td.done) * 100) + "%" : "—"}</b><span>今天答對率</span></div>
        <div><b>${done}/${Q.length}</b><span>全部練過</span></div>
      </div>
      <div class="menu">
        <button id="m-learn"><span class="icon">📖</span><span>先看重點<span class="sub">用最白話的方式，把會考的觀念整理成卡片</span></span></button>
        <button id="m-real" class="primary"><span class="icon">⭐</span><span>刷 115 年真題<span class="sub" style="color:#ffe9dc">今年 5 月真的考過的 100 題，最重要</span></span></button>
        <button id="m-practice"><span class="icon">✏️</span><span>更多練習<span class="sub">官方樣題、依主題練、全部隨機</span></span></button>
        <button id="m-wrong"><span class="icon">❌</span><span>錯題＋標記（${wrong} 題）<span class="sub">答錯的、和你按 🔖 標記的題目都在這裡</span></span></button>
        <button id="m-mock"><span class="icon">🎯</span><span>模擬考<span class="sub">50 題、75 分鐘，跟真的考試一樣${lastMock ? `｜上次 ${lastMock.score} 分` : ""}</span></span></button>
        ${PAPERS.length ? `<button id="m-ai"><span class="icon">🤖</span><span>AI 模擬卷（${PAPERS.length} 份）<span class="sub">AI 讀官方講義另外出的新題，練習「沒看過的題目」</span></span></button>` : ""}
      </div>
      <div class="card">
        <h3>建議怎麼念（兩週）</h3>
        <p>① 前 3 天：每天看 3～4 張重點卡，看完就按「練這個主題」。</p>
        <p>② 第 4～10 天：每天刷 40 題真題＋樣題，錯的看白話解說。</p>
        <p>③ 用猜的、不太確定的題目按「🔖 標記」；每天睡前把「錯題＋標記」清一次。</p>
        <p>④ 最後 4 天：每天各考一次科目一、科目二模擬考，錯的再看解說。</p>
        <p class="muted">真題（⭐）常常換個說法再考一次，一定要熟。</p>
      </div>
      <p class="muted" style="text-align:center"><button class="small ghost" id="m-reset">清除所有進度</button></p>
    `, () => {
      bind("#m-learn", learnList);
      bind("#m-real", () => practiceMenu("real"));
      bind("#m-practice", () => practiceMenu("all"));
      bind("#m-wrong", wrongBook);
      bind("#m-mock", mockMenu);
      bind("#m-ai", aiMenu);
      bind("#m-reset", () => {
        if (confirm("確定要清除所有作答紀錄嗎？清掉就回不來了。")) { store = { stats: {}, days: {}, mocks: [], marks: {} }; save(); home(); }
      });
    });
  }

  // ---------- 重點卡 ----------
  function learnList() {
    const group = (s) => DATA.lessons.filter((l) => l.subject === s).map((l) => {
      const n = Q.filter((q) => q.topic === l.key).length;
      return `<button data-k="${l.key}"><span>${esc(l.title)}</span><span class="count">${n} 題</span></button>`;
    }).join("");
    show(`
      <div class="topbar"><button class="small" id="back">← 回首頁</button></div>
      <h2>📖 重點卡</h2>
      <p class="muted">每張卡看完，就按下面的按鈕練那個主題的題目，記得最牢。</p>
      <div class="card list"><h3>科目一：3D 列印概論</h3>${group(1)}</div>
      <div class="card list"><h3>科目二：製程與材料概論</h3>${group(2)}</div>
    `, () => {
      bind("#back", home);
      bindAll(".list button", (el) => lesson(el.dataset.k));
    });
  }

  function lesson(key, back) {
    const ordered = DATA.lessons.filter((x) => x.subject === 1).concat(DATA.lessons.filter((x) => x.subject === 2));
    const idx = ordered.findIndex((x) => x.key === key);
    const l = ordered[idx];
    const n = Q.filter((q) => q.topic === key).length;
    const next = ordered[idx + 1];
    show(`
      <div class="topbar"><button class="small" id="back">${back ? "← 回成績" : "← 重點卡列表"}</button><span class="muted">${l.subject === 1 ? "科目一" : "科目二"}</span></div>
      <h2>${esc(l.title)}</h2>
      <div class="card">
        ${l.points.map(([h, t, fig]) => `<div class="lesson-point"><h3>${esc(h)}</h3><p>${esc(t)}</p>${fig ? `<img class="qimg fig" src="fig/${esc(fig)}.svg" alt="示意圖（點一下放大）">` : ""}</div>`).join("")}
      </div>
      <div class="navrow">
        <button class="primary" id="go">練這個主題（${n} 題）</button>
        ${next ? `<button id="next">下一張：${esc(next.title)} →</button>` : ""}
      </div>
    `, () => {
      bind("#back", back || learnList);
      bindZoom();
      bind("#go", () => startPractice(Q.filter((q) => q.topic === key), `主題：${l.title}`, () => lesson(key, back)));
      if (next) bind("#next", () => lesson(next.key, back));
    });
  }

  // ---------- 練習選單 ----------
  function practiceMenu(mode) {
    const sets = mode === "real"
      ? [
          ["115 真題・科目一", (q) => q.src === "115真題" && q.subject === 1],
          ["115 真題・科目二", (q) => q.src === "115真題" && q.subject === 2],
          ["115 真題・兩科混合", (q) => q.src === "115真題"],
        ]
      : [
          ["全部題目隨機（真題＋樣題）", (q) => !isAI(q)],
          ["官方樣題・科目一", (q) => q.src === "官方樣題" && q.subject === 1],
          ["官方樣題・科目二", (q) => q.src === "官方樣題" && q.subject === 2],
          ["只練還沒做過的（真題＋樣題）", (q) => !isAI(q) && !seen(q.id)],
        ];
    const rows = sets.map(([name, f], i) => {
      const list = Q.filter(f);
      const left = list.filter((q) => !seen(q.id)).length;
      return `<button data-i="${i}" ${list.length ? "" : "disabled"}><span>${name}</span><span class="count">${list.length} 題・沒做過 ${left}</span></button>`;
    }).join("");
    const topics = mode === "real" ? "" : `<div class="card list"><h3>依主題練</h3>${
      Object.entries(DATA.topics).map(([k, name]) => `<button data-t="${k}"><span>${esc(name)}</span><span class="count">${Q.filter((q) => q.topic === k).length} 題</span></button>`).join("")}</div>`;
    show(`
      <div class="topbar"><button class="small" id="back">← 回首頁</button></div>
      <h2>${mode === "real" ? "⭐ 115 年真題" : "✏️ 更多練習"}</h2>
      <p class="muted">每次 ${SESSION_SIZE} 題。沒做過的先出，再出錯過的。</p>
      <div class="card list">${rows}</div>
      ${topics}
    `, () => {
      bind("#back", home);
      bindAll("[data-i]", (el) => { const [name, f] = sets[+el.dataset.i]; startPractice(Q.filter(f), name, () => practiceMenu(mode)); });
      bindAll("[data-t]", (el) => startPractice(Q.filter((q) => q.topic === el.dataset.t), `主題：${DATA.topics[el.dataset.t]}`, () => practiceMenu(mode)));
    });
  }

  // ---------- 刷題 ----------
  let sess = null;
  function orderForPractice(list) {
    const fresh = shuffle(list.filter((q) => !seen(q.id)));
    const wrong = shuffle(list.filter((q) => seen(q.id) && toReview(q.id)));
    const rest = shuffle(list.filter((q) => seen(q.id) && !toReview(q.id)));
    return fresh.concat(wrong, rest);
  }
  function startPractice(list, title, backTo, ordered) {
    const all = ordered ? list : orderForPractice(list);
    if (!all.length) { alert("這個範圍沒有題目。"); return; }
    sess = { pool: list, list: all.slice(0, SESSION_SIZE).map((q) => q.id), i: 0, right: 0, wrongIds: [], title, backTo };
    question();
  }

  function question() {
    const q = QBY[sess.list[sess.i]];
    const total = sess.list.length;
    show(`
      <div class="topbar"><button class="small" id="quit">結束</button><span class="muted">${esc(sess.title)}</span></div>
      <div class="muted">第 ${sess.i + 1} / ${total} 題・答對 ${sess.right}</div>
      <div class="progressbar"><i style="width:${(sess.i / total) * 100}%"></i></div>
      <div class="card">
        ${tagsHtml(q)}
        <div class="question">${esc(q.q)}</div>
        ${imgsHtml(q)}
        <div class="options">${q.options.map((_, i) => `<button data-o="${i}"><span class="letter">${LETTERS[i]}</span><span>${optionText(q, i)}</span></button>`).join("")}</div>
        <div class="markrow">${markBtn(q.id)}</div>
        <div id="after"></div>
      </div>
    `, () => {
      bindZoom();
      bindMarks();
      bind("#quit", () => (sess.i > 0 ? summary() : sess.backTo()));
      bindAll("[data-o]", (el) => answer(+el.dataset.o));
      keyHandler = (e) => {
        const k = e.key.toUpperCase();
        const n = "1234".indexOf(k) >= 0 ? "1234".indexOf(k) : LETTERS.indexOf(k);
        if (n >= 0) answer(n);
      };
    });
  }

  function answer(pick) {
    const q = QBY[sess.list[sess.i]];
    const ans = LETTERS.indexOf(q.answer);
    const ok = pick === ans;
    record(q.id, ok);
    if (ok) sess.right++; else sess.wrongIds.push(q.id);
    app.querySelectorAll("[data-o]").forEach((b, i) => {
      b.disabled = true;
      b.style.opacity = 1;
      if (i === ans) b.classList.add("right");
      else if (i === pick) b.classList.add("wrong");
    });
    const last = sess.i + 1 >= sess.list.length;
    app.querySelector("#after").innerHTML = `
      <div class="result ${ok ? "good" : "bad"}">${ok ? "✅ 答對了！" : `❌ 答錯了，答案是 ${q.answer}`}</div>
      ${ok && !marked(q.id) ? '<p class="muted">如果是用猜的，按上面的「🔖 標記」，這題就會留在「錯題＋標記」。</p>' : ""}
      <div class="explain"><h4>💡 白話解說</h4>${esc(q.plain)}${q.fig ? `<img class="qimg fig" src="fig/${esc(q.fig)}.svg" alt="示意圖（點一下放大）">` : ""}</div>
      <div class="tipbox">📌 一句話記：${esc(q.tip)}</div>
      ${q.official ? `<details class="official"><summary>看官方詳細解析（比較難，可以跳過）</summary><div>${esc(q.official)}</div></details>` : ""}
      <div class="navrow"><button class="primary" id="next">${last ? "看結果" : "下一題 →"}</button></div>`;
    const go = () => { if (last) summary(); else { sess.i++; question(); } };
    bind("#next", go);
    app.querySelector("#next").scrollIntoView({ behavior: "smooth", block: "end" });
    keyHandler = (e) => {
      if (e.target.closest && e.target.closest("[data-mark]")) return; // 讓標記鈕自己吃 Enter／空白鍵
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); }
    };
  }

  function summary() {
    const done = sess.wrongIds.length + sess.right;
    const pct = done ? Math.round((sess.right / done) * 100) : 0;
    const moreLeft = orderForPractice(sess.pool).length > 0;
    const markedIds = sess.list.slice(0, done).filter((id) => marked(id) && !sess.wrongIds.includes(id));
    const redoIds = sess.wrongIds.concat(markedIds);
    show(`
      <h2>這一輪結束</h2>
      <div class="card" style="text-align:center">
        <div class="score">${pct}%</div>
        <p>做了 ${done} 題，答對 ${sess.right} 題</p>
        <p class="muted">${pct >= 80 ? "很棒！保持下去 💪" : pct >= 60 ? "不錯，錯的再看一次解說就會了" : "沒關係，錯的題目都進了錯題本，多練幾次就會"}</p>
      </div>
      ${markedIds.length ? `<div class="card"><h3>這輪答對、但有標記 🔖 的題目</h3>${markedIds.map((id) => `<p>• ${esc(QBY[id].q.slice(0, 40))}…<br><span class="muted">答案 ${QBY[id].answer}：${esc(QBY[id].tip)}</span></p>`).join("")}</div>` : ""}
      ${sess.wrongIds.length ? `<div class="card"><h3>這輪答錯的題目</h3>${sess.wrongIds.map((id) => `<p>• ${esc(QBY[id].q.slice(0, 40))}…<br><span class="muted">答案 ${QBY[id].answer}：${esc(QBY[id].tip)}</span></p>`).join("")}</div>` : ""}
      <div class="navrow">
        ${redoIds.length ? `<button class="primary" id="redo">${markedIds.length ? "把錯的和標記的再做一次" : "把錯的再做一次"}</button>` : ""}
        ${moreLeft ? `<button id="more">同範圍再來 ${SESSION_SIZE} 題</button>` : ""}
        <button id="back">回上一頁</button>
      </div>
    `, () => {
      const s = sess;
      bind("#redo", () => startPractice(redoIds.map((id) => QBY[id]), markedIds.length ? "再做一次錯的和標記的" : "再做一次答錯的", s.backTo, true));
      bind("#more", () => startPractice(s.pool, s.title, s.backTo));
      bind("#back", s.backTo);
    });
  }

  // ---------- 錯題本 ----------
  function wrongBook() {
    const list = Q.filter((q) => toReview(q.id));
    const nMarked = list.filter((q) => marked(q.id)).length;
    const line = (q) => {
      const why = [inWrongBook(q.id) ? `錯 ${store.stats[q.id].w} 次` : "", marked(q.id) ? "🔖 你標記的" : ""].filter(Boolean).join("・");
      return `<div class="bookitem"><p>• ${esc(q.q.slice(0, 45))}…<br><span class="muted">答案 ${q.answer}：${esc(q.tip)}（${why}）</span></p>${marked(q.id) ? markBtn(q.id) : ""}</div>`;
    };
    show(`
      <div class="topbar"><button class="small" id="back">← 回首頁</button></div>
      <h2>❌ 錯題＋標記（${list.length} 題）</h2>
      <p class="muted">答錯的題目：同一題連續答對 2 次，就會自動移出。<br>🔖 標記的題目（現在 ${nMarked} 題）：答對也不會消失，熟了再自己按一下取消。</p>
      ${list.length ? `<button class="primary" id="go" style="width:100%">開始練這些題目</button>` : `<div class="card">目前沒有錯題，也沒有標記的題目，太厲害了！</div>`}
      <div class="card">${list.map(line).join("") || '<p class="muted">（空的）</p>'}</div>
    `, () => {
      bind("#back", home);
      bind("#go", () => startPractice(list, "錯題＋標記", wrongBook));
      bindMarks(() => wrongBook());
    });
  }

  // ---------- 模擬考 ----------
  let mock = null;
  function mockMenu() {
    const hist = store.mocks.slice(-6).reverse();
    show(`
      <div class="topbar"><button class="small" id="back">← 回首頁</button></div>
      <h2>🎯 模擬考</h2>
      <div class="card">
        <p>跟真的考試一樣：每科 ${MOCK_SIZE} 題、${MOCK_MINUTES} 分鐘，每題 2 分。</p>
        <p>考試中不會告訴你對錯，交卷後才一起檢討。</p>
        <p class="muted">題目從真題＋官方樣題裡隨機抽，每次都不一樣。想考沒看過的新題，請到首頁「🤖 AI 模擬卷」。</p>
      </div>
      <div class="menu">
        <button data-s="1"><span class="icon">1️⃣</span><span>${subjName(1)}</span></button>
        <button data-s="2"><span class="icon">2️⃣</span><span>${subjName(2)}</span></button>
      </div>
      ${hist.length ? `<div class="card"><h3>最近的成績</h3>${hist.map((m) => `<p>${m.date}　${m.subject === 1 ? "科目一" : "科目二"}${m.paper ? `（AI 第 ${m.paper} 份）` : ""}：<b>${m.score} 分</b></p>`).join("")}</div>` : ""}
    `, () => {
      bind("#back", home);
      bindAll("[data-s]", (el) => startMock(+el.dataset.s));
    });
  }

  // paper 有給就考那一份 AI 模擬卷（題目固定、順序打亂），沒給就從官方題隨機抽
  function startMock(subject, paper) {
    const list = paper ? shuffle(paper.ids) : shuffle(OFFICIAL.filter((q) => q.subject === subject)).slice(0, MOCK_SIZE).map((q) => q.id);
    mock = { subject, paper, list, ans: {}, i: 0, end: Date.now() + MOCK_MINUTES * 60000, done: false };
    mockQuestion();
  }
  const mockTitle = () => (mock.paper ? paperName(mock.paper) : subjName(mock.subject));

  // ---------- AI 模擬卷 ----------
  function aiMenu() {
    const last = (p) => store.mocks.filter((m) => m.subject === p.subject && m.paper === p.no).pop();
    show(`
      <div class="topbar"><button class="small" id="back">← 回首頁</button></div>
      <h2>🤖 AI 模擬卷</h2>
      <div class="card">
        <p>這些是 AI 讀官方學習指引後，另外出的新題目（不是官方考題），用來練習「沒看過的題目」怎麼判斷。</p>
        <p>每份 ${MOCK_SIZE} 題左右。「模擬考」跟真的考試一樣計時 ${MOCK_MINUTES} 分鐘、交卷才對答案；「練習」每題馬上看解說。</p>
        <p class="muted">答錯的一樣會進「錯題＋標記」。若解說跟官方講義不同，以官方為準。</p>
      </div>
      <div class="card">
        <h3>今年真題怎麼考（115 年 100 題分析）</h3>
        <p>• 沒有考公司、年份、人名這類冷知識；要背的只有七大技術的名稱與縮寫。</p>
        <p>• 科目一：看一段製程描述判斷是哪種技術、技術之間的比較、某設計「為什麼」這樣做、某情境選哪種技術、操作安全怎麼處置。</p>
        <p>• 科目二：幾乎都是實務判斷：參數調高調低會怎樣、看到某種缺陷怎麼修、模型怎麼擺、材料怎麼選；還有幾題看圖判斷擺放。</p>
        <p>• 數字很少，只有常用的（例如 PLA 約 190～220°C、層厚約為噴嘴直徑的一半）。約四成題目問「何者有誤／不是」，要看清楚題目。</p>
      </div>
      ${PAPERS.map((p, i) => {
        const m = last(p);
        return `<div class="card"><h3>${paperName(p)}</h3>
          <p><b>${paperNote(p.no)}</b></p>
          <p class="muted">${p.ids.length} 題${m ? `｜上次模擬考 ${m.score} 分（${m.date}）` : ""}｜練過 ${p.ids.filter(seen).length} 題</p>
          <div class="navrow"><button class="primary" data-pm="${i}">模擬考（計時）</button><button data-pp="${i}">練習（每題看解說）</button></div></div>`;
      }).join("")}
    `, () => {
      bind("#back", home);
      bindAll("[data-pm]", (el) => { const p = PAPERS[+el.dataset.pm]; startMock(p.subject, p); });
      bindAll("[data-pp]", (el) => { const p = PAPERS[+el.dataset.pp]; startPractice(p.ids.map((id) => QBY[id]), paperName(p), aiMenu); });
    });
  }

  function mockQuestion() {
    const q = QBY[mock.list[mock.i]];
    const n = mock.list.length;
    const answered = Object.keys(mock.ans).length;
    show(`
      <div class="topbar"><span class="muted">${esc(mockTitle())}</span><span class="timer" id="timer"></span></div>
      <div class="muted">第 ${mock.i + 1} / ${n} 題・已作答 ${answered}</div>
      <div class="card">
        <div class="question">${mock.i + 1}. ${esc(q.q)}</div>
        ${imgsHtml(q)}
        <div class="options">${q.options.map((_, i) => `<button data-o="${i}" class="${mock.ans[q.id] === i ? "picked" : ""}"><span class="letter">${LETTERS[i]}</span><span>${optionText(q, i)}</span></button>`).join("")}</div>
        <div class="markrow">${markBtn(q.id)}</div>
        <div class="navrow">
          <button id="prev" ${mock.i ? "" : "disabled"}>← 上一題</button>
          <button id="next" class="primary" ${mock.i < n - 1 ? "" : "disabled"}>下一題 →</button>
        </div>
      </div>
      <div class="card">
        <div class="grid-nums">${mock.list.map((id, i) => `<button data-j="${i}" class="${mock.ans[id] !== undefined ? "done" : ""} ${i === mock.i ? "cur" : ""} ${marked(id) ? "marked" : ""}">${i + 1}</button>`).join("")}</div>
        <p class="muted">題號右上角有 🔖 的，是你標記的題目，交卷前可以回去再看一次。</p>
        <div class="navrow"><button id="submit" class="primary">交卷</button><button id="giveup" class="ghost">放棄這次考試</button></div>
      </div>
    `, () => {
      bindZoom();
      bindMarks((id) => { const g = app.querySelector(`[data-j="${mock.i}"]`); if (g) g.classList.toggle("marked", marked(id)); });
      const go = (j) => { mock.i = j; mockQuestion(); };
      bindAll("[data-o]", (el) => {
        mock.ans[q.id] = +el.dataset.o;
        if (mock.i < n - 1) go(mock.i + 1); else mockQuestion();
      });
      bind("#prev", () => go(mock.i - 1));
      bind("#next", () => go(mock.i + 1));
      bindAll("[data-j]", (el) => go(+el.dataset.j));
      bind("#submit", () => {
        const left = n - Object.keys(mock.ans).length;
        if (!left || confirm(`還有 ${left} 題沒作答，確定要交卷嗎？`)) mockResult();
      });
      bind("#giveup", () => { if (confirm("確定放棄這次模擬考？不會記錄成績。")) (mock.paper ? aiMenu : mockMenu)(); });
      keyHandler = (e) => {
        const k = e.key.toUpperCase();
        const o = "1234".indexOf(k) >= 0 ? "1234".indexOf(k) : LETTERS.indexOf(k);
        if (o >= 0) app.querySelectorAll("[data-o]")[o].click();
        else if (e.key === "ArrowRight" && mock.i < n - 1) go(mock.i + 1);
        else if (e.key === "ArrowLeft" && mock.i > 0) go(mock.i - 1);
      };
      tick();
      timerId = setInterval(tick, 1000);
    });
  }

  function tick() {
    const ms = mock.end - Date.now();
    const el = document.getElementById("timer");
    if (ms <= 0) { stopTimer(); alert("時間到！自動交卷。"); mockResult(); return; }
    const m = Math.floor(ms / 60000), s = Math.floor((ms % 60000) / 1000);
    if (el) { el.textContent = `⏱ ${m}:${String(s).padStart(2, "0")}`; el.classList.toggle("warn", m < 10); }
  }

  // 各主題答對率：最弱的排最上面，可直接去看那個主題的重點卡
  function topicCard(ids, isRight) {
    const rows = {};
    ids.forEach((id) => {
      const t = QBY[id].topic;
      const r = rows[t] || (rows[t] = { t, n: 0, ok: 0 });
      r.n++;
      if (isRight(id)) r.ok++;
    });
    const list = Object.values(rows).sort((a, b) => a.ok / a.n - b.ok / b.n || b.n - a.n);
    return `<div class="card"><h3>各主題答對率</h3>
      <p class="muted">最弱的排在最上面。先把紅色主題的重點卡看懂，再回來考。</p>
      ${list.map((r) => {
        const pct = Math.round((r.ok / r.n) * 100);
        const lv = pct >= 70 ? "good" : pct >= 50 ? "mid" : "bad";
        return `<div class="trow"><div class="tname">${esc(DATA.topics[r.t])}<span class="muted">　${r.ok}/${r.n} 題</span></div>
          <div class="tbar"><i class="${lv}" style="width:${pct}%"></i></div><b class="${lv}">${pct}%</b>
          <button class="small" data-lesson="${esc(r.t)}">看重點</button></div>`;
      }).join("")}</div>`;
  }

  function mockResult() {
    if (!mock.done) {
      mock.done = true;
      mock.list.forEach((id) => { if (mock.ans[id] !== undefined) record(id, LETTERS[mock.ans[id]] === QBY[id].answer); });
      const right = mock.list.filter((id) => LETTERS[mock.ans[id]] === QBY[id].answer).length;
      mock.score = Math.round((right / mock.list.length) * 100);
      mock.right = right;
      store.mocks.push(Object.assign({ date: today(), subject: mock.subject, score: mock.score }, mock.paper ? { paper: mock.paper.no } : {}));
      save();
    }
    const wrong = mock.list.filter((id) => LETTERS[mock.ans[id]] !== QBY[id].answer);
    const markedRight = mock.list.filter((id) => LETTERS[mock.ans[id]] === QBY[id].answer && marked(id));
    const msg = mock.score >= 70 ? "這科穩了！🎉" : mock.score >= 60 ? "這科及格了，但兩科平均要 70，再拚一點" : "還差一點，把下面錯的看懂再考一次";
    show(`
      <h2>模擬考成績・${esc(mockTitle())}</h2>
      <div class="card" style="text-align:center">
        <div class="score" style="color:${mock.score >= 70 ? "var(--good)" : mock.score >= 60 ? "#c98a00" : "var(--bad)"}">${mock.score} 分</div>
        <p>答對 ${mock.right} / ${mock.list.length} 題</p>
        <p>${msg}</p>
      </div>
      ${topicCard(mock.list, (id) => LETTERS[mock.ans[id]] === QBY[id].answer)}
      <div class="card"><div class="grid-nums">${mock.list.map((id, i) => `<button data-j="${i}" class="${LETTERS[mock.ans[id]] === QBY[id].answer ? "right" : "wrong"} ${marked(id) ? "marked" : ""}">${i + 1}</button>`).join("")}</div>
        <p class="muted">綠色答對、紅色答錯，右上角有 🔖 的是你標記的。點題號可以看那題的解說。</p></div>
      ${markedRight.length ? `<h3>答對、但你有標記 🔖 的題目（${markedRight.length} 題）</h3>${markedRight.map((id) => reviewCard(id)).join("")}` : ""}
      <h3>答錯的題目（${wrong.length} 題）</h3>
      ${wrong.map((id) => reviewCard(id)).join("")}
      <div class="navrow"><button class="primary" id="again">再考一次</button><button id="back">回首頁</button></div>
    `, () => {
      bindZoom();
      bindMarks((id) => { const g = app.querySelector(`[data-j="${mock.list.indexOf(id)}"]`); if (g) g.classList.toggle("marked", marked(id)); });
      bind("#again", () => startMock(mock.subject, mock.paper));
      bindAll("[data-lesson]", (el) => lesson(el.dataset.lesson, mockResult));
      bind("#back", home);
      bindAll("[data-j]", (el) => mockReview(+el.dataset.j));
    });
  }

  function reviewCard(id) {
    const q = QBY[id];
    const mine = mock.ans[id];
    return `<div class="card">
      ${tagsHtml(q)}
      <div class="question">${esc(q.q)}</div>
      ${imgsHtml(q)}
      <div class="options">${q.options.map((_, i) => `<button disabled style="opacity:1" class="${LETTERS[i] === q.answer ? "right" : i === mine ? "wrong" : ""}"><span class="letter">${LETTERS[i]}</span><span>${optionText(q, i)}</span></button>`).join("")}</div>
      <p class="muted">${mine === undefined ? "你沒有作答" : `你選 ${LETTERS[mine]}`}，答案是 ${q.answer}</p>
      <div class="explain"><h4>💡 白話解說</h4>${esc(q.plain)}${q.fig ? `<img class="qimg fig" src="fig/${esc(q.fig)}.svg" alt="示意圖（點一下放大）">` : ""}</div>
      <div class="tipbox">📌 一句話記：${esc(q.tip)}</div>
      <div class="markrow">${markBtn(id)}</div>
    </div>`;
  }

  function mockReview(j) {
    show(`
      <div class="topbar"><button class="small" id="back">← 回成績</button><span class="muted">第 ${j + 1} 題</span></div>
      ${reviewCard(mock.list[j])}
      <div class="navrow">
        <button id="prev" ${j ? "" : "disabled"}>← 上一題</button>
        <button id="next" ${j < mock.list.length - 1 ? "" : "disabled"}>下一題 →</button>
      </div>
    `, () => {
      bindZoom();
      bindMarks();
      bind("#back", mockResult);
      bind("#prev", () => mockReview(j - 1));
      bind("#next", () => mockReview(j + 1));
    });
  }

  home();
})();
