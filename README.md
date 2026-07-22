# 🎰 Pachislot Little Mary Edition（小瑪莉パチスロ）

一款純前端、免安裝的日式老虎機（パチスロ）瀏覽器遊戲，靈感來自日本經典小瑪莉（Little Mary）機台。  
**單一 HTML 檔案即可執行**，無需後端、無需 Node.js，雙擊即玩。

---

## ✨ 遊戲特色

- **27 線全盤規則**：三個滾輪各出現相同圖標即中獎（不限上中下位置）
- **14 種圖標**：Wild 萬用牌、3 種 Free Spin 觸發符號、10 種一般圖標
- **3 輪不等長物理輪帶**：L = 125 / 144 / 169（三個 coprime → **LCM = 組合數 = 3,042,000**），**11 種圖案（10 reg + Wild）都有前綴 cluster、都可打到 27 線滿盤**（iter7）
- **小瑪莉 Bonus Game**：觸發後進入 16 格環狀跑馬燈，停格獲得倍率獎金
- **神秘大獎（Mystery ❓）**：特殊格觸發轉盤，贏取 75～250× 高額獎金
- **天氣粒子特效**：Bonus 期間金幣雨飄落、每分鐘隨機數字爆發特效
- **背景震動演出**：每 3 分鐘觸發機台震動（非 Bonus 期間）
- **鍵盤快捷鍵**：`Enter` 開轉 / `Space` 依序停輪
- **5 段下注額**：100、200、500、1000、1500
- **完整校準工具鏈**：`rtp_sim.py` 內建 analytic RTP 閉式解 + Monte Carlo + HL Loop 校準 + 100K 玩家模擬（破產率 / spins-to-bust 分佈 / 期末結餘）；**iter6 起加 `exact_moments.py`** 用 Law of Total Variance 對 3M outcome 精確枚舉，同時給 σ / CV / P(X=0) / per-symbol per-line-count 分佈

---

## 🕹️ 操作說明

| 操作 | 功能 |
|------|------|
| `Enter` | 開始轉動所有滾輪 |
| `Space` | 依序停止第 1 → 2 → 3 滾輪；Bonus 中停止指示燈 |
| STOP 1 / 2 / 3 按鈕 | 個別手動停止對應滾輪 |
| `+` / `-` 按鈕 | 調整下注額 |
| 增加籌碼 按鈕 | 補充 +5,000 信用點數 |
| STOP（Bonus 中） | 停止小瑪莉跑馬燈 / 神秘轉盤 |

---

## 🃏 圖標賠率表

> 賠率以下注 **100** 為基準；實際獎金 ＝ 賠率倍數 × (下注額 ÷ 100)

| 圖標 | 名稱 | 賠率倍數 | 出現權重 | 特殊功能 |
|:----:|------|:-------:|:-------:|---------|
| 🃏 | Wild | **220×** | 3 | 替代所有非 FS 圖標；3 輪各 3 張 Wild 同停 offset=30 觸發 27 線 Wild 大獎（機率 3.29e-7），累加所有 reg 通配線 → 單擊最大 27,540 |
| 🔴 | Red 7 | — | 7 | 觸發小瑪莉 **×2 倍率**，10 次 |
| 🔵 | Blue 7 | — | 4 | 觸發小瑪莉 **×3 倍率**，10 次 |
| 🟡 | Gold 7 | — | 2 | 觸發小瑪莉 **×5 倍率**，10 次 |
| 🎰 | BAR | **180×** | 2 | — |
| 👑 | Crown | **130×** | 3 | — |
| 💎 | Diamond | **110×** | 4 | — |
| 🔔 | Bell | **80×** | 5 | — |
| 🍉 | Watermelon | **70×** | 6 | — |
| 🍇 | Grape | **60×** | 7 | — |
| 🍊 | Orange | **50×** | 8 | — |
| 🍋 | Lemon | **45×** | 9 | — |
| 🍒 | Cherry | **40×** | 10 | — |
| 🍀 | Clover | **35×** | 12 | — |

> **Wild 規則**：可替代任何一般圖標（不能替代 Free Spin 符號）  
> **中獎計算**：若多個位置同時符合，獎金以「配對線數 × 賠率倍數」疊加

---

## 🎉 小瑪莉 Bonus Game

### 觸發條件
三輪同時各出現至少一個相同 Free Spin 符號（🔴 / 🔵 / 🟡）

### Bonus 玩法
1. 進入 **16 格環狀跑馬燈**（Little Mary Track）
2. 燈光自動在格子間循環移動
3. 按 `STOP` 或 `Space` 停止，依落格獲得獎勵：

| 格子類型 | 獎勵 |
|---------|------|
| 💰 普通獎格 | 10 / 15 / 20 / 30 / 50 / 70 × 下注額 × FS 倍率 |
| 💵 大獎格 | 100 × 下注額 × FS 倍率 |
| 👑 頂獎格 | 150 × 下注額 × FS 倍率 |
| ❓ 神秘格 | 觸發轉盤：75 / 100 / 150 / 200 / 250 中停止，再乘 FS 倍率 |

### Bonus 倍率
| 觸發圖標 | 倍率 | 次數 |
|---------|:---:|:---:|
| 🔴 Red 7 | ×2 | 10 次 |
| 🔵 Blue 7 | ×3 | 10 次 |
| 🟡 Gold 7 | ×5 | 10 次 |

10 次消耗完畢後自動結束 Bonus，回到一般遊戲模式。

---

## 🌟 特效系統

| 特效 | 觸發時機 |
|------|---------|
| 💵 金幣雨 | 進入 Bonus Game 期間持續飄落 |
| 🔢 數字爆發 | Bonus 中每 60 秒隨機爆出 10～20 個彩色數字 |
| 📳 機台震動 | 非 Bonus 時，每 3 分鐘震動 1～5 次 |

---

## 🚀 快速開始

不需要任何安裝！直接用瀏覽器開啟：

```bash
# macOS
open pachislot_mali.html

# Windows（直接雙擊，或命令列）
start pachislot_mali.html

# Linux
xdg-open pachislot_mali.html
```

或部署至靜態托管服務（GitHub Pages、Netlify、Vercel）一鍵上線。

---

## 🛠️ 技術規格

| 項目 | 說明 |
|------|------|
| 語言 | 純 HTML5 + CSS3 + Vanilla JavaScript (ES6+) |
| 依賴 | 零依賴，無任何第三方套件 |
| 相容性 | Chrome / Firefox / Edge / Safari（現代版本） |
| 檔案 | 單一 `.html`，全部邏輯、樣式、腳本一體 |

---

## 📂 專案結構

```
pachislot_mali/
├── pachislot_mali.html            # 遊戲主體（含所有邏輯 + REEL_STRIPS iter7 上線版）
├── rtp_sim.py                     # 引擎 + analytic RTP + MC + HL 校準 + 玩家模擬（iter0-5 核心）
├── exact_moments.py               # iter6+：Law of Total Variance 精確枚舉 3M outcome
├── iter6_wild_open.py             # iter6 實驗：撤 Wild max cluster + Wild payout=200
├── iter7_wild_cluster.py          # iter7 上線版：加 Wild cluster prefix + Wild payout=220
├── tuned_strips.json              # iter5 結果（RTP 96%）
├── tuned_strips_iter6.json        # iter6 結果（RTP 93.43%, σ=254.65）
├── tuned_strips_iter7.json        # iter7 結果（RTP 93.44%, σ=308.48，上線）
├── VERSION_LOG.md                 # 完整 iter0-7 校準日誌
└── README.md                      # 本說明文件
```

---

## 🧮 RTP 校準：HL Loop 設計與執行

### 為什麼要 HL 校準

原始 `pachislot_mali.html` 用獨立 weighted random（`getRandomSymbol()` × 9），實測 RTP 僅 **50.96%** —— 遠低於北美賭場 92–98% 與日式パチスロ規制 55–97.5% 下限。改成物理輪帶後用 **HL Loop** 校準，並確保 27 線可達 + 三種 Bonus 都能觸發。

> 📌 **iter7 update (2026-07-22 上線版)**：撤 Wild max cluster limit + 加 Wild cluster prefix 讓 Wild 27 線可觸發（機率 3.29e-7 = 1/(L₁·L₂·L₃)） + Wild payout=220 + HL target 拉到 93.5%（92-95% 區間中點）。上線 exact enumeration 驗證 **total RTP=93.4446% / σ=308.48 / P(X=0)=64.46%**。詳見 [`VERSION_LOG.md`](VERSION_LOG.md) iter7。
>
> **關鍵發現（iter6）**：Analytic Base RTP **≡** Exact Base RTP（per-symbol 精確到小數 4 位），因為 $\mathbb{E}[m_1 m_2 m_3] = \prod \mathbb{E}[m_r]$ 只需 reel 間獨立、reel 內 3 格不必獨立。Wild 相關性只影響 σ 不影響 mean。iter0-5 記錄的「analytic vs MC 差 1.4pp」是 MC 雜訊+bonus 近似殘留，非 base 有偏差。
>
> **σ ⇔ RTP decouple**：iter6→iter7 RTP 幾乎沒變（+0.02pp）但 σ +21%——同 house edge 玩家體感截然不同，屬遊戲設計選擇。
>
> 以下 iter0/iter1 章節保留為歷史紀錄。

### RTP 拆解與計算公式

**符號設定**

- 3 輪物理輪帶 $r \in \{0, 1, 2\}$，每輪長度 $L_r$
- 每輪符號組成 $c_{s,r}$ = 符號 $s$ 在輪 $r$ 出現次數
- 每 spin 動畫停止時顯示每輪 3 連續 slot 窗口，共 3×3=9 格盤面
- 下注 base $B=100$；一般 payout 表以 $B=100$ 為單位

**核心近似**：3 個 row 假設為 pattern-independent 抽樣。物理輪帶下 3 row 實為連續三格，非嚴格獨立；但 strip 已充分打散且 $\max c \ll L$ 時（本專案 $\sim 15/108$），誤差 $\sim 1\%$ 級。HL 用這個 closed form 跑得快（毫秒級），MC 再驗證真值。

#### 🎯 Base RTP（27 線常規中獎）

「27 線全盤」規則：對符號 $s$，中獎線數 $= m_0 \cdot m_1 \cdot m_2$，其中 $m_r$ 為輪 $r$ 窗口中「match $s$」的格數。**Wild 通配**：非-FS 符號 $s$ 的 match 條件為 `sid == s OR sid == WILD`。

**每輪匹配機率**：

$$p_{\text{match}}(r, s) = \frac{c_{s,r} + c_{\text{WILD},r}}{L_r}$$

**單輪期望匹配數**（3 個 row 各自獨立以 $p$ 命中）：

$$\mathbb{E}[m_r] = 3 \cdot p_{\text{match}}(r, s)$$

**3 輪聯合期望線數**（reel 間獨立）：

$$\mathbb{E}[\text{lines}_s] = \prod_{r=0}^{2} \mathbb{E}[m_r] = 27 \prod_{r=0}^{2} p_{\text{match}}(r, s)$$

**Base RTP 閉式解**（sum over reg symbols）：

$$\boxed{\text{RTP}_{\text{base}} = \sum_{s \in \text{REG}} \frac{27 \cdot \text{payout}_s}{B} \cdot \prod_{r=0}^{2} \frac{c_{s,r} + c_{\text{WILD},r}}{L_r}}$$

#### 🎉 Bonus RTP（Free Spin 觸發 × Mali round）

**FS 每輪至少 1 張**（iter5 起，`make_strip_v4` 保證同種 FS 環狀最小距離 ≥ 3 → 兩個相同 FS 不共享任何 3-slot 窗口 → 覆蓋率精確）：

$$P_{\text{reel}}(r, y) = \min\left(\frac{3 c_{y,r}}{L_r},\ 1\right)$$

> **iter1–iter4 舊公式**：$1 - (1 - c_{y,r}/L_r)^3$（獨立抽樣近似）。iter4 因為沒 spread constraint、FS 在 shuffle tail 局部聚集，此公式高估 P_reel（reel 0 FS1 empirical/analytic = 0.83）→ analytic-MC gap 到 −2.62pp。iter5 補完 spread + 換公式後 gap 收斂到 0.03pp。

**3 輪全部滿足才 match**：

$$P_{\text{match}}(y) = \prod_{r=0}^{2} P_{\text{reel}}(r, y)$$

**優先權排他**：JS `checkWin` 內 `fsMode` guard 讓 FS 只能同時觸發一種；程式跑順序為 FS1 → FS2 → FS3，所以：

$$P_{\text{trigger}}(y_1) = P_{\text{match}}(y_1)$$

$$P_{\text{trigger}}(y_2) = P_{\text{match}}(y_2) \cdot \bigl(1 - P_{\text{match}}(y_1)\bigr)$$

$$P_{\text{trigger}}(y_3) = P_{\text{match}}(y_3) \cdot \bigl(1 - P_{\text{match}}(y_1)\bigr) \cdot \bigl(1 - P_{\text{match}}(y_2)\bigr)$$

**Mali round 期望值（bet 100、mult 1）**：

layout = 2 固定格（`100`、`150`）+ 1 mystery 格 + 13 個從 `MALI_PRIZES = [10,15,20,30,50,70]` 隨機抽的一般格；每次 uniform 隨機停 1 格。Mystery 命中時再從 `MYSTERY_PRIZES = [75,100,150,200,250]` uniform 抽 1：

$$E_{\text{mystery}} = \tfrac{1}{5}(75+100+150+200+250) = 155$$

$$E_{\text{cell}} = \tfrac{1}{6}(10+15+20+30+50+70) = 32.5$$

$$E_{\text{mali\_val}} = \frac{100 + 150 + E_{\text{mystery}} + 13 \cdot E_{\text{cell}}}{16} = \frac{827.5}{16} \approx 51.72$$

**Bonus RTP 閉式解**（每 FS 種類的觸發率 × 固定 spin 數 × Mali 期望 × FS 倍率）：

$$\boxed{\text{RTP}_{\text{bonus}} = \sum_{y \in \text{FS}} P_{\text{trigger}}(y) \cdot n_{\text{spins}}(y) \cdot E_{\text{mali\_val}} \cdot \frac{\text{fs\_mult}(y)}{B}}$$

其中 $n_{\text{spins}}(y) = 10$ (三種 FS 一致)，$\text{fs\_mult} \in \{2, 3, 5\}$（Red/Blue/Gold 7）。

#### 🧮 Total & Monte Carlo 校核

$$\text{RTP}_{\text{total}} = \text{RTP}_{\text{base}} + \text{RTP}_{\text{bonus}}$$

**MC 補角色**：analytic 假設 3 row 獨立，物理輪帶連續三格會微幅低估 Wild cluster 帶來的「3 wild 同視窗」機率（iter1/iter2 有 Wild cluster 時 MC > analytic 約 1pp；iter3 打散 wild 後兩者差 −0.5pp）。所以：
- **HL 校準跑 analytic**（快，毫秒級 per iter）
- **驗收跑 MC**（正確反映物理輪帶語意）
- 玩家模擬用 MC 精神（`_fast_spin_win` 內 offset 隨機抽 → 查 3 輪預算表 → 展 FS session）

> **iter6 更正（2026-07-22）**：以上「MC > analytic 1pp」的直覺**只對總 RTP 的 bonus 部分**成立。對 **base RTP**，exact enumeration 顯示 Δ = +0.0000pp（per-symbol 到小數 4 位完全等價），因為 $\mathbb{E}[m_1 m_2 m_3] = \prod \mathbb{E}[m_r]$ 只需 reel 間獨立、reel 內獨立不必要。Wild 相關性影響的是 **Var / skew / kurtosis / per-line-count 分佈形狀**，不影響一階動差。詳見下方 exact enumeration 章節與 [`VERSION_LOG.md`](VERSION_LOG.md) iter6。

#### 🎯 Exact Enumeration × Variance（iter6+ 加入）

`exact_moments.py` 對 $L_1 \times L_2 \times L_3 = 3{,}042{,}000$ 個 offset triple **精確枚舉**，同時算 RTP + σ + CV + P(X=0) + per-symbol per-line-count 頻率。

**設計切分**：outer 是確定性、inner 是隨機

- **outer**：3-reel window 組合有限，枚舉每個 outcome 都得 base_win + 是否觸發 FS_i
- **inner**：對每種 fs_mult 各跑 MC 500k Mali session 得 $(\mu_i, \sigma_i^2)$ 常數

**合體用 Law of Total Variance**：

$$\operatorname{Var}(X) = \mathbb{E}_o\bigl[\operatorname{Var}(X \mid o)\bigr] + \operatorname{Var}_o\bigl(\mathbb{E}[X \mid o]\bigr)$$

- no-FS outcome：$\mathbb{E}[X \mid o] = \text{base\_win}$，$\operatorname{Var}[X \mid o] = 0$
- FS_i outcome：$\mathbb{E}[X \mid o] = \text{base\_win} + \mu_i$，$\operatorname{Var}[X \mid o] = \sigma_i^2$

單次成本：bonus MC 500k ≈ 28s + exact enumeration ≈ 15s（純 Python，可 numpy vectorize 到 <1s）。

**執行**：

```bash
PYTHONUTF8=1 python exact_moments.py --source html --focus S9   # 對現行 HTML 跑
PYTHONUTF8=1 python exact_moments.py --source json --focus WILD # 對 tuned_strips.json 跑
```

#### 📐 iter5 代入實例

以 reel 0 的 🎰 BAR（$s = \text{S0}$、$\text{payout}_{S0} = 180$，最高 payout 符號）為例：

| 參數 | reel 0 | reel 1 | reel 2 |
|------|:---:|:---:|:---:|
| $L_r$ | 125 | 144 | 169 |
| $c_{S0,r}$ | 3 | 4 | 4 |
| $c_{\text{WILD},r}$ | 13 | 13 | 10 |
| $p_{\text{match}}(r, S0)$ | 16/125 = 0.128 | 17/144 ≈ 0.118 | 14/169 ≈ 0.0828 |

$$\mathbb{E}[\text{lines}_{S0}] = 27 \times 0.128 \times 0.118 \times 0.0828 \approx 0.0338$$

$$\text{RTP}_{S0} = 0.0338 \times 180 / 100 \approx 6.1\%$$

10 個 reg 加總 → **analytic base RTP ≈ 72.76%**（與 MC 72.70% 差 0.06pp）。

**FS1（🔴 Red 7）觸發率（iter5 spread ceiling 公式）**：
- reel 0: $c=11$, $L=125$ → $P_{\text{reel}} = 3 \times 11 / 125 = 0.264$
- reel 1: $c=12$, $L=144$ → $P_{\text{reel}} = 3 \times 12 / 144 = 0.250$
- reel 2: $c=15$, $L=169$ → $P_{\text{reel}} = 3 \times 15 / 169 \approx 0.266$
- $P_{\text{trigger}}(\text{FS1}) = 0.264 \times 0.250 \times 0.266 \approx 0.01756$ ≈ **1.756%**（與 MC 1.757% 完全對齊）

**iter5 total gap**：analytic 96.00% vs MC 95.97% → **−0.03pp**（iter4 曾 −2.62pp，87× 收斂）。

**合計** $\text{RTP}_{\text{total}} = 80.50\% + 16.00\% = 96.50\%$，落在 target 95–97% 內 ✓

### HL Heuristic System 對映

| HS 元件 | 本專案實體 |
|---------|------------|
| **state** | `counts_per_reel`：3 輪 × 14 符號的組成 |
| **policy** | `hl_single_swap_search()` — 枚舉 (reel, from_sym, to_sym) 三元組，選最能收斂 gap 的 swap |
| **feedback** | `analytic_rtp_from_counts()` — 解析式 base/bonus/per-symbol/FS-trigger 分解 |
| **memory** | history list + `tuned_strips.json` |
| **regression** | `min_wild_per_reel=3`（27 線可達）+ `min_fs_per_reel=1`（三種 Bonus 都能觸發） |

Policy 是**人類可讀的 swap 規則**，不是黑箱 weights。詳見 [`VERSION_LOG.md`](VERSION_LOG.md) 與 wiki [[concept_heuristic_learning]]、[[concept_slot_rtp_calibration_hl]]。

### HL 執行過程

#### iter0（無 constraint）— 5 步收斂

| iter | swap | RTP |
|------|------|-----|
| 0 | reel 0: −Diamond +Wild | 50.96% → 57.90% |
| 1 | reel 1: −Diamond +Wild | 57.90% → 66.91% |
| 2 | reel 2: −Diamond +Wild | 66.91% → 78.68% |
| 3 | reel 0: −Watermelon +Wild | 78.68% → 89.76% |
| 4 | reel 0: −Red 7 +Wild | 89.76% → 95.61% ✅ |

**但發現致命問題**：3 輪 Wild 分別 4/2/2 個且散開 → 每輪窗口最多 1 張 Wild → 每符號 max 匹配數 1~3 → 遊戲號稱 27 線但**實際 max 只有 12 線（Clover）**，BAR 180 賠率符號甚至只有 2 線 → **輪帶等於欺騙**。

#### iter1（加 27 線可達 constraint）— 12 步收斂

**Policy 程式碼改動**（HL 精神：failure → 加 constraint → 重跑）：
1. 加 `min_wild_per_reel=3` + `make_strip_with_wild_cluster()` 把每輪前 3 slot 固定為 Wild 群
2. 加 `min_fs_per_reel=1` 保證每輪每種 FS 至少 1 張（iter1 第一次跑時 HL 為省 RTP 把 FS1/FS3 從某輪清零 → Bonus 觸發率變 0，被 regression 抓到補上）

Baseline 補 Wild 到 120.37% → HL 反向 swap 收斂：

| iter | swap | RTP |
|------|------|-----|
| 0–2 | reel 0: −3× Red 7 +3× Cherry | 120.37% → 109.17% |
| 3–5 | reel 0: −3× Grape +3× Cherry | 109.17% → 103.81% |
| 6–7 | reel 1: −2× Red 7 +2× Grape | 103.81% → 101.27% |
| 8–10 | reel 2: −2× Cherry −1× BAR +3× Red 7 | 101.27% → 96.80% |
| 11 | reel 0: −1× Crown +1× Blue 7 | 96.80% → 96.02% ✅ |

### 校準結果（iter5 三層 vs iter7 上線版）

**iter5（歷史，target 0.96）**：

| 度量 | Analytic | Python MC 200k | Player sim ~230M |
|------|:---:|:---:|:---:|
| **Total RTP** | **96.00%** | **95.97%** | **96.01%** |
| Base | 72.76% | 72.70% | — |
| Bonus | 23.24% | 23.27% | — |

gap 0.03pp 屬 MC 統計 noise 級別。

**iter7（上線版，target 0.935）**：

| 度量 | Analytic | **Exact enumeration** | Player sim ~107M |
|------|:---:|:---:|:---:|
| **Total RTP** | **93.485%** | **93.4446%** | 90.68% (截斷) |
| Base | 69.85% | 69.68% | — |
| Bonus | 23.63% | 23.76% | — |
| **σ** | — | **308.48** | — |
| **CV** | — | **3.30** | — |
| **P(X=0)** | — | **64.46%** | — |

iter7 用 exact enumeration 直接得精確值，MC 只用來對照 & 生 bonus 條件變異。

### 📊 iter6-7 σ 與變異度分析（exact_moments 新增能力）

exact_moments.py 對 3M outcome 精確枚舉 + Law of Total Variance，一次算完 RTP 的所有動差。iter7 上線版 σ 分佈長這樣：

| 動差 | 值 | 業界對照 |
|------|:---:|:---:|
| E[X] (bet=100) | 93.4446 | RTP 93.44% |
| **σ (單 spin sd)** | **308.48** | 高變異（>250 屬 high volatility） |
| CV (σ/E) | 3.30 | 遠高於低變異機（<1.5） |
| Vol Idx (σ/bet) | 3.08 | 分類參考 |
| P(X=0) | 64.46% | 空盤率高（低變異機一般 <50%） |
| P(X > 100) | 24.4% | 中獎超過本金的機率 |

**iter6 vs iter7 σ 對照**（Wild cluster 效應）：

| | iter6 | iter7 | Δ | 意義 |
|---|:---:|:---:|:---:|---|
| RTP | 93.43% | 93.44% | +0.02pp | **幾乎不變** |
| σ | 254.65 | 308.48 | **+21.1%** | 分佈更寬 |
| P(X=0) | 60.60% | 64.46% | +3.9pp | 更多空盤 |
| 單擊最大 | 7,150 | 21,600 | +202% | 頭獎爆炸 |

**這是 σ ⇔ RTP decouple**：同一個 house edge（6.55%），Wild cluster 把 payoff 分佈的高 k 尾巴放大——中位玩家死更早、q90 玩家撐更久、單次最大 3 倍。$\mathbb{E}[X]$ 靠 $P(k)\cdot k$ 對稱抵消不變，$\mathbb{E}[X^2]$ 靠 $P(k)\cdot k^2$ 高 k 貢獻放大 → σ 拉升。

**設計哲學意義**：如果目標是「玩家體感 volatility」，光看 RTP 不夠——σ 才是玩家爽感的實體。iter6 的 σ=255 是「穩定 grinder」設定，iter7 的 σ=308 是「賭爆點」設定，兩者 house edge 完全一樣。

### 玩家模擬（iter7 上線版：100K × 起始 10K × bet 100 × cap 30K spin）

| 指標 | iter7 | iter6（對照） |
|------|:---:|:---:|
| 破產玩家 | **100,000 / 100,000 (100.00%)** | 100,000 (100%) |
| 觸 cap 未破產 | 0 | 0 |
| lifetime RTP | 90.68% | 90.90% |
| **單擊最大 win** | **21,600 credits** | 7,150 |

（破產率 100% 因 RTP<100%，只要 cap 拉夠長長期必然破產；iter5 的 96.53% 是因為 cap 只 10K 有玩家沒燒完）

**破產 spin 分佈**（僅破產玩家）：

| 分位數 | iter7 | iter6 |
|-------|:---:|:---:|
| q10 | 322 | 367 |
| q25 | 463 | 525 |
| **median** | **752** | 829 |
| q75 | 1,299 | 1,358 |
| q90 | 2,170 | 2,138 |
| mean | 1,067 | 1,093 |

**期末結餘分佈**（全 100K 含破產者 = 0）：

| 分位數 | balance |
|-------|:---:|
| q10 | ~0 |
| median | 55 |
| q90 | 90 |
| top-1% | ~95 |
| mean | 52 |

（cap 30K 內全部破產，期末結餘幾乎全 0，未來 iter 拉更大 cap 或加 stop-loss policy 才能看到 top-tail）

**σ ⇔ RTP decouple 體感**：iter6 到 iter7 total RTP 幾乎不變（+0.02pp），但 **σ +21.1%**（254.65 → 308.48）——中位玩家死得早（−9.3%），q90 幸運兒撐更久（+1.5%），單次最大 win **7,150 → 21,600（+202%）**。同一個 house edge，玩家體感截然不同：iter6 是「溫和穩定」，iter7 是「高爆點高變異」。這個 decouple 是 Wild cluster 效應——把 payoff 分佈的高 k 尾巴放大，$\mathbb{E}[X^2]$ 靠 $P(k)\cdot k^2$ 而 $k^2$ 對高 k 敏感度大，所以 σ 拉升但 $\mathbb{E}[X]$ 靠對稱抵消不變。

### FS 觸發期望 spin 數（iter7 exact，幾何分佈）

| FS 符號 | 單 spin 觸發率 | E[N] | 中位數（50%） | 90 分位 |
|---------|:--------------:|:----:|:-------------:|:-------:|
| 🔴 Red 7 (×2) | **1.7574%** | ~57 | 39 | 131 |
| 🔵 Blue 7 (×3) | **0.2918%** | ~343 | 237 | 789 |
| 🟡 Gold 7 (×5) | **0.0426%** | ~2,347 | 1,626 | 5,404 |

**解讀**：Red 7 高頻率觸發（100 spin 內約 83% 玩家會遇到）；Blue 7 中位 237 spin；Gold 7 中位 1,626 spin（100K 玩家模擬 median 破產 752 spin → **中位玩家整場沒看過 Gold 7**，只有 top-tail 玩家會遇到）。iter5→iter7 微幅差異來自 tuned counts 微調（FS1 從 11/12/15→11/12/15，FS3 從 3/4/4→3/4/4）。

### 27 線可達性（iter7 現況）

每輪前 33 slot 為 10 個 reg 各自 3-slot cluster + Wild 3-slot cluster → 每種都是 max=3 on 每輪 → **11 種都可達 27 線 ✅**：

| 符號 | reel 0 | reel 1 | reel 2 | 最大線數 | offset |
|------|:---:|:---:|:---:|:---:|:---:|
| 🎰 BAR | 3 | 3 | 3 | **27 ✅** | 0 |
| 👑 Crown | 3 | 3 | 3 | **27 ✅** | 3 |
| 💎 Diamond | 3 | 3 | 3 | **27 ✅** | 6 |
| 🔔 Bell | 3 | 3 | 3 | **27 ✅** | 9 |
| 🍉 Watermelon | 3 | 3 | 3 | **27 ✅** | 12 |
| 🍇 Grape | 3 | 3 | 3 | **27 ✅** | 15 |
| 🍊 Orange | 3 | 3 | 3 | **27 ✅** | 18 |
| 🍋 Lemon | 3 | 3 | 3 | **27 ✅** | 21 |
| 🍒 Cherry | 3 | 3 | 3 | **27 ✅** | 24 |
| 🍀 Clover | 3 | 3 | 3 | **27 ✅** | 27 |
| 🃏 **Wild** | 3 | 3 | 3 | **27 ✅** ⭐ | **30** (iter7 新增) |

**Roy spec「所有圖案都要有 27 線機會」達成**，且 iter7 加碼把 Wild 也放進來。每種的目押 offset 見上表。

**iter7 現行 11 種 jackpot 對照**（3 輪同停對應 offset 都觸發該符號 27 線；純理論機率 = 1/(L₁·L₂·L₃) = 3.29e-7 每種，約 300 萬次一次）：

| 符號 | offset | jackpot @ bet 100 |
|:----:|:---:|:---:|
| 🎰 BAR | 0 | 4,860 |
| 👑 Crown | 3 | 3,510 |
| 💎 Diamond | 6 | 2,970 |
| 🔔 Bell | 9 | 2,160 |
| 🍉 Watermelon | 12 | 1,890 |
| 🍇 Grape | 15 | 1,620 |
| 🍊 Orange | 18 | 1,350 |
| 🍋 Lemon | 21 | 1,215 |
| 🍒 Cherry | 24 | 1,080 |
| 🍀 Clover | 27 | 945 |
| 🃏 **Wild (iter7)** | **30** | **27,540 ⭐** |

**Wild jackpot 27,540 = 5,940（27 × 220 Wild 自賠）+ 21,600（27 × (180+130+...+35) 所有 reg 通配累加）**，是全機頂級大獎，是 BAR 5.66× 的 upside。iter7 加入 Wild cluster 讓這個此前不可能的 outcome 首次成為玩家目押的目標。

---

## 🎯 輪帶內容（iter7：L=125 / 144 / 169，3.04M 組合）

**設計主軸**（iter7 上線版）：
- 每輪前 **33 slot** = 10 個 reg cluster + Wild cluster：`[S0×3, S1×3, ..., S9×3, WILD×3]`
  → 11 種圖案（10 reg + Wild）的 27 線 jackpot 都是**目押可達的 outcome**
- 剩餘 tail（92/111/136 slot）shuffle：extra wild、FS、額外 reg
- Wild max cluster 限制 **已撤**（iter5 曾禁 3 連 wild）→ Wild 27 線可觸發（機率 3.29e-7）
- 三輪 L 為 coprime（5³, 2⁴×3², 13²）→ **LCM = 組合數 = 3,042,000**，破解樣本 ~M 級

### iter7 每輪符號 counts

```
reel 0 (L=125): WILD:12 FS1:11 FS2:6 FS3:3 S0:3 S1:3 S2:6 S3:3 S4:9  S5:11 S6:12 S7:14 S8:15 S9:17
reel 1 (L=144): WILD:12 FS1:12 FS2:7 FS3:4 S0:4 S1:3 S2:7 S3:4 S4:11 S5:12 S6:14 S7:16 S8:18 S9:20
reel 2 (L=169): WILD:10 FS1:15 FS2:8 FS3:4 S0:4 S1:5 S2:8 S3:6 S4:12 S5:14 S6:16 S7:19 S8:21 S9:27
```

**Wild cluster 驗證**：每輪 `strip[30:33] = 🃏🃏🃏` ✅ → 三輪同停 offset=30 觸發 Wild 27 線大獎

**10 個 reg cluster 驗證**：每輪 prefix[0:30] = `[S0×3, S1×3, S2×3, S3×3, S4×3, S5×3, S6×3, S7×3, S8×3, S9×3]` ✅

**FS spread 驗證**（每輪每種 FS 環狀最小 gap ≥ 3）：iter7 make_strip_v5 保留此 constraint，analytic $P_{\text{reel}} = 3c/L$ 精確成立。

### 完整 3 輪內容（帶 slot 索引，寫死於 [`pachislot_mali.html`](pachislot_mali.html) `REEL_STRIPS`）

#### Reel 0 (L=125)

```
[000]🎰 [001]🎰 [002]🎰 [003]👑 [004]👑 [005]👑 [006]💎 [007]💎 [008]💎 [009]🔔
[010]🔔 [011]🔔 [012]🍉 [013]🍉 [014]🍉 [015]🍇 [016]🍇 [017]🍇 [018]🍊 [019]🍊
[020]🍊 [021]🍋 [022]🍋 [023]🍋 [024]🍒 [025]🍒 [026]🍒 [027]🍀 [028]🍀 [029]🍀
[030]🃏 [031]🃏 [032]🃏 [033]🍇 [034]🃏 [035]🍀 [036]🍋 [037]🍀 [038]🍋 [039]🍒
[040]🔴 [041]🍒 [042]🍀 [043]🍀 [044]🍒 [045]🔴 [046]🍉 [047]🟡 [048]🍒 [049]🍀
[050]💎 [051]🔴 [052]🍀 [053]🍋 [054]🔴 [055]🍀 [056]🍒 [057]🍇 [058]🍊 [059]🍊
[060]🔵 [061]🍊 [062]🍒 [063]🍋 [064]🍉 [065]🍋 [066]🔴 [067]🍇 [068]🃏 [069]🍒
[070]🔴 [071]🃏 [072]🍉 [073]🍊 [074]🔵 [075]🍇 [076]🍀 [077]🍇 [078]🍋 [079]🃏
[080]🃏 [081]🔴 [082]🍀 [083]🍇 [084]🍊 [085]🍇 [086]🍉 [087]🔴 [088]🔵 [089]💎
[090]🔴 [091]🍋 [092]🍊 [093]🍉 [094]🍊 [095]🍋 [096]🍒 [097]🍀 [098]🟡 [099]🍊
[100]🍋 [101]🍋 [102]🍀 [103]🍋 [104]🍉 [105]🍀 [106]🃏 [107]🔵 [108]🍊 [109]🍒
[110]💎 [111]🍒 [112]🟡 [113]🍀 [114]🍇 [115]🔴 [116]🔵 [117]🃏 [118]🍀 [119]🍒
[120]🔵 [121]🍒 [122]🃏 [123]🃏 [124]🔴
```

#### Reel 1 (L=144)

```
[000]🎰 [001]🎰 [002]🎰 [003]👑 [004]👑 [005]👑 [006]💎 [007]💎 [008]💎 [009]🔔
[010]🔔 [011]🔔 [012]🍉 [013]🍉 [014]🍉 [015]🍇 [016]🍇 [017]🍇 [018]🍊 [019]🍊
[020]🍊 [021]🍋 [022]🍋 [023]🍋 [024]🍒 [025]🍒 [026]🍒 [027]🍀 [028]🍀 [029]🍀
[030]🃏 [031]🃏 [032]🃏 [033]🍀 [034]🍋 [035]🃏 [036]🍉 [037]🟡 [038]🍋 [039]🍉
[040]🔵 [041]🍉 [042]🍇 [043]🔴 [044]🍀 [045]🍒 [046]🍒 [047]🍊 [048]🍇 [049]🍇
[050]🃏 [051]🍋 [052]🍋 [053]💎 [054]🍀 [055]🔔 [056]🟡 [057]🍋 [058]💎 [059]🍀
[060]🃏 [061]🃏 [062]🍀 [063]🍒 [064]🔵 [065]🍒 [066]🍊 [067]🍊 [068]🔵 [069]🔴
[070]🍋 [071]🍒 [072]🍉 [073]🍒 [074]🍊 [075]🃏 [076]🔴 [077]🍀 [078]🍒 [079]🍇
[080]🍒 [081]🔴 [082]🍊 [083]🍒 [084]🔴 [085]🎰 [086]🔵 [087]🃏 [088]🍊 [089]🔴
[090]🔵 [091]🍒 [092]🍊 [093]🍀 [094]🔴 [095]🍀 [096]🍋 [097]🍀 [098]🍇 [099]🍊
[100]🍒 [101]🃏 [102]🍇 [103]🔴 [104]🍋 [105]🍊 [106]🔵 [107]🍇 [108]🍀 [109]🍋
[110]🍉 [111]🔴 [112]🍋 [113]🍊 [114]🔴 [115]🃏 [116]🍋 [117]🍀 [118]🍉 [119]🍀
[120]🍒 [121]🍋 [122]🍀 [123]💎 [124]🍉 [125]🍀 [126]🍊 [127]🟡 [128]🔴 [129]🍀
[130]🍀 [131]🍀 [132]🍇 [133]🍒 [134]🍒 [135]🍇 [136]🍋 [137]🃏 [138]💎 [139]🟡
[140]🍉 [141]🍒 [142]🔵 [143]🔴
```

#### Reel 2 (L=169)

```
[000]🎰 [001]🎰 [002]🎰 [003]👑 [004]👑 [005]👑 [006]💎 [007]💎 [008]💎 [009]🔔
[010]🔔 [011]🔔 [012]🍉 [013]🍉 [014]🍉 [015]🍇 [016]🍇 [017]🍇 [018]🍊 [019]🍊
[020]🍊 [021]🍋 [022]🍋 [023]🍋 [024]🍒 [025]🍒 [026]🍒 [027]🍀 [028]🍀 [029]🍀
[030]🃏 [031]🃏 [032]🃏 [033]💎 [034]🍋 [035]🍒 [036]🍋 [037]🍇 [038]🍋 [039]🍀
[040]🍇 [041]🔵 [042]🔴 [043]🍒 [044]🃏 [045]🍋 [046]🍋 [047]🍒 [048]🍋 [049]🍋
[050]🃏 [051]🍒 [052]🍇 [053]🍀 [054]🍀 [055]💎 [056]🔴 [057]🔵 [058]🍋 [059]🃏
[060]🍊 [061]🃏 [062]🍀 [063]🔵 [064]🔔 [065]💎 [066]🍇 [067]🍀 [068]🍇 [069]🍊
[070]🔴 [071]🟡 [072]🍇 [073]🍀 [074]🍒 [075]🔴 [076]🍊 [077]🍉 [078]🟡 [079]🍊
[080]🍀 [081]🔴 [082]🍊 [083]💎 [084]🔴 [085]👑 [086]🍇 [087]🍒 [088]🔵 [089]🍇
[090]🔴 [091]🍉 [092]🍀 [093]🍀 [094]🍒 [095]🍋 [096]🔵 [097]🍒 [098]🍀 [099]🍋
[100]🟡 [101]🍉 [102]🔴 [103]🍉 [104]🟡 [105]🔴 [106]🍀 [107]🔔 [108]🍊 [109]🍒
[110]🔴 [111]🍒 [112]🍀 [113]🍊 [114]🍉 [115]🍒 [116]🔵 [117]🍀 [118]🍊 [119]👑
[120]🍀 [121]🍉 [122]🍊 [123]🍒 [124]🍒 [125]🍇 [126]🍊 [127]💎 [128]🍋 [129]🍒
[130]🍋 [131]🍊 [132]🍉 [133]🍀 [134]🍀 [135]🃏 [136]🍀 [137]🍀 [138]🔔 [139]🃏
[140]🔵 [141]🍋 [142]🍀 [143]🔵 [144]🔴 [145]🍀 [146]🍇 [147]🍀 [148]🍀 [149]🃏
[150]🍊 [151]🔴 [152]🍊 [153]🍒 [154]🍒 [155]🔴 [156]🍋 [157]🍋 [158]🔴 [159]🎰
[160]🍀 [161]🍉 [162]🍋 [163]🍒 [164]🍉 [165]🍒 [166]🔴 [167]🍀 [168]🍇
```

> 遊戲右側 strip preview panel（`max-height: 40vh` 可捲）動態渲染這 3 條輪帶內容，但**不 highlight 當前 offset**——目押要自己盯中央 reel 眼力抓。

### 11 種 27 線 cluster 位置（iter7 固定 prefix，3 輪一致）

| Offset 範圍 | 符號 | jackpot @ bet 100 |
|:---:|:---:|:---:|
| 00–02 | 🎰 BAR | 4,860 |
| 03–05 | 👑 Crown | 3,510 |
| 06–08 | 💎 Diamond | 2,970 |
| 09–11 | 🔔 Bell | 2,160 |
| 12–14 | 🍉 Watermelon | 1,890 |
| 15–17 | 🍇 Grape | 1,620 |
| 18–20 | 🍊 Orange | 1,350 |
| 21–23 | 🍋 Lemon | 1,215 |
| 24–26 | 🍒 Cherry | 1,080 |
| 27–29 | 🍀 Clover | 945 |
| **30–32** | **🃏 Wild** | **27,540** ⭐ (5,940 Wild 自賠 + 21,600 reg 通配累加) |

**3 輪同停在同一段 offset 即打出該符號的 27 線 jackpot**（三輪 prefix 排列完全一致）。**Wild @ offset 30 是全機頂獎 27,540（275× bet）**，因為 Wild 通配替代所有 10 個 reg 都會同時觸發它們各自的 27 線 payout（累加式）——iter7 加入 Wild cluster 讓這個超級大獎第一次成為可能。BAR 需 3 輪都停 offset=0，難度同 Wild jackpot（都是 1/(L₁·L₂·L₃) = 3.29e-7 每 300 萬次一次）。

### FS 目押位置速查（cheat sheet，iter7 shuffled tail，同種 FS 環狀 gap ≥ 3）

| 符號 | Reel 0 | Reel 1 | Reel 2 |
|------|--------|--------|--------|
| 🔴 Red 7 (FS×2) | 40, 45, 51, 54, 66, 70, 81, 87, 90, 115, 124 | 43, 69, 76, 81, 84, 89, 94, 103, 111, 114, 128, 143 | 42, 56, 70, 75, 81, 84, 90, 102, 105, 110, 144, 151, 155, 158, 166 |
| 🔵 Blue 7 (FS×3) | 60, 74, 88, 107, 116, 120 | 40, 64, 68, 86, 90, 106, 142 | 41, 57, 63, 88, 96, 116, 140, 143 |
| 🟡 Gold 7 (FS×5) | 47, 98, 112 | 37, 56, 127, 139 | 71, 78, 100, 104 |
| 🃏 Wild | **30, 31, 32** (cluster), 34, 68, 71, 79, 80, 106, 117, 122, 123 | **30, 31, 32** (cluster), 35, 50, 60, 61, 75, 87, 101, 115, 137 | **30, 31, 32** (cluster), 44, 50, 59, 61, 135, 139, 149 |

---

## 🎮 目押機制（Eye-Play）

`SPIN_SPEED_MS = 100`（可調）→ 每 slot 100ms、10 slot/秒。

- `startReelAnimation` 每 tick 前進 `reel.currentOffset` 並顯示**真符號不模糊**
- `stopReel` 讀當下 `currentOffset` → 按下瞬間就是結果（不重新亂數）
- 起始 offset 隨機（防玩家記住起始位置直接算停格）

**難度調整**：
- 加難：`SPIN_SPEED_MS = 50`（20 slot/秒）
- 加易：`SPIN_SPEED_MS = 200`（5 slot/秒）
- 加真實パチスロ手感：可加 0–4 frame slippage（本專案未實作）

---

## 🎰 玩家可玩 spin 數估算（iter7）

給定起始資金、下注額、目標 RTP，估算玩家平均能玩多少 spin。

**純理論公式（無 variance）**：

$$\text{spins}_{\text{theory}} = \frac{\text{initial}}{\text{bet} \times (1 - \text{RTP})}$$

以 iter7 RTP=93.44% 為例，10,000 起始 / 100 下注：

$$\text{spins}_{\text{theory}} = \frac{10{,}000}{100 \times 0.0656} \approx 1{,}524 \text{ spin}$$

**實測（100K 玩家模擬）**：

| 分位 | iter7 spin 數 | iter6 spin 數 |
|-----|:---:|:---:|
| **平均** | **1,067** | 1,093 |
| median | 752 | 829 |
| q10（最快破產） | 322 | 367 |
| q25 | 463 | 525 |
| q75 | 1,299 | 1,358 |
| q90（撐最久） | 2,170 | 2,138 |

**實測平均 1,067 比理論 1,524 短 30%**——這是 volatility 的懲罰：

- **負向漂移**：每 spin 期望輸 6.56 元，長期必然歸零
- **高 σ**：payoff 分佈波動大，玩家 balance 隨機遊走，即使幾次幸運大爆發也很快就在後續連空回吐
- **對數縮短**：$\mathbb{E}[\text{ruin time}] < \frac{\text{initial}}{\text{drift}}$ 是 gambler's ruin 的一個常見結果（Chung 1974）

**不同起始資金對照**（iter7 RTP + σ）：

| 起始資金 | 理論 spins | 預估實測平均 | 中位數 |
|---------|:---:|:---:|:---:|
| 5,000 | 762 | ~534 | ~376 |
| **10,000** | **1,524** | **1,067** | **752** |
| 20,000 | 3,049 | ~2,134 | ~1,504 |
| 50,000 | 7,622 | ~5,335 | ~3,760 |

（比例縮放；實測略有 non-linear 效應，需另跑 sim）

**不同下注額對照**（10K 起始）：

| 下注額 | 理論 spins | 期望遊玩時間（100ms/spin）|
|--------|:---:|:---:|
| 100 | 1,524 | ~2.5 分鐘 純轉動 |
| 200 | 762 | ~1.3 分鐘 |
| 500 | 305 | ~30 秒 |
| 1000 | 152 | ~15 秒 |
| 1500 | 102 | ~10 秒 |

（純理論、不含 bonus 動畫時間；玩家實際會慢慢按 STOP 目押，一 spin 3-5 秒是常態）

---

## 🔬 自行重跑校準

### iter5 HL 校準（rtp_sim.py，96% RTP）

```bash
cd pachislot_mali
PYTHONUTF8=1 python rtp_sim.py --target 0.96 --tol 0.005 --mc 200000 --players 100000
```

參數：
- `--target 0.96` — 目標 RTP
- `--tol 0.005` — 收斂容忍（±0.5pp）
- `--mc 200000` — Monte Carlo 驗證 spin 數
- `--players 100000` — 玩家模擬台數
- `--seed 20260720` — random seed（reproducible）

輸出 `tuned_strips.json`。

### iter6 實驗（撤 Wild 限制 + Wild payout=200，93.5% RTP）

```bash
PYTHONUTF8=1 python iter6_wild_open.py
```

（無 CLI 參數；設計改動寫死在檔頭。輸出 `tuned_strips_iter6.json`）

### iter7 上線版（加 Wild cluster + Wild payout=220，93.5% RTP）

```bash
PYTHONUTF8=1 python iter7_wild_cluster.py
```

輸出 `tuned_strips_iter7.json`。跑完後可用內建 build 腳本同步 REEL_STRIPS 到 HTML（見 wiki [[concept_slot_rtp_calibration_hl]]）。

### exact_moments 精確枚舉

```bash
# 對現行 HTML 跑
PYTHONUTF8=1 python exact_moments.py --source html --focus S9

# 對特定 iter 的 json 跑
PYTHONUTF8=1 python exact_moments.py --source json --focus WILD

# 換 focus 符號看 per-line-count 分佈
PYTHONUTF8=1 python exact_moments.py --focus S0    # BAR (最高 payout)
PYTHONUTF8=1 python exact_moments.py --focus FS1   # Red 7
```

參數：
- `--source html|json` — 從 pachislot_mali.html REEL_STRIPS 或 tuned_strips.json 讀取
- `--bonus-mc 500000` — Mali session MC 樣本數（估 bonus mean/var）
- `--focus S9` — per-line-count 詳表要看哪個符號

---

## 📜 免責聲明

本專案為個人學習與娛樂用途開發，**不涉及任何真實賭博或金錢交易**。  
所有信用點數均為虛擬，不具任何實際價值。請理性娛樂。
