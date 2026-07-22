# Pachislot Little Mary — RTP 校準 VERSION LOG

> HL Loop 校準日誌，依 [[concept_heuristic_learning]] 架構管理。
> Pattern 同 [[project_darkchess_npc]]：sim 為 truth source → HL 校準 → 寫回 HTML → 記錄。

---

## [2026-07-20] iter0 → baseline 建立 + HL 校準 v1

### 起點：HTML 原始 weights 縮放到 30-slot 物理輪帶

原始 SYMBOLS weight（`pachislot_mali.html:683-697`）總和 82，按比例縮放並 round 到 30-slot：

```
{WILD:1, FS1:3, FS2:1, FS3:1,
 S0:1, S1:1, S2:1, S3:2, S4:2,
 S5:3, S6:3, S7:3, S8:4, S9:4}      sum = 30 ✓
```

三輪相同，seed 20260720/…21/…22 分別 shuffle。

### Baseline RTP

| 項目 | RTP |
|------|-----|
| Base（27-line 常規中獎） | **26.71%** |
| Bonus（小瑪莉觸發 × 期望值）| **24.25%** |
| **TOTAL** | **50.96%** |

低於北美賭場水位（92–98%）與日式パチスロ規制（55–97.5%）下限，屬「陪玩級」設定。

Base 各符號貢獻（前三大）：
- 🍒 Cherry: 5.00%
- 🍀 Clover: 4.38%
- 🍇 Grape: 3.84%

FS 觸發率：Red 7 1.99% / Blue 7 0.089% / Gold 7 0.089% —— 三者的期望觸發回饋 10.34x / 15.52x / 25.86x bet。

### HL Loop（target 96%, tol ±0.5pp）

HS 架構對映：
- **state**：`counts_per_reel: List[Dict[str, int]]`
- **policy**：`hl_single_swap_search` —— 枚舉 (reel, from_sym, to_sym) 單交換，選最能收斂 `|target - RTP|` 的一步（≈ greedy gradient descent）
- **feedback**：`analytic_rtp_from_counts` 回傳 base/bonus/per_symbol 分解
- **regression**：seed-locked 解析式 RTP 落在 `[target±tol]`

收斂軌跡：

| iter | swap | RTP | gap |
|------|------|-----|-----|
| 0 | reel0: −S2 (Diamond) +Wild | 50.96% → 57.90% | +45.04pp |
| 1 | reel1: −S2 +Wild | 57.90% → 66.91% | +38.10pp |
| 2 | reel2: −S2 +Wild | 66.91% → 78.68% | +29.09pp |
| 3 | reel0: −S4 (Watermelon) +Wild | 78.68% → 89.76% | +17.32pp |
| 4 | reel0: −FS1 (Red 7) +Wild | 89.76% → 95.61% | +6.24pp |
| 5 | — | 95.61% | +0.39pp ✓ 收斂 |

**5 iter 收斂**。策略讀來完全人類可讀：三輪各加 1 個 Wild → 再對 reel 0 追加 2 個 Wild（其中 1 個以 FS1 換出降 bonus 佔比）。

### Tuned Strips

```
reel 0: WILD:4 FS1:2 FS2:1 FS3:1 S0:1 S1:1 S3:2 S4:1 S5:3 S6:3 S7:3 S8:4 S9:4
reel 1: WILD:2 FS1:3 FS2:1 FS3:1 S0:1 S1:1 S3:2 S4:2 S5:3 S6:3 S7:3 S8:4 S9:4
reel 2: WILD:2 FS1:3 FS2:1 FS3:1 S0:1 S1:1 S3:2 S4:2 S5:3 S6:3 S7:3 S8:4 S9:4
```

Wild 總數 3 → 8（reel 0 集中放 4 個），S2 Diamond 完全清零。

### RTP 驗證

| 度量 | Analytic | MC (200k spins) |
|------|----------|-----------------|
| Base RTP | 77.72% | 78.19% |
| Bonus RTP | 17.89% | 18.79% |
| **Total RTP** | **95.61%** | **96.98%** |

- **Analytic** 假設 3 row 為獨立抽樣，對應 HTML 現行 `getRandomSymbol()` 語意；差 target 0.39pp
- **MC** 用物理輪帶（consecutive 3-position window）；差 target 0.98pp，仍在容忍內。**MC > Analytic 1.4pp** 反映 shuffled strip 上 Wild 有時 3 連（同視窗），造成一輪 3 個 match 的機率高於獨立假設，觸發 3×3×3=27 條線的超大 payout。

兩個數字都落在合理區間，取哪個當「真值」看 HTML 之後採哪套 RNG：
- 若 **保留 HTML 原本的 independent weighted RNG** → 用 analytic 95.61%
- 若 **改成物理輪帶（stopReel 讀 REEL_STRIPS[off,off+1,off+2]）** → 用 MC 96.98%

### 已知限制與未來 iter 待辦

1. **三輪非對稱**：reel 0 有 4 Wild、reel 1/2 只有 2 個。若未來想要玩家視覺一致的對稱輪帶，可加 constraint 重跑 HL（trade-off：可達 RTP 曲面較窄，可能需微調 payout）
2. **Bonus RTP 佔比降至 18.7%（原 47.6%）**：base 拉到 78% 後 bonus 相對變小；日式パチスロ習慣是 bonus 佔比高（>50%），下 iter 可換成「保留低 base + 提高 FS spins 或 mult」的策略
3. **Mystery 格永不「消失」**：JS 邏輯下 mystery 命中後 layout 保留，可能同 session 重複命中同格；若要改成「命中後 mystery 換成一般格」，Mali round 期望值需重算
4. **HL policy 是 greedy single-swap**：找不到全局最優。可延伸：simulated annealing 或 pair-swap（保 total count）避免卡 local minima

---

## [2026-07-20] iter1 → 修 27 線騙人 bug + 真目押機制

### 問題

Roy 指出 iter0 tuned strips **號稱 27 線但實際不可達**：每輪窗口最多 1 張 Wild、且 reg 符號很少 3 連續，計算後每個 reg 符號的 max lines = 1×1×1 到 2×2×3 = 最多 12 線（Clover），BAR/Diamond/Grape 甚至只有 1 線。加上 iter0 動畫用 blur + `getRandomSymbol()`，玩家「按停止時機」跟結果完全無關 → 目押（eye-play）被繞過。

### 修正

**兩個 constraint 加進 HL：**
- `min_wild_per_reel = 3` → 每輪 Wild ≥ 3，用 `make_strip_with_wild_cluster()` 把前 3 slot 固定成 Wild 群
- `min_fs_per_reel = 1` → 每輪每種 FS（Red/Blue/Gold 7）至少 1 張，避免 HL 為省 RTP 把 FS1/FS3 從某輪清零（iter1 曾出現過此 bug，被抓修）

**HTML 三處改動：**
- 加 `SPIN_SPEED_MS = 100`（10 slot/秒，人類反應 200ms 可鎖 2 slot 內）
- `startReelAnimation`：由「50ms/tick 顯示 blur 隨機符號」改為「SPIN_SPEED_MS/tick 前進 `reel.currentOffset` +1、顯示真實 strip 窗口不模糊」
- `stopReel`：由 `spinFromStrip()` 重新亂數改為讀 `windowAtOffset(index, reel.currentOffset)` → **按下當下的 offset 就是結果**

### HL Loop（constraints 版）

Baseline 加 Wild 補到每輪 ≥ 3 → RTP 從 50.96% 直接跳到 **120.37%**（3 wild 拉爆 base），HL 需要**扣**回來：

| iter | swap | RTP |
|------|------|-----|
| 0-2 | reel0: −3 FS1 +3 S8（Cherry）| 120.37 → 109.17 |
| 3-5 | reel0: −3 S5（Grape） +3 S8 | 109.17 → 103.81 |
| 6-7 | reel1: −2 FS1 +2 S5 | 103.81 → 101.27 |
| 8-10 | reel2: −2 S8 −1 S0 +3 FS1 | 101.27 → 96.80 |
| 11 | reel0: −1 S1 +1 FS2 | 96.80 → 96.02 ✓ |

**12 iter 收斂**。有 2 種 constraint 後策略變複雜，HL 學會「加 Wild 靠 base 拿 RTP → 拿掉部分 FS 降 bonus 收斂」。

### Tuned Strips（iter1）

```
reel 0: WILD:3 FS1:1 FS2:2 FS3:1 S2:1 S3:2 S4:2 S6:3 S7:3 S8:8 S9:4
reel 1: WILD:3 FS1:1 FS2:1 FS3:1 S0:1 S1:1 S2:1 S3:2 S4:2 S5:5 S6:3 S7:3 S8:2 S9:4
reel 2: WILD:3 FS1:6 FS2:1 FS3:1 S1:1 S2:1 S3:2 S4:2 S5:3 S6:3 S7:3 S9:4
```

（reel 0 S8:8 = Cherry cluster；reel 2 FS1:6 = Red 7 集中）

### 驗證

| 度量 | Analytic | Python MC (200k) | Browser JS MC (100k) |
|------|----------|-------------------|----------------------|
| Total RTP | 96.02% | 95.95% | 96.57% |
| Base | 86.28% | 85.14% | 85.81% |
| Bonus | 9.74% | 10.81% | 10.76% |
| FS1 (Red 7) 觸發率 | 0.456% | 0.529% | 0.503% |
| FS2 (Blue 7) | 0.174% | 0.181% | 0.217% |
| FS3 (Gold 7) | 0.090% | 0.095% | 0.086% |
| 全 Wild 27 線 jackpot | 0.0037% | — | 0.0060% (6/100k) |

**27 線可達性**：10 個 reg 符號在 3 輪都 max=3（全靠 Wild 群覆蓋）✅

**目押實測 jackpot**：手動把 3 輪都停在 offset=0 → 顯示 3×3 全 Wild → win 21,600 = 27 × (180+130+110+80+70+60+50+45+40+35) = 27 × 800 ✅

### 目押難度分析（SPIN_SPEED_MS = 100，iter1）

- 10 slot/秒 → 每 slot 100ms
- 人類反應時間 ~200ms → 「瞄準 A 按停」實際落在 A+2 slot 附近
- 窗口 3 slot → 偏差 ≤ 2 slot 都能把 A 卡進窗口
- **理論上 100% 命中每次目押**——但要瞄準 3 輪 × 目標符號的連續呼吸，人類實際錯過率不低
- 想加難度：`SPIN_SPEED_MS = 50`（20 slot/秒）；想加輔助（真實パチスロ）：加 0-4 frame 的 slippage
- 純目押 optimal 玩法下 RTP 會 > 96%（玩家瞄準高 payout 或 FS 符號）；若要守 96% 對抗 optimal 玩家，需要加 slippage 或動態 RTP

---

## [2026-07-21] iter2 → 修 wild 滿盤無賠率 + 3 輪不等長

### 問題（Roy 指出）

1. **Wild 滿盤無對應賠率**：iter1 的 3-Wild jackpot（3 輪同時停 offset=0）雖然靠 wild 通配替代 10 個 reg 符號合計 21,600 賠付，但 WILD 本身 `payout: 0` → 賠率表 Wild 列顯示 `-`，玩家看不出「Wild × 3 連線」有專屬回饋。
2. **3 條輪帶等長（都 30 slot）**：所有輪帶節奏一樣、offset 循環對齊，記位型玩家可預判。

### 修正

**Wild 賠率**：
- `SYMBOLS.WILD.payout: 0 → 300`（成為賠率表最高，超過 BAR 180）
- `renderPaytable`：改成只把 FS 顯示 `-`，Wild 也顯示數字；備註欄改「WILD (可替代 & 3線自賠)」
- `check_wins` (Python sim)：加入 Wild 3-line 自賠計算，跟 wild 通配 reg 符號**不重複計數**（match 是 `sid == WILD_ID`）

**變長輪帶**：
- `REEL_LENGTHS = [28, 30, 32]`（module constant）
- `make_strip*` / `initial_counts_from_html_weights` / `analytic_rtp*` / `hl_*` 全部改吃 per-reel length
- HTML `REEL_STRIPS` 三條長度不同；`renderReelStatic` / `windowAtOffset` 原本就走 `strip.length`，不用改
- 加 `--lengths CLI` 參數方便未來調整

**額外 constraint**（校準時發現）：
- `max_reg_per_reel = 8`：避免 HL 為降 RTP 把單一 reg 符號塞爆一輪（第一次跑出 reel 2 S8:16 = 半條 Cherry，視覺失衡）
- 語意上蓋所有非-Wild 符號（含 FS，避免又躲進 FS1 塞爆），CLI: `--max-reg 8`（預設）

### HL Loop（iter2 constraints）

Baseline（HTML weights 縮放到 28/30/32、每輪 Wild 已補到 3）RTP 起點約 129%（3-Wild jackpot 加上 wild 通配貢獻很大），HL 需扣回：

- 收斂 iter 數：HL 走了一輪 single-swap search 就落到 target
- Total RTP：**95.99%** analytic ≈ target 96.00% ±0.5pp ✓

### Tuned Strips（iter2）

```
reel 0 (L=28): WILD:3 FS1:8 FS2:1 FS3:1 S1:1 S2:1 S3:2 S4:2 S5:3 S6:3 S7:3
reel 1 (L=30): WILD:3 FS1:1 FS2:1 FS3:1 S0:1 S2:1 S4:2 S5:6 S6:1 S7:3 S8:2 S9:8
reel 2 (L=32): WILD:3 FS1:1 FS2:1 FS3:1 S1:1 S2:1 S3:2 S4:2 S6:3 S7:3 S8:8 S9:6
```

reel 0 FS1:8 是 HL 為壓 RTP 用的手段（塞高計數 FS1 拉高 FS1 觸發率，但 FS1 單觸發 bonus 期望只有 10.34×bet 相對溫和，反而幫忙把 RTP 從 130% 降到 96%）。

### 驗證

| 度量 | Analytic | MC (200k spins) |
|------|----------|-----------------|
| Total RTP | **95.99%** | **97.21%** |
| Base | 86.63% | 86.67% |
| Bonus | 9.51% | 10.53% |
| FS1 (Red 7) 觸發率 | 0.558% | 0.621% |
| FS2 (Blue 7) | 0.090% | 0.090% |
| FS3 (Gold 7) | 0.090% | 0.104% |
| 3-Wild jackpot 期望回饋 | **8100 credits @ bet 100** | 實測 ✓ |
| 全 Wild 滿盤總賠付 @ bet 100 | 8100 (WILD 自賠) + 21600 (wild 通配) = **29700** | JS 手動觸發驗證 ✓ |

**27 線可達性**：10 個 reg 符號 + WILD 在 3 輪都 max=3 ✅

MC 高 analytic 1.2pp 的原因跟 iter1 同：物理輪帶 3 row 是連續三格、Wild cluster 造成 3 連 wild 概率高於獨立抽樣近似。

### 已知限制與未來 iter 待辦

1. **reel 0 FS1:8 佔比 28%**：Red 7 出現非常密，視覺上會看到很多紅七跑過。若要更均衡可加 `max_fs_per_reel` 上限（例如 4），trade-off 是 HL 得改用其他手段降 base RTP
2. **變長輪帶 → 3 輪 offset 週期不對齊**：LCM(28,30,32) = 3360，記位型玩家需要多 100× 樣本才能建 3 輪聯合分佈，反破解強度顯著提升
3. **paytable 顯示未含 Wild 27-line 上限**：目前 Wild 那格顯示 `300`（單線賠率），實際 3-Wild 滿盤 27 線 = 8100 + reg wild-sub。可加輔助說明或 "MAX WIN" 欄

---

## [2026-07-21] iter3 → 打散 wild + 拉長輪帶 + 保底 27 線 cluster + 玩家模擬

### 問題（Roy 追加）

1. **輪帶太短**：iter2 L=28/30/32 → 26,880 組合、LCM=3,360，記位型玩家 100 spin 就能建 baseline 分佈
2. **Wild 滿盤這個「無賠率鏡頭」不該存在**（iter2 是加賠率補救、方向錯了 → 回頭改成禁止該 outcome）
3. **但有賠率的圖案仍需要 27 線可達**：至少一個 reg 符號可以打出滿盤
4. **需要多台玩家模擬**：估算破產率、平均破產 spin 數、期末結餘分佈

### 修正

**輪帶拉長 × 打散 × 保底 cluster：**
- `REEL_LENGTHS = [80, 96, 108]`（829,440 組合、LCM=8,640 → 破解需要樣本 ~30×）
- 新 constant `WILD_MAX_CONSECUTIVE = 2`：strip 環狀掃描不能有任何 3 連續 Wild → **wild 滿盤（9 格全 Wild）數學上不可能發生**
- 新 constant `REG_CLUSTER_SYMBOL = 'S9'` + `REG_CLUSTER_SIZE = 3`：每輪前 3 slot 固定為 S9 群 → 3 輪同停 offset=0 時 S9 達 27 線（jackpot 落地為 27×35 = 945@bet100）
- `WILD.payout` 從 iter2 的 300 **revert 回 0**（Roy 明確否認要求）
- `WILD_MIN_PER_REEL = 3`（保通配基本量、不會空 wild）

**新 strip builder：`make_strip_v3()`**
- 前 3 slot 固定 S9-S9-S9
- 其餘 shuffle（含 Wild 散在中間）
- 拒絕採樣：若 shuffle 出來的環狀窗口違反 `WILD_MAX_CONSECUTIVE`，換 seed 重跑（上限 200 次）

**HL constraint 補：**
- 加 `min_cluster_sym_per_reel = REG_CLUSTER_SIZE`：不讓 HL 為降 RTP 把 S9 抽到 <3
- `max_reg_per_reel` 預設從 8 放寬到 20（長輪帶應允許更多同符號）

**初始 count 縮放修正：** `initial_counts_from_html_weights(length)` 改為按 HTML weights **比例**縮放到 length 而不是「基準 30 + 差額全丟一個符號」，避免長輪帶 baseline 把單一符號堆到 50+ 導致 HL 卡住

**多台玩家模擬新增 `simulate_players()`：**
- 每台玩家獨立 session，balance 從 initial 開始，固定 bet 每 spin，直到破產或觸 max_spins cap
- 為衝速度加了 `_build_base_win_tables()`：預先把每輪每個 offset 的 3-slot 窗口壓成 per-symbol count dict → 單 spin 從 O(reels × slots) 降到 3 dict 查詢 + 10 乘積 → **~10× 加速**（1000 玩家從 100s → 11s）
- 統計：破產率、spins-to-bust 分位數（q10/25/50/75/90 + mean）、期末結餘分位數、單擊最大 win、lifetime RTP（與 MC 對照）

### HL Loop（iter3 constraints）

Baseline 起點 47.5% → constraints seed 補 wild+S9 後 33.0% → **14 iter 收斂到 96.50% analytic**（詳細 swap 路徑省略，關鍵是 HL 一路 −reg +WILD 拉高 base 讓通配貢獻大於 wild 打散造成的損失）

### Tuned Strips（iter3）

```
reel 0 (L=80):  WILD:10 FS1:6 FS2:4 FS3:2 S2:4 S3:4 S4:6 S5:7 S6:8 S7:9 S8:10 S9:10
reel 1 (L=96):  WILD:8  FS1:8 FS2:5 FS3:1 S1:3 S2:5 S3:6 S4:7 S5:8 S6:9 S7:11 S8:12 S9:13
reel 2 (L=108): WILD:7  FS1:9 FS2:5 FS3:2 S0:1 S1:4 S2:5 S3:7 S4:8 S5:9 S6:11 S7:12 S8:13 S9:15
```

前 3 slot 都是 `S9-S9-S9`；Wild 散開驗證 3 輪都 ✅ `≤ 2 連續`。

### RTP 驗證

| 度量 | Analytic | MC (200k spins) |
|------|----------|-----------------|
| Total RTP | **96.50%** | **96.01%** |
| Base | 80.50% | 80.14% |
| Bonus | 16.00% | 15.87% |
| FS1 (Red 7) 觸發率 | 1.101% | 1.065% |
| FS2 (Blue 7) | 0.277% | 0.296% |
| FS3 (Gold 7) | 0.012% | 0.012% |

MC 與 analytic 差距從 iter1/iter2 的 +1~1.4pp 縮小到 **-0.5pp**——因為 Wild 打散後獨立假設更接近真實物理輪帶行為（沒有 wild cluster 造成的相關性偏差）。**這是 iter3 一個非直覺的副作用**：策略決策時 analytic 值更可信、HL 更易收斂。

### 27 線可達性驗證

| 符號 | reel1 max | reel2 max | reel3 max | 最大線數 |
|------|-----------|-----------|-----------|---------|
| 🎰 BAR | 2 | 2 | 1 | 4 |
| 👑 Crown | 2 | 2 | 2 | 8 |
| 💎 Diamond | 2 | 2 | 1 | 4 |
| 🔔 Bell | 3 | 2 | 2 | 12 |
| 🍉 Watermelon | 3 | 2 | 2 | 12 |
| 🍇 Grape | 3 | 2 | 2 | 12 |
| 🍊 Orange | 2 | 2 | 2 | 8 |
| 🍋 Lemon | 2 | 2 | 2 | 8 |
| 🍒 Cherry | 2 | 3 | 2 | 12 |
| 🍀 **Clover** | **3** | **3** | **3** | **27 ✅** |

**Roy spec「有賠率的圖案 需要有滿盤的機會」達成：S9 Clover 是保底 27 線路徑**（設計出來的），其他 reg 符號機率性中 4–12 線。iter1/iter2 每個 reg 都能 27 線是靠 wild cluster 覆蓋——iter3 打散 wild 之後就不能再有這種便宜行事了，這是 trade-off 的直接後果。

### 玩家模擬（100,000 台 × 起始 10,000 × bet 100 × cap 10,000 spin）

| 指標 | 數值 |
|------|------|
| 破產玩家數 | **94,804 / 100,000** (94.80%) |
| 觸 cap 未破產 | 5,196 (5.20%) |
| lifetime RTP | 96.71% |

**破產玩家的 spin-to-bust 分佈：**

| 分位數 | spins |
|-------|-------|
| q10 | 529 |
| q25 | 838 |
| median | **1,558** |
| q75 | 3,080 |
| q90 | 5,375 |
| mean | 2,311 |

**期末結餘分佈（含破產者，全 100k 玩家）：**

| 分位數 | balance |
|-------|---------|
| q10 | 10 |
| median | 60 |
| q90 | 95 |
| top-1% | 30,190 |
| mean | 1,084 |

**單擊最大 win：6,550 credits @ bet=100**（一次 FS session 走運疊 Mali+Mystery）

### 解讀（大賺大賠 vs 平穩）

- **中位數玩家玩 1,558 spin 就燒完 10K 籌碼**（平均 6.4 credits/spin 損失、RTP 96% 對應期望 4/spin，差距是有 spin 打了小 win 拉回來又損掉）
- **90% 玩家在 5,375 spin 內破產**——玩家想「玩久」機率很低
- **top-1% 玩家帶著 30k+ 離場**（3× 起始金）——長尾靠 FS session 疊 mystery/gold 7 觸發
- **94.8% 玩家最終破產**——RTP 96% 但沒有停損機制，長線 100% 破產（僅視乎 cap 何時到）
- 業界類比：日式パチスロ 5-6 號機（低變動）median 通常 3000–5000 spin，此機為 1,558 spin → **偏「高頻小獎 + 稀有大獎」的高變動設計**（吃 Cherry/Clover 通配、Red 7 觸發率 1%但賠率低）

### 已知限制與未來 iter 待辦

1. **Cap 10,000 spin 是人為終止**：5.2% 未破產玩家如果繼續玩 → 幾乎全部會破產（RTP<100%）。要模擬「玩家帶錢離場」行為需加 stopping policy（達 X 倍即撤、連輸 Y spin 停等）
2. **spins-to-bust 分佈的 q90/q10 比 = 10.2×** → 高變動，玩家體驗跨度大。若要壓變動可提高低賠率符號 count（S8/S9 已在 10-15 區間，接近 max_reg 20 上限）
3. **右側 strip preview panel 已加 `max-height:40vh + overflow-y:auto`**：長輪帶不會擠掉 game log；但 108 slot 看起來仍冗長，可考慮改「摺疊/展開」按鈕
4. **FS3 Gold 7 觸發率 0.012% ≈ 每 8,333 spin 一次**：中位數玩家（1,558 spin）看不到；只有 top-tail 玩家會遇到 → 可能需要另一個 marketing 敘事讓玩家知道「有」而不是覺得騙人
5. **_build_base_win_tables 記憶體 O(sum(L)) = ~280 dict × ~13 entries** → 玩家模擬瓶頸不在此，若要跑百萬台可 numpy 化再加 20-50×

---

## [2026-07-21] iter4 → 每個 reg 圖案都可 27 線 + 輪帶再拉長

### 問題（Roy 追加）

iter3 只有 S9 Clover 能達 27 線滿盤——**其他 reg 圖案有賠率但打不到滿盤**，與「所有圖案都要有 27 線機會」的設計理念相違。同時 iter3 輪帶（80/96/108 = 829K 組合）仍嫌短。

### 修正

**每個 reg 都 cluster + 輪帶再拉長：**
- `REEL_LENGTHS = [125, 144, 169]`（三個 coprime：5³, 2⁴×3², 13² → **LCM = 組合數 = 3,042,000**，最大化 anti-cheat 週期）
- 新 `REG_CLUSTER_SIZE = 3` 對**所有** reg 生效：每輪前 30 slot 固定為 `[S0×3, S1×3, ..., S9×3]`
  → 3 輪同停對應 offset（0/3/6/9/12/15/18/21/24/27）時，任一 reg 都可達 27 線
- Wild 仍打散（`WILD_MAX_CONSECUTIVE=2`）→ wild 滿盤仍不可能
- HL constraint `min_all_reg_per_reel=REG_CLUSTER_SIZE`：每個 reg 都必須 ≥ 3（保 cluster 建構原料）
- `max_reg_per_reel` 從 iter3 的 20 放寬到 40（長輪帶允許更多同符號）

**新 builder `make_strip_v4()`**：
- prefix = 10 個 reg × 3 slot = 30 slot 固定
- 剩餘 95/114/139 slot 為 shuffled tail（wild + FS + 額外 reg）
- 拒絕採樣確認 tail wild ≤ 2 連續

**HL target 調整**：iter4 有嚴格的 30-slot cluster prefix → HL 反而收斂困難，且 analytic-MC gap 從 iter3 的 −0.5pp 擴到 −3pp（見下文）。將 `--target` 拉到 **0.99**（analytic），MC 才落在 Roy 指定的 95-97% 內。

### HL Loop（iter4，target 0.99）

22 iter 收斂：baseline 47.06% → 一路 −reg +WILD 拉高 base RTP → 收斂到 analytic **99.11%**（gap +0.06pp）。

### Tuned Strips（iter4，前 30 slot 為固定 cluster prefix）

```
reel 0 (L=125): WILD:14 FS1:12 FS2:6 FS3:3 S0:3 S1:3 S2:6 S3:3 S4:9  S5:11 S6:9  S7:14 S8:15 S9:17
reel 1 (L=144): WILD:13 FS1:12 FS2:7 FS3:4 S0:4 S1:3 S2:7 S3:3 S4:11 S5:12 S6:14 S7:16 S8:18 S9:20
reel 2 (L=169): WILD:11 FS1:14 FS2:8 FS3:4 S0:4 S1:6 S2:8 S3:5 S4:12 S5:14 S6:16 S7:19 S8:21 S9:27
```

前 3 slot: `S0 S0 S0`；[03-05]: `S1 S1 S1`；...；[27-29]: `S9 S9 S9` ✅ 三輪都一致，tail shuffle 各自不同。

### RTP 驗證

| 度量 | Analytic (target 0.99) | MC 200K spins | Player sim ~230M spins |
|------|------------------------|---------------|-----------------------|
| Total RTP | **99.11%** | **96.49%** | **95.99%** |
| Base | ~82% | 82.65% | — |
| Bonus | ~17% | 13.84% | — |
| FS1 觸發率 | ~1.20% | 0.912% | — |
| FS2 | ~0.27% | 0.213% | — |
| FS3 | ~0.06% | 0.045% | — |

**analytic vs MC 差 −2.62pp**（iter3 只差 −0.48pp）——這是 iter4 的一個非預期副作用：

> **原因**：30-slot cluster prefix 讓 wild + FS 都擠到 95/114/139 slot 的 tail 內，shuffle 後某些 FS 會在近距離（≤2 slot）內成對出現，共享 3-slot 窗口 → 有效觸發覆蓋率 < 3 × count（獨立假設）。實測 reel 0 FS1 的 empirical/analytic = 0.83（17% 缺角）。
> 
> **應對**：直接拉 HL target 到 0.99，讓 MC 落到 96.49% 對齊 Roy spec。徹底修法是在 `make_strip_v4` 加「同種 FS 最小 gap ≥ 3」的 rejection 條件——iter5 待辦。

### 27 線可達性驗證 ✅

| 符號 | reel 0 | reel 1 | reel 2 | 最大線數 |
|------|:---:|:---:|:---:|:---:|
| 🎰 BAR | 3 | 3 | 3 | **27 ✅** |
| 👑 Crown | 3 | 3 | 3 | **27 ✅** |
| 💎 Diamond | 3 | 3 | 3 | **27 ✅** |
| 🔔 Bell | 3 | 3 | 3 | **27 ✅** |
| 🍉 Watermelon | 3 | 3 | 3 | **27 ✅** |
| 🍇 Grape | 3 | 3 | 3 | **27 ✅** |
| 🍊 Orange | 3 | 3 | 3 | **27 ✅** |
| 🍋 Lemon | 3 | 3 | 3 | **27 ✅** |
| 🍒 Cherry | 3 | 3 | 3 | **27 ✅** |
| 🍀 Clover | 3 | 3 | 3 | **27 ✅** |

**Roy spec「所有圖案都要有機會可以 27 線」全數達成**。玩家目押只要 3 輪同停在對應 offset 就中對應 jackpot：

| 符號 | offset (每輪) | jackpot @ bet 100 |
|------|:---:|:---:|
| 🎰 BAR | 0 | **4,860** |
| 👑 Crown | 3 | 3,510 |
| 💎 Diamond | 6 | 2,970 |
| 🔔 Bell | 9 | 2,160 |
| 🍉 Watermelon | 12 | 1,890 |
| 🍇 Grape | 15 | 1,620 |
| 🍊 Orange | 18 | 1,350 |
| 🍋 Lemon | 21 | 1,215 |
| 🍒 Cherry | 24 | 1,080 |
| 🍀 Clover | 27 | 945 |

BAR 頂 jackpot 從 iter3 的 945（S9 only）拉到 **4,860（5.14×）**，玩家目押誘因大幅升級。

### 玩家模擬（100,000 台 × 起始 10,000 × bet 100 × cap 10,000 spin）

| 指標 | iter4 值 | iter3 對照 | Δ |
|------|:---:|:---:|:---:|
| 破產玩家數 | 96,835 (**96.84%**) | 94,804 (94.80%) | +2.04pp（更容易破產） |
| 觸 cap 未破產 | 3,165 (3.16%) | 5,196 (5.20%) | −2.04pp |
| lifetime RTP | **95.99%** | 96.71% | −0.72pp |

**破產玩家的 spin-to-bust 分佈**：

| 分位數 | iter4 | iter3 |
|-------|:---:|:---:|
| q10 | 478 | 529 |
| q25 | 752 | 838 |
| median | **1,384** | 1,558 |
| q75 | 2,703 | 3,080 |
| q90 | 4,822 | 5,375 |
| mean | 2,082 | 2,311 |

**期末結餘分佈（全 100K 玩家、含破產者=0）**：

| 分位數 | iter4 | iter3 |
|-------|:---:|:---:|
| q10 | 10 | 10 |
| median | 55 | 60 |
| q90 | 90 | 95 |
| top-1% | 23,140 | 30,190 |
| mean | 653 | 1,084 |

**單擊最大 win**：iter4 = **7,550**（vs iter3 6,550）——iter4 top FS session 略高。

### iter4 vs iter3 行為對照解讀

- **中位玩家 1,384 spin 破產**（iter3 1,558），生存時間縮短 11%
- **iter4 lifetime RTP 略低**（95.99% vs 96.71%）→ 破產率上升、mean 期末結餘從 1,084 掉到 653
- **top-1% 期末結餘從 30,190 掉到 23,140**（−23%）——iter4 bonus 觸發率整體較低（bonus RTP 13.84% vs iter3 15.99%），大贏機會變小
- **原因**：iter4 為了塞 30-slot reg cluster prefix，wild 和 FS 都被擠壓到 tail 較短區域，FS 觸發覆蓋率下降 → bonus 貢獻縮水 → 玩家更靠 base 中獎，波動性稍降但總 RTP 也降
- **玩家體感層面**：iter4 「所有圖案都可能中大獎」比 iter3 「只有 Clover 能滿盤」在 marketing 上明顯優越；統計層面則是 bonus 弱化的 trade-off

### 已知限制與 iter5 待辦

1. **Analytic-MC gap 2.6pp**：`make_strip_v4` shuffle tail 造成 FS 局部聚集 → 若加「同種 FS min gap ≥ 3」約束於 rejection sampling，analytic 應能對齊 MC 到 ±0.5pp
2. **cluster prefix 過度規則化**：玩家看多了會發現前 30 slot 固定順序 → 提高目押難度但也降低隨機性視覺。iter5 可以打亂 cluster 順序（保留 10 個 3-slot cluster 但排列不同）
3. **bonus RTP 13.84% 偏低**（iter3 15.99%、iter1 9.74%）：BAR/Crown 高 payout jackpot 可能被玩家目押破解 → 需要監測 optimal-play 對抗 RTP
4. **玩家模擬 lifetime RTP 95.99% ≈ Roy spec 下限**：seed 變動可能跌破 95%。iter5 fix 完 gap 後可將 target 拉回 0.96 直接命中

---

## [2026-07-21] iter5 → 修 FS spread，analytic ≡ MC

### 問題（iter4 收尾時發現）

iter4 analytic 99.11% vs MC 96.49% → gap **−2.62pp**。追蹤發現：`make_strip_v4` shuffle tail 造成同種 FS 局部聚集（reel 0 FS1 empirical/analytic = 0.83），共享 3-slot 窗口 → 有效觸發覆蓋率 < 3c/L → analytic 高估 → HL 校準錯位（實際 MC 低於 target）。

### 修正（三件套一起改）

**1. 加 constraint：`FS_MIN_GAP = 3`**

`make_strip_v4` 拒絕採樣新增 `_fs_gap_violated(strip, min_gap=3)` 檢查，每種 FS 在環狀 strip 上任兩位置最小距離 < 3 就 reject 重跑。3 是關鍵閾值——同種 FS 距離 ≥ 3 → 兩者所覆蓋的 3-slot 窗口完全不重疊 → 「至少 1 個 FS_y」的覆蓋率 = **3c_y/L 精確成立**。

**2. 修 analytic 公式（用 spread ceiling）**

`_analytic_core` 內 FS trigger 從 iter1–iter4 的 `1 - (1-p_fs)^3`（獨立抽樣近似）改為 `min(3·c_fs/L, 1)`（spread 精確）。物理輪帶 + gap 保證 → 兩者相等，不再是近似。

**3. HL target 拉回 0.96**

iter4 曾拉到 0.99 補償 analytic 高估；iter5 gap 收斂到 0.03pp → 直接以 0.96 為 target 命中，不用補償。

### HL Loop 結果

22 iter 收斂：baseline 51.59% → 96.00% analytic，MC 95.97%，gap **0.03pp** ≈ noise。

### Tuned Strips（iter5）

```
reel 0 (L=125): WILD:13 FS1:11 FS2:6 FS3:3 S0:3 S1:3 S2:6 S3:3 S4:9  S5:11 S6:11 S7:14 S8:15 S9:17
reel 1 (L=144): WILD:13 FS1:12 FS2:7 FS3:4 S0:4 S1:3 S2:7 S3:3 S4:11 S5:12 S6:14 S7:16 S8:18 S9:20
reel 2 (L=169): WILD:10 FS1:15 FS2:7 FS3:4 S0:4 S1:6 S2:8 S3:6 S4:12 S5:14 S6:16 S7:19 S8:21 S9:27
```

FS spread 驗證（每輪每種 FS 環狀最小 gap）：

| Reel | FS1 min_gap | FS2 min_gap | FS3 min_gap |
|------|:---:|:---:|:---:|
| 0 | 3 | 3 | 5 |
| 1 | 3 | 4 | 14 |
| 2 | 3 | 5 | 10 |

**每輪每種 FS 都 ≥ 3 ✅** → analytic 3c/L 精確成立。

### RTP 驗證：**analytic ≡ MC**

| 度量 | Analytic | MC 200K | Player sim ~230M | gap (Ana vs MC) |
|------|:---:|:---:|:---:|:---:|
| Total RTP | **96.00%** | **95.97%** | **96.01%** | **−0.03pp ✅** |
| Base | 72.76% | 72.70% | — | −0.06pp |
| Bonus | 23.24% | 23.27% | — | +0.03pp |
| FS1 觸發率 | ~1.75% | 1.757% | — | ≈0 |
| FS2 | ~0.25% | 0.249% | — | ≈0 |
| FS3 | ~0.05% | 0.048% | — | ≈0 |

**iter4 → iter5 gap 從 2.62pp 收斂到 0.03pp**（87× 收斂），Roy「analytic 對齊 MC」spec 達成。

### 玩家模擬（100K × 起始 10K × bet 100 × cap 10K spin）

| 指標 | iter5 | iter4 | Δ |
|------|:---:|:---:|:---:|
| 破產玩家 | 96,532 (**96.53%**) | 96,835 (96.84%) | −0.31pp |
| 觸 cap 未破產 | 3,468 (3.47%) | 3,165 (3.16%) | +0.31pp |
| lifetime RTP | **96.01%** | 95.99% | +0.02pp |
| 單擊最大 win | 6,650 | 7,550 | −900 |

**破產 spin 分佈**（iter5 vs iter4）：

| 分位數 | iter5 | iter4 |
|-------|:---:|:---:|
| q10 | 453 | 478 |
| q25 | 718 | 752 |
| median | **1,334** | 1,384 |
| q75 | 2,660 | 2,703 |
| q90 | 4,790 | 4,822 |
| mean | 2,045 | 2,082 |

**期末結餘分佈**（全 100K 含破產者）：

| 分位數 | iter5 | iter4 |
|-------|:---:|:---:|
| median | 55 | 55 |
| q90 | 90 | 90 |
| top-1% | **25,980** | 23,140 |
| mean | 751 | 653 |

### 玩家體感層面：iter4 → iter5 質變

- **FS1 (Red 7) 觸發率 0.91% → 1.76%（1.9×）**：中位玩家（1,334 spin）從 iter4 期望遇 12 次 Red 7 → iter5 期望遇 **23 次** → bonus 場景體感明顯變頻繁
- **Bonus RTP 佔比 13.84% → 23.27%（+9.43pp）**：iter5 把更多 RTP 撥給 bonus，base 相對縮水
- **top-1% 玩家帶錢離場從 23k → 26k（+12%）**：bonus 觸發率上升 → 大贏樣本增加
- **mean 期末結餘 653 → 751（+15%）**：平均更多玩家撐更久
- **設計哲學層面**：iter5 更接近日式パチスロ「頻繁小 bonus + 稀有大 jackpot」的玩法節奏，iter4 則偏向「賭 base 大線」

### 已知限制與未來 iter 待辦

1. **rejection sampling 效率**：iter5 加 FS gap constraint 後，`make_strip_v4` 每輪 shuffle 需要平均 ~10 次 retry 才通過（vs iter4 ~1 次）。目前 max_retries=500 綽綽有餘，但若未來 FS count 拉高或 L 縮短可能失敗
2. **Base RTP 掉到 72.70%**：低於一般 パチスロ base RTP 期望（75-80%）；玩家不觸發 bonus 時 base 中獎頻率偏低。可考慮加強 reg cluster tail 拉高 base
3. **cluster prefix 30 slot 固定順序仍是 optimal-play 破解點**：iter5 沒動這個。iter6 可打亂 cluster 順序（保留 10 個 3-slot cluster 但每輪不同）
4. **analytic ≡ MC 只在 3-line 27-cell 規則下成立**：若未來規則改（如 5-line, 10x10 grid），需重推 spread ceiling 公式


---

## [2026-07-22] iter6 → 撤 Wild max cluster + Wild payout=200 + exact_moments 精確枚舉

### 問題（Roy 新需求）

1. **撤掉 Wild 限制**：iter5 的 `WILD_MAX_CONSECUTIVE=2` 保證 Wild 滿盤數學上不可能，但也讓 Wild 3-line 這個玩家熟悉的老虎機大獎場景永不觸發
2. **給 Wild 賠率**：iter2 曾試過 300 後 revert 到 0，這次要正式給 Wild payout（Roy 授權自訂）
3. **RTP 落到 92-95%**：從 iter5 的 96% 往下調，貼近中北美賭場中段水位
4. **量化變異程度 & 平均可玩 spin 數**：iter5 只算 RTP，玩家 volatility 沒量化

### 修正（三件套一起改）

**1. 新增 `exact_moments.py`**：Law of Total Variance 精確枚舉

- **outer (確定性)**：對 $L_1 \times L_2 \times L_3 = 3{,}042{,}000$ 個 offset triple 全枚舉
- **inner (隨機)**：對每種 fs_mult 各跑 MC 500k Mali session 得 $(\mu_i, \sigma_i^2)$ 常數
- **合體**：
  $$\operatorname{Var}(X) = \mathbb{E}_o[\operatorname{Var}(X|o)] + \operatorname{Var}_o(\mathbb{E}[X|o])$$
  no-FS outcome: $\mathbb{E}[X|o]=$ base_win, $\operatorname{Var}[X|o]=0$
  FS_i outcome: $\mathbb{E}[X|o]=$ base_win $+ \mu_i$, $\operatorname{Var}[X|o]=\sigma_i^2$

單次成本：bonus MC 500k ≈ 28s + exact enumeration ≈ 15s（純 Python）。

**2. `iter6_wild_open.py`（不動 rtp_sim.py，monkey-patch approach）**

- `rtp_sim._has_wild_run = lambda strip, max_ok: False` → 撤 Wild max cluster
- `SYM['WILD'].payout = 200` → Wild 3-line 額外獎金
- HL target 96% → **93.5%，tol ±0.8pp**（窗 92.7-94.3%）

### 🔬 意外發現：Analytic Base RTP ≡ Exact Base RTP

對 iter5 tuned strips 跑 exact 對照 analytic：

| | Analytic | Exact | Δ |
|---|---:|---:|---:|
| Total RTP | 95.9959% | 96.0176% | +0.0217pp |
| **Base RTP** | **72.7607%** | **72.7607%** | **+0.0000pp** ✅ |
| **S9 Clover 貢獻** | **11.3791%** | **11.3791%** | **+0.0000pp** ✅ |

**原因**：

$$\mathbb{E}[m_1 \cdot m_2 \cdot m_3] = \mathbb{E}[m_1] \cdot \mathbb{E}[m_2] \cdot \mathbb{E}[m_3]$$

只需 reel 間獨立（物理成立），不需 reel 內 3 格獨立。而 $\mathbb{E}[m_r] = 3(c_s+c_W)/L$ 對**任何** strip 排列都精確成立（線性期望）。**Wild 相關性只影響二階以上動差（Var、skew、kurt）與 per-line-count 分佈形狀，一階完全免疫**。

iter0-5 記錄的「analytic vs MC 差 1.4pp」是 MC 雜訊 + FS bonus 獨立近似殘留，**不是** base RTP 有偏差。這修正了本專案先前的一個持續誤讀。

### Clover per-line-count 分佈：形狀偏移但期望值不變

同一 iter5 strips：

| k | Analytic P(k) | Exact P(k) | Δ |
|---:|---:|---:|---:|
| 0 | 84.082% | 86.801% | +2.72pp（更多空盤） |
| 1 | 6.807% | 4.450% | −2.36pp |
| 2 | 6.081% | 4.906% | −1.18pp |
| 3 | 0.605% | 0.943% | +0.34pp |
| 6 | 0.360% | 0.690% | +0.33pp |
| 12 | 0.053% | 0.126% | +0.07pp |
| 27 | 0.000175% | 0.000657% | ×3.75 |

Wild 相關性把中低 k 移到 0，高 k 機率放大。分佈變「要嘛沒有要嘛爆多」——variance 的來源。$\mathbb{E}[X]$ 兩邊抵消到相等；$\mathbb{E}[X^2]$ 靠 $P(k)\cdot k^2$，高 k 敏感度更大，exact σ 才是真數字。

### HL Loop 結果（iter6）

Baseline（HTML weights 縮放）在新 payout 下 RTP=51.86%（Wild payout=0→200 不影響 baseline 因為 Wild 通配貢獻沒動；只有 Wild 3-line 貢獻增加，但 Wild 密度低影響小）。HL 20 iter 收斂：

| iter | swap | RTP |
|:---:|:---|:---:|
| 0-17 | 幾乎全在 −S1/−S3 → +WILD（HL 找到最省事的拉升路徑） | 51.86% → 92.19% |
| 18 | reel 0: −S6 (Orange) +FS1 | 92.19% → 93.43% ✅ |

**20 iter 收斂到 analytic 93.43%**，MC/exact 對齊。策略讀來：「加 Wild 靠通配拉 base 是最有效率的 RTP knob，最後補一次 FS1 補 bonus」。

### Tuned Counts（iter6）

```
reel 0 (L=125): WILD:12 FS1:12 FS2:6 FS3:3 S0:3 S1:3 S2:6 S3:3 S4:9  S5:11 S6:11 S7:14 S8:15 S9:17
reel 1 (L=144): WILD:12 FS1:12 FS2:7 FS3:4 S0:4 S1:3 S2:7 S3:4 S4:11 S5:12 S6:14 S7:16 S8:18 S9:20
reel 2 (L=169): WILD:10 FS1:14 FS2:8 FS3:4 S0:4 S1:5 S2:8 S3:7 S4:12 S5:14 S6:16 S7:19 S8:21 S9:27
```

Wild 從 iter5 的 13/13/10 微調到 12/12/10；FS 分佈重排；reg 大致保留 iter5 pattern。

### RTP 驗證與變異度

| 度量 | Analytic | Exact enumeration |
|---|---:|---:|
| Total RTP | 93.4282% | **93.4254%** |
| Base RTP | 69.2965% | 69.2965% |
| Bonus RTP | 24.1317% | 24.1289% |
| **σ (單 spin sd)** | — | **254.65** |
| **CV (σ/E)** | — | **2.7257** |
| **Vol Idx (σ/bet)** | — | **2.5465** |
| **P(X=0)** | — | **60.60%** |

**Per-symbol RTP 貢獻**（exact，由高至低）：

| 圖案 | Payout | 貢獻 |
|---|---:|---:|
| 🍀 Clover | 35 | 10.67% |
| 🍒 Cherry | 40 | 8.91% |
| 🍋 Lemon | 45 | 8.43% |
| 🍇 Grape | 60 | 7.67% |
| 🍊 Orange | 50 | 7.48% |
| 🍉 Watermelon | 70 | 7.22% |
| 💎 Diamond | 110 | 6.68% |
| 🎰 BAR | 180 | 6.08% |
| 👑 Crown | 130 | 4.73% |
| 🔔 Bell | 80 | 2.91% |
| 🃏 **Wild** | **200** | **2.56%** |

Wild 貢獻 2.56% 中，**72% 來自單 wild 線**（Wild 通配到自己的 k=1）+ **25% 來自 2-wild 線**——payout=200 沒帶出「Wild 頂級大獎」的心理效果。

### 玩家模擬（100K 台 × 起始 10K × bet 100 × cap 20K spin）

| 指標 | iter6 |
|---|---:|
| 破產玩家 | 100,000 / 100,000（**100.00%**，cap 20K spin 內全 bust） |
| lifetime RTP | 90.90% |
| **平均破產 spin** | **1,093** |
| median | 829 |
| q10 / q90 | 367 / 2,138 |
| q25 / q75 | 525 / 1,358 |
| 單擊最大 win | 7,150 |

**純理論值** = 10000 / (100 × (1−0.9343)) = **1,522 spin**；實測平均 1,093 比理論短 **28%**——這是 volatility 懲罰（負向漂移 + 高 σ 讓破產成常態）。

### 設計偏差警示（→ iter7 起因）

**Wild 27 線在 iter6 中沒觸發**：shuffled strips 中 Wild 3 連在 3-window 內的機率 ≈ 0（Wild 密度 ~9%，shuffle 天然分散）。Wild payout=200 幾乎完全靠「單 wild 線」貢獻，「Wild 頂級大獎」的設計動機沒實現。

→ iter7 主動加 Wild cluster prefix 補這個洞。

### 已知限制與 iter7 待辦

1. Wild 27 線機率 = 0（沒有 cluster）
2. Wild payout 累加式：Wild 3 連時 reg 通配 27 條也一起賠 → 極端 upside，需在 cluster 補上後量化
3. Exact enumeration 15s 純 Python 太慢，不適合塞 HL inner loop → numpy vectorize 未做
4. lifetime RTP 90.9% vs exact 93.4% 差 2.5pp 是玩家全 bust 的截斷效應

---

## [2026-07-22] iter7 → 加 Wild cluster prefix + Wild payout=220（上線版）

### 問題（承 iter6）

iter6 撤 Wild 限制 + payout=200 但 Wild 27 線機率 = 0，「頂級大獎」沒發揮心理效果。iter7 主動放 Wild cluster 讓 27 線可觸發。

### 修正

**1. 新 strip builder `make_strip_v5`**（`iter7_wild_cluster.py` 內）

prefix 從 iter4 的 30 slot 擴到 **33 slot**：

```
[S0]*3 [S1]*3 [S2]*3 [S3]*3 [S4]*3 [S5]*3 [S6]*3 [S7]*3 [S8]*3 [S9]*3 [WILD]*3
```

三輪同停對應 offset：
- offset 0/3/6/…/27 → 對應 reg 27 線大獎（同 iter4-6）
- **offset 30 → Wild 27 線大獎（新）**

**2. Wild payout 200 → 220**（Roy 拍板）

### ⚠️ Wild 27 線機率修正

初次規劃時預估 $P = \frac{3 \cdot 3 \cdot 3}{L_1 L_2 L_3} = \frac{27}{3{,}042{,}000} \approx 8.87 \times 10^{-6}$（每 11 萬 spin）——**錯**。

cluster size N 保證的完美 window 數 = $N - W + 1$（W = window size = 3）。當 $N = W = 3$ 時只有 **1 個 offset** (off=30) 產生 [WILD, WILD, WILD]。要 3 個 offset 得放 5 連 wild ($5-3+1=3$)。

**正確**：

$$P(\text{Wild 27 線}) = \frac{1}{L_1 L_2 L_3} = \frac{1}{3{,}042{,}000} \approx 3.29 \times 10^{-7}$$

**約每 300 萬次 spin 一次**。

實測 = 0.00003287% vs 理論 0.00003288% → 比值 **0.9997** ✅ 完美吻合。

### HL Loop 結果（iter7）

20 iter 收斂，路徑跟 iter6 幾乎一樣（−S1/−S3 → +WILD 為主）：

| iter | swap | RTP |
|:---:|:---|:---:|
| 0-17 | 幾乎全 −S1/−S3 → +WILD | 51.89% → 92.45% |
| 18 | reel 2: −S3 (Bell) +FS1 | 92.45% → 93.48% ✅ |

**20 iter 收斂到 analytic 93.48%**。

### Tuned Counts（iter7）

```
reel 0 (L=125): WILD:12 FS1:11 FS2:6 FS3:3 S0:3 S1:3 S2:6 S3:3 S4:9  S5:11 S6:12 S7:14 S8:15 S9:17
reel 1 (L=144): WILD:12 FS1:12 FS2:7 FS3:4 S0:4 S1:3 S2:7 S3:4 S4:11 S5:12 S6:14 S7:16 S8:18 S9:20
reel 2 (L=169): WILD:10 FS1:15 FS2:8 FS3:4 S0:4 S1:5 S2:8 S3:6 S4:12 S5:14 S6:16 S7:19 S8:21 S9:27
```

Prefix layout 驗證：每輪 `[30:33] = 🃏🃏🃏` ✅

### RTP 驗證與變異度（exact enumeration）

| 度量 | iter6 | iter7 | Δ |
|---|---:|---:|---:|
| Total RTP | 93.4254% | **93.4446%** | +0.02pp |
| Base RTP | 69.2965% | 69.6817% | +0.39pp |
| Bonus RTP | 24.1289% | 23.7628% | −0.37pp |
| **σ** | 254.65 | **308.48** | **+21.1% ⬆** |
| CV | 2.7257 | 3.3012 | +21.1% |
| Vol Idx | 2.5465 | 3.0848 | +20.9% |
| **P(X=0)** | 60.60% | **64.46%** | **+3.9pp ⬆** |
| Wild RTP 貢獻 | 2.56% | 2.81% | +0.26pp |
| **單次最大 win** | 7,150 | **21,600** | **+202%** |

### 🎯 核心發現：σ ⇔ RTP decouple

- **RTP 幾乎沒變**（+0.02pp），但 **σ 大漲 21%**
- Wild cluster 讓 payoff 分佈的 kurtosis 上升
- 同一個 house edge（6.55%），玩家體感截然不同

$\mathbb{E}[X]$ 靠 $P(k)\cdot k$ 對稱抵消（Wild cluster 加高 k 但減低 k）；$\mathbb{E}[X^2]$ 靠 $P(k)\cdot k^2$，高 k 貢獻放大 → σ 拉升。這是 iter6 exact 對照時「Wild 相關性影響 Var 不影響 mean」的具體驗證。

### 🃏 Wild per-line-count 精確分佈

| k 線 | P(lines=k) | contrib RTP | 占 Wild total |
|---:|---:|---:|---:|
| 0 | 99.334% | 0% | — |
| 1 | 0.328% | 0.721% | 25.66% |
| **2** | 0.220% | **0.969%** ⭐ | 34.44% |
| 3 | 0.046% | 0.304% | 10.79% |
| 4 | 0.044% | 0.388% | 13.80% |
| 6 | 0.020% | 0.266% | 9.48% |
| 8 | 0.003% | 0.049% | 1.73% |
| 9 | 0.002% | 0.042% | 1.50% |
| 12 | 0.002% | 0.053% | 1.88% |
| 18 | 0.0005% | 0.018% | 0.65% |
| **27** | **0.00003%** | **0.002%** | **0.07%** ← 頭獎終於出現 |

**Wild 27 線 RTP 貢獻只有 0.002%**——極稀有大獎，實質是**心理誘餌**而非 RTP 主軸。Wild 貢獻 2.81% 中，超過 60% 來自 k=1 和 k=2。

### 玩家模擬（100K 台 × 起始 10K × bet 100 × cap 30K spin）

| 指標 | iter7 | iter6 | Δ |
|---|---:|---:|---:|
| 破產玩家 | 100,000（100%） | 100,000（100%） | — |
| lifetime RTP | 90.68% | 90.90% | −0.22pp |
| **平均破產 spin** | **1,067** | 1,093 | −2.4% |
| median | **752** | 829 | −9.3% |
| q10 / q90 | 322 / 2,170 | 367 / 2,138 | 尾巴略拉 |
| q25 / q75 | 463 / 1,299 | 525 / 1,358 | 更 skewed |
| 單擊最大 win | **21,600** | 7,150 | +202% |

**中位玩家更快破產（−9.3%）**，**q90 幸運兒略撐更久（+1.5%）**——σ 上升的必然結果：分佈變寬，兩端拉大。

### 設計選擇：iter6 vs iter7

- **iter6 = 溫和**：中位玩家 829 spin，最大 win 71.5× bet
- **iter7 = 爆點**：中位玩家 752 spin（−9.3%），最大 win 216× bet（+202%），偶發 Wild 27 線頂級大獎

Roy 選 **iter7 上線**。

### iter5-6-7 對照速查

| 維度 | iter5 | iter6 | iter7 |
|---|---:|---:|---:|
| Wild max cluster | ≤2 | ∞ | ∞ + cluster prefix |
| Wild payout | 0 | 200 | **220** |
| Wild 27 線可能性 | 0 | ~0 (shuffle) | 3.29e-7 ✅ |
| Total RTP | 96.02% | 93.43% | **93.44%** |
| σ | (未算) | 255 | **308** |
| P(X=0) | 61.15% | 60.60% | **64.46%** |
| Prefix 長度 | 30 slot | 30 slot | **33 slot** |
| 定位 | 教學/低度娛樂 | 標準商用 | 高爆點商用 |

### 上線動作

- `pachislot_mali.html` 已同步：REEL_STRIPS 替換為 iter7 tuned strips、SYMBOLS.WILD.payout 0→220
- wiki `[[concept_slot_rtp_calibration_hl]]` 加 iter6-7 section 130 行 + 檔案索引
- `.recall/context.md` 存本 session 摘要

### 已知限制與未來 iter 待辦

1. **exact_moments.py 純 Python 15s** — 要 numpy vectorize 才能進 HL inner loop 做 multi-objective 校準（現在還在 offline 分析工具階段）
2. **Wild 27 線機率 3.29e-7 極稀有** — 若要提高到「每 100 萬次一次」等心理常聽到的數字，得把 Wild cluster 拉到 5 連（$5-3+1=3$ 個 offset，機率 ×3）
3. **check_wins 累加式 Wild 3 連 payoff = 27,540** — 玩家真觸發拿 275× bet 大獎，本輪保留此設計，若日後想壓到 54× bet 得改核心邏輯改「取最高」
4. **RTP 曲線掃描未做** — 91/92/93/94/95 各一組拿 σ vs RTP 對照表可讓遊戲設計時 trade-off 更清楚
