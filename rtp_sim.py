"""
Pachislot Little Mary (小瑪莉) — 輪帶建置 × RTP 模擬 × HL 校準

Reference:
  - [[concept_heuristic_learning]] — Weng 2026, code-as-policy + coding-agent update
  - [[project_darkchess_npc]] — 同源 RTP 校準 pattern（NPC 棋力 + 經濟聯合校準）

Design:
  Engine  — 忠實移植 pachislot_mali.html JS 語意（14 SYMBOLS、27-line rule、
            FS 優先權觸發、Mali round 期望值封閉解）
  Strips  — 3 條長 30 的物理輪帶（typical pachislot 21~30），shuffled 打散
  Sim     — 解析式 base RTP（reel 獨立 → E[m1·m2·m3]=27·∏ p_match）
            + MC 驗證 + per-symbol 貢獻分解
  HL loop — state = strip composition
            policy = single-swap search（枚舉 +A/-B 對 3 輪 × 14 sym × 13 sym）
            feedback = |target_rtp - current_rtp|
            regression = seed-locked analytical RTP within [target±tol]

Usage:
  python -X utf8 rtp_sim.py                # 顯示現況 + 跑 HL 校準
  python -X utf8 rtp_sim.py --mc 1000000   # 加跑 MC 驗證
"""

from __future__ import annotations
import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ==================== Engine ====================

@dataclass
class Symbol:
    id: str
    char: str
    name: str
    stype: str        # 'reg' | 'wild' | 'fs'
    payout: int       # per-line at bet=100
    fs_mult: int = 0
    fs_spins: int = 0

SYMBOLS: List[Symbol] = [
    Symbol('WILD', '🃏', 'Wild',        'wild', 0),
    Symbol('FS1',  '🔴', 'Red 7',       'fs',   0, fs_mult=2, fs_spins=10),
    Symbol('FS2',  '🔵', 'Blue 7',      'fs',   0, fs_mult=3, fs_spins=10),
    Symbol('FS3',  '🟡', 'Gold 7',      'fs',   0, fs_mult=5, fs_spins=10),
    Symbol('S0',   '🎰', 'BAR',         'reg',  180),
    Symbol('S1',   '👑', 'Crown',       'reg',  130),
    Symbol('S2',   '💎', 'Diamond',     'reg',  110),
    Symbol('S3',   '🔔', 'Bell',        'reg',   80),
    Symbol('S4',   '🍉', 'Watermelon',  'reg',   70),
    Symbol('S5',   '🍇', 'Grape',       'reg',   60),
    Symbol('S6',   '🍊', 'Orange',      'reg',   50),
    Symbol('S7',   '🍋', 'Lemon',       'reg',   45),
    Symbol('S8',   '🍒', 'Cherry',      'reg',   40),
    Symbol('S9',   '🍀', 'Clover',      'reg',   35),
]

SYM: Dict[str, Symbol] = {s.id: s for s in SYMBOLS}
REG_IDS = [s.id for s in SYMBOLS if s.stype == 'reg']
FS_IDS  = [s.id for s in SYMBOLS if s.stype == 'fs']
WILD_ID = 'WILD'
ALL_IDS = [s.id for s in SYMBOLS]

MALI_PRIZES    = [10, 15, 20, 30, 50, 70]
MYSTERY_PRIZES = [75, 100, 150, 200, 250]

# E[Mali round val at bet=100, mult=1]:
# layout = 2 fixed (100, 150) + 1 mystery + 13 random from MALI_PRIZES
# 每 round uniform 隨機選 1/16 格；mystery 格觸發時再隨機抽 mystery prize
# E[val] = (100 + 150 + E[mystery] + 13*E[MALI_PRIZES]) / 16
E_MYSTERY = sum(MYSTERY_PRIZES) / len(MYSTERY_PRIZES)                # 155
E_MALI_CELL = sum(MALI_PRIZES) / len(MALI_PRIZES)                     # 32.5
E_MALI_VAL = (100 + 150 + E_MYSTERY + 13 * E_MALI_CELL) / 16          # 51.71875

REEL_LENGTHS = [125, 144, 169]  # iter4：三個 coprime → LCM = 組合數 = 3,042,000
WILD_MAX_CONSECUTIVE = 2         # 禁 wild 滿盤（任一 3-window 最多 2 wild）
WILD_MIN_PER_REEL = 3            # 每輪至少 3 wild
REG_CLUSTER_SIZE = 3             # iter4：**每個** reg 3-slot cluster → 每個可達 27 線
FS_MIN_GAP = 3                   # iter5：同種 FS 環狀最小 gap，讓 P_reel = 3c/L 精確成立（analytic ≡ MC）
# prefix 排序：按 REG_IDS 順序 S0-S0-S0 S1-S1-S1 ... S9-S9-S9（前 REG_CLUSTER_SIZE * 10 = 30 slot）

# ==================== Reel Strip 建置 ====================

def make_strip(counts: Dict[str, int], seed: int, length: int) -> List[str]:
    """組成物理輪帶：重複填入各符號 count 次後 shuffle。sum(counts) 必須等於 length。"""
    assert sum(counts.values()) == length, \
        f"counts must sum to {length}, got {sum(counts.values())} : {counts}"
    strip: List[str] = []
    for sid, c in counts.items():
        strip.extend([sid] * c)
    rng = random.Random(seed)
    rng.shuffle(strip)
    return strip

def _has_wild_run(strip: List[str], max_ok: int) -> bool:
    """回傳 True 若 strip（環狀）任一位置有 > max_ok 個連續 Wild。"""
    L = len(strip)
    for i in range(L):
        run = 0
        for k in range(max_ok + 1):
            if strip[(i + k) % L] == WILD_ID:
                run += 1
            else:
                break
        if run > max_ok:
            return True
    return False

def _fs_gap_violated(strip: List[str], min_gap: int = FS_MIN_GAP) -> bool:
    """iter5：回傳 True 若任一種 FS 在 strip（環狀）內有兩個位置的最小距離 < min_gap。
    min_gap=3 → 同種 FS 至少隔 3 slot → 不共享任何 3-slot 窗口 → P_reel = 3c/L 精確成立。"""
    L = len(strip)
    for fs_id in FS_IDS:
        positions = [i for i, s in enumerate(strip) if s == fs_id]
        if len(positions) < 2:
            continue
        for a, b in zip(positions, positions[1:]):
            if b - a < min_gap:
                return True
        # 環狀 wrap：最後一個位置到第一個位置
        if L - positions[-1] + positions[0] < min_gap:
            return True
    return False

def make_strip_v4(
    counts: Dict[str, int],
    seed: int,
    length: int,
    cluster_size: int = REG_CLUSTER_SIZE,
    wild_max_consecutive: int = WILD_MAX_CONSECUTIVE,
    max_retries: int = 500,
) -> List[str]:
    """iter4 strip 建構：**每個** reg 符號都放一段 cluster_size 連續 slot 於前段
    → 3 輪同時停在對應 offset 時任一 reg 都可達 27 線。

      - 前 cluster_size × len(REG_IDS) = 30 slot 為固定 prefix
        prefix = [S0]*3 + [S1]*3 + ... + [S9]*3（按 REG_IDS 順序）
      - 每個 reg 的 offset 起始 = REG_IDS.index(sym) * cluster_size
        e.g. S0 cluster 在 [0:3]、S1 在 [3:6]、... S9 在 [27:30]
      - 其餘 (length - 30) slot 為 remaining counts shuffle
      - 拒絕採樣：shuffled 部分（含環狀 wrap 檢查）不能有 > wild_max_consecutive 連續 Wild
        prefix 全為 reg → wrap boundary 天然安全
    """
    for rid in REG_IDS:
        assert counts.get(rid, 0) >= cluster_size, \
            f"iter4 需要每個 reg 符號 ≥ {cluster_size} 張才能建 cluster，{rid} 只有 {counts.get(rid, 0)}"
    assert sum(counts.values()) == length, \
        f"counts must sum to {length}, got {sum(counts.values())}"

    # Build prefix: 按 REG_IDS 順序連放 cluster
    prefix: List[str] = []
    for rid in REG_IDS:
        prefix.extend([rid] * cluster_size)
    prefix_len = len(prefix)  # = cluster_size * 10 = 30

    # Remaining = counts - cluster consumption
    remaining = dict(counts)
    for rid in REG_IDS:
        remaining[rid] -= cluster_size
    others: List[str] = []
    for sid, c in remaining.items():
        if c > 0:
            others.extend([sid] * c)
    assert len(others) == length - prefix_len

    for retry in range(max_retries):
        rng = random.Random(seed + retry * 10007)
        shuffled = list(others)
        rng.shuffle(shuffled)
        strip = prefix + shuffled
        if _has_wild_run(strip, wild_max_consecutive):
            continue
        # iter5: 同種 FS min gap 檢查 → 讓 analytic P_reel = 3c/L 精確
        if _fs_gap_violated(strip, FS_MIN_GAP):
            continue
        return strip
    raise RuntimeError(
        f"make_strip_v4: 無法在 {max_retries} 次 retry 內同時滿足 wild ≤ {wild_max_consecutive} 連續 + FS min gap {FS_MIN_GAP}（"
        f"length={length}, wild_count={counts.get('WILD', 0)}, fs_counts={[counts.get(f, 0) for f in FS_IDS]}）"
    )

def initial_counts_from_html_weights(length: int) -> Dict[str, int]:
    """按原始 HTML weights ratio 縮放到 length slot（sum 需正好等於 length）。

    做法：按比例配額 round 到 int（每符號至少 1），尾差配到最高 count 的 reg 符號調平。
    對長輪帶（>50 slot）不會把單一符號堆到誇張的數字。
    """
    # HTML weights（原始總和 82）
    base_weights = {
        'WILD': 3, 'FS1': 7, 'FS2': 4, 'FS3': 2,
        'S0': 2, 'S1': 3, 'S2': 4, 'S3': 5, 'S4': 6,
        'S5': 7, 'S6': 8, 'S7': 9, 'S8': 10, 'S9': 12,
    }
    total_w = sum(base_weights.values())
    result: Dict[str, int] = {sid: max(1, round(w * length / total_w)) for sid, w in base_weights.items()}
    # 尾差配置到最高 count 的 reg 符號
    diff = length - sum(result.values())
    while diff != 0:
        reg_sorted = sorted(
            ((sid, n) for sid, n in result.items() if SYM[sid].stype == 'reg'),
            key=lambda kv: -kv[1],
        )
        sid = reg_sorted[0][0]
        if diff > 0:
            result[sid] += 1
            diff -= 1
        elif result[sid] > 1:
            result[sid] -= 1
            diff += 1
        else:
            break
    assert sum(result.values()) == length, f"scaling failed: {result} sum={sum(result.values())}"
    return result

def counts_of(strip: List[str]) -> Dict[str, int]:
    return dict(Counter(strip))

# ==================== 解析式 RTP ====================

def _analytic_core(ps: List[Dict[str, float]]) -> Dict:
    """給定 3 輪的 per-symbol 概率 ps[r][sid]，回傳解析 RTP 分解。

    公式：
      per reel r, per 非 FS sym: p_match(r, sym) = c_sym(r)/L + c_wild(r)/L
      per reel r, WILD sym:      p_match(r, WILD) = c_wild(r)/L        （wild 只由 wild match，不吃自己兩次）
      E[m_i] = 3 * p_match_i；E[m1·m2·m3] = 27 · ∏ p_match_i          （linearity + reel 間獨立，exact）
      base_RTP = Σ_reg∪{WILD} 27·∏ p_match_i · payout / 100

      FS 觸發（iter5 起）：make_strip_v4 保證同種 FS min gap ≥ 3 → 每 reel P(≥1 於 3 row) = 3·c_fs/L 精確
                       （iter1–iter4 用 1-(1-p_fs)^3 獨立近似，會低估物理輪帶 spread FS 的覆蓋率）
      優先權 FS1→FS2→FS3
      bonus_RTP = Σ_fs P(fs 觸發) · fs_spins · E_MALI_VAL · fs_mult / 100
    """
    per_sym: Dict[str, float] = {}
    # WILD 本身（3-Wild line jackpot）
    prod = 1.0
    for r in range(3):
        prod *= 3 * ps[r][WILD_ID]
    per_sym[WILD_ID] = prod * SYM[WILD_ID].payout / 100
    # 一般 reg 符號（含 Wild 通配替代）
    for reg_id in REG_IDS:
        sym = SYM[reg_id]
        prod = 1.0
        for r in range(3):
            p_match = ps[r][reg_id] + ps[r][WILD_ID]
            prod *= 3 * p_match
        per_sym[reg_id] = prod * sym.payout / 100

    fs_match_prob: Dict[str, float] = {}
    for fs_id in FS_IDS:
        # iter5: 同種 FS min gap ≥ 3 (由 make_strip_v4 保證) → P_reel = 3c/L 精確
        # 若 3c/L > 1（極端高密度不會發生於本設計），退回 1
        p = 1.0
        for r in range(3):
            p *= min(3 * ps[r][fs_id], 1.0)
        fs_match_prob[fs_id] = p

    fs_trigger: Dict[str, float] = {}
    fs_trigger['FS1'] = fs_match_prob['FS1']
    fs_trigger['FS2'] = fs_match_prob['FS2'] * (1 - fs_match_prob['FS1'])
    fs_trigger['FS3'] = fs_match_prob['FS3'] * (1 - fs_match_prob['FS1']) * (1 - fs_match_prob['FS2'])

    bonus_rtp = sum(
        fs_trigger[fs_id] * SYM[fs_id].fs_spins * E_MALI_VAL * SYM[fs_id].fs_mult / 100
        for fs_id in FS_IDS
    )
    base_rtp = sum(per_sym.values())
    return {
        'per_symbol_contrib': per_sym,
        'fs_match_prob': fs_match_prob,
        'fs_trigger_rate': fs_trigger,
        'base_rtp': base_rtp,
        'bonus_rtp': bonus_rtp,
        'total_rtp': base_rtp + bonus_rtp,
    }

def analytic_rtp(strips: List[List[str]]) -> Dict:
    """解析式 RTP，接受不同長度的三條輪帶。"""
    counts = [counts_of(s) for s in strips]
    lengths = [len(s) for s in strips]
    ps = [{sid: counts[r].get(sid, 0) / lengths[r] for sid in ALL_IDS} for r in range(3)]
    return _analytic_core(ps)

def analytic_rtp_from_counts(counts_per_reel: List[Dict[str, int]], lengths: List[int]) -> Dict:
    """跳過 shuffle，只用 counts 算 RTP（HL 內迴圈用）。lengths 必須逐輪指定。"""
    ps = [{sid: counts_per_reel[r].get(sid, 0) / lengths[r] for sid in ALL_IDS} for r in range(3)]
    return _analytic_core(ps)

# ==================== Monte Carlo（驗證用） ====================

def spin_reels(strips: List[List[str]], rng: random.Random) -> List[List[str]]:
    out = []
    for strip in strips:
        L = len(strip)
        off = rng.randrange(L)
        out.append([strip[(off + i) % L] for i in range(3)])
    return out

def check_wins(windows: List[List[str]]) -> Tuple[int, Optional[str]]:
    """回傳 (base_payout_at_bet100, fs_triggered_id_or_None)。
    FS 優先權：FS1 → FS2 → FS3（比對 pachislot_mali.html triggerFreeSpin fsMode guard）。
    Wild 3-line jackpot：per-reel 只算純 Wild（不重複算 wild 通配對自己的 match）。
    """
    total = 0
    fs_hit: Optional[str] = None
    for fs_id in FS_IDS:
        m = [sum(1 for sid in w if sid == fs_id) for w in windows]
        if m[0] and m[1] and m[2]:
            fs_hit = fs_id
            break
    # WILD 本身 3-line：每輪計 Wild 數
    m = [sum(1 for sid in w if sid == WILD_ID) for w in windows]
    if m[0] and m[1] and m[2]:
        total += m[0] * m[1] * m[2] * SYM[WILD_ID].payout
    for reg_id in REG_IDS:
        sym = SYM[reg_id]
        m = [sum(1 for sid in w if sid == reg_id or SYM[sid].stype == 'wild') for w in windows]
        if m[0] and m[1] and m[2]:
            total += m[0] * m[1] * m[2] * sym.payout
    return total, fs_hit

def mc_simulate(strips: List[List[str]], n_spins: int, seed: int = 42) -> Dict:
    rng = random.Random(seed)
    total_bet = 0
    total_win = 0
    base_win = 0
    bonus_win = 0
    fs_count = {fs_id: 0 for fs_id in FS_IDS}
    for _ in range(n_spins):
        total_bet += 100
        windows = spin_reels(strips, rng)
        w, fs = check_wins(windows)
        total_win += w
        base_win += w
        if fs is not None:
            fs_count[fs] += 1
            mult = SYM[fs].fs_mult
            spins = SYM[fs].fs_spins
            # 一個 FS session 中的所有 spin 都在同一個 layout 上 landing
            # layout 是每 session 生成一次（見 triggerFreeSpin: this.maliItems = generateMaliItems(...)）
            layout = [100, 150, 'M'] + [rng.choice(MALI_PRIZES) for _ in range(13)]
            rng.shuffle(layout)
            for _ in range(spins):
                cell = layout[rng.randrange(16)]
                if cell == 'M':
                    prize = rng.choice(MYSTERY_PRIZES)
                else:
                    prize = cell
                bonus_win += prize * mult
                total_win += prize * mult
    return {
        'n_spins': n_spins,
        'rtp_total': total_win / total_bet,
        'rtp_base': base_win / total_bet,
        'rtp_bonus': bonus_win / total_bet,
        'fs_trigger_rate': {k: v / n_spins for k, v in fs_count.items()},
    }

def _single_spin_win(strips: List[List[str]], rng: random.Random) -> int:
    """單次 spin 的完整結算，回傳玩家實得（含 FS session 展開），bet 100 base。"""
    windows = spin_reels(strips, rng)
    win, fs = check_wins(windows)
    if fs is None:
        return win
    mult = SYM[fs].fs_mult
    spins = SYM[fs].fs_spins
    layout = [100, 150, 'M'] + [rng.choice(MALI_PRIZES) for _ in range(13)]
    rng.shuffle(layout)
    for _ in range(spins):
        cell = layout[rng.randrange(16)]
        prize = rng.choice(MYSTERY_PRIZES) if cell == 'M' else cell
        win += prize * mult
    return win

def _build_base_win_tables(strips: List[List[str]]) -> Tuple[List[int], List[int]]:
    """為玩家模擬預算：把每輪每個 offset 的 3-slot 窗口壓成 (count_bitmap, base_payout_multiplier)。

    回傳 (win_by_combo, fs_by_combo) — 這裡改用「不 join 三輪」的形式：
    給定 offset o_r，回傳
      window_stats[r][o_r] = (per_sym_count_dict, fs_hit_dict)

    這樣單 spin 只要查 3 個 dict + 一個 3-乘積迴圈。"""
    # 為避免建 829K 大表（memory heavy），改用 per-reel per-offset 預算
    per_reel: List[List[Dict]] = []
    for strip in strips:
        L = len(strip)
        reel_stats = []
        for off in range(L):
            w = [strip[(off + i) % L] for i in range(3)]
            counts_reg = {rid: sum(1 for sid in w if sid == rid or SYM[sid].stype == 'wild') for rid in REG_IDS}
            counts_fs = {fid: sum(1 for sid in w if sid == fid) for fid in FS_IDS}
            reel_stats.append((counts_reg, counts_fs))
        per_reel.append(reel_stats)
    return per_reel

def _fast_spin_win(per_reel_stats, rng: random.Random) -> int:
    """用預算表查一次 spin 的完整 win（含 FS session）。"""
    o0 = rng.randrange(len(per_reel_stats[0]))
    o1 = rng.randrange(len(per_reel_stats[1]))
    o2 = rng.randrange(len(per_reel_stats[2]))
    c0r, c0f = per_reel_stats[0][o0]
    c1r, c1f = per_reel_stats[1][o1]
    c2r, c2f = per_reel_stats[2][o2]

    win = 0
    for reg_id in REG_IDS:
        m0, m1, m2 = c0r[reg_id], c1r[reg_id], c2r[reg_id]
        if m0 and m1 and m2:
            win += m0 * m1 * m2 * SYM[reg_id].payout

    # FS 優先權：FS1 → FS2 → FS3
    fs = None
    for fs_id in FS_IDS:
        if c0f[fs_id] and c1f[fs_id] and c2f[fs_id]:
            fs = fs_id
            break

    if fs is None:
        return win

    mult = SYM[fs].fs_mult
    spins = SYM[fs].fs_spins
    layout = [100, 150, 'M'] + [rng.choice(MALI_PRIZES) for _ in range(13)]
    rng.shuffle(layout)
    for _ in range(spins):
        cell = layout[rng.randrange(16)]
        prize = rng.choice(MYSTERY_PRIZES) if cell == 'M' else cell
        win += prize * mult
    return win

def _quantile(data: List[float], q: float) -> float:
    """簡易 quantile（無 numpy 依賴），data 必須已排序。"""
    if not data:
        return float('nan')
    idx = q * (len(data) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(data) - 1)
    frac = idx - lo
    return data[lo] * (1 - frac) + data[hi] * frac

def simulate_players(
    strips: List[List[str]],
    n_players: int = 100_000,
    initial_balance: int = 10_000,
    bet: int = 100,
    max_spins: int = 100_000,
    seed: int = 42,
) -> Dict:
    """跑 n_players 台獨立玩家，每人固定下注 bet，直到破產（balance < bet）或觸及 max_spins。

    回傳統計：
      - bust_rate：破產玩家比例
      - spins_to_bust 分佈（quartiles + mean）
      - final_balance 分佈（所有玩家，含破產者填 0）
      - biggest_single_win：所有 spin 中最大單擊
      - top_1pct_final_balance：前 1% 玩家的期末結餘
      - lifetime_rtp：所有玩家總下注 / 總 win（含 FS session），與 mc_simulate 對照
    """
    rng = random.Random(seed)
    per_reel_stats = _build_base_win_tables(strips)
    spins_to_bust: List[int] = []
    final_balances: List[float] = []
    biggest_win = 0
    total_bet_all = 0
    total_win_all = 0
    bust_count = 0
    hit_cap = 0

    for _ in range(n_players):
        balance = initial_balance
        spins = 0
        while balance >= bet and spins < max_spins:
            balance -= bet
            total_bet_all += bet
            win = _fast_spin_win(per_reel_stats, rng)
            balance += win
            total_win_all += win
            biggest_win = max(biggest_win, win)
            spins += 1
        if balance < bet:
            bust_count += 1
            spins_to_bust.append(spins)
        else:
            hit_cap += 1
        final_balances.append(balance)

    final_balances.sort()
    spins_to_bust.sort()

    return {
        'n_players': n_players,
        'initial_balance': initial_balance,
        'bet': bet,
        'max_spins': max_spins,
        'bust_count': bust_count,
        'bust_rate': bust_count / n_players,
        'hit_max_spin_cap': hit_cap,
        'spins_to_bust_mean': (sum(spins_to_bust) / len(spins_to_bust)) if spins_to_bust else float('nan'),
        'spins_to_bust_q10': _quantile(spins_to_bust, 0.10),
        'spins_to_bust_q25': _quantile(spins_to_bust, 0.25),
        'spins_to_bust_median': _quantile(spins_to_bust, 0.50),
        'spins_to_bust_q75': _quantile(spins_to_bust, 0.75),
        'spins_to_bust_q90': _quantile(spins_to_bust, 0.90),
        'final_balance_mean': sum(final_balances) / len(final_balances),
        'final_balance_median': _quantile(final_balances, 0.50),
        'final_balance_q10': _quantile(final_balances, 0.10),
        'final_balance_q90': _quantile(final_balances, 0.90),
        'final_balance_top1pct': _quantile(final_balances, 0.99),
        'biggest_single_win': biggest_win,
        'lifetime_rtp': (total_win_all / total_bet_all) if total_bet_all else float('nan'),
    }

# ==================== HL Loop ====================

def initial_counts_uniform() -> Dict[str, int]:
    """三輪都用同一組 counts。以 HTML weights 為初始（照設計者本意）。"""
    return initial_counts_from_html_weights()

def hl_single_swap_search(
    counts_per_reel: List[Dict[str, int]],
    lengths: List[int],
    target: float,
    min_wild_per_reel: int = 0,
    min_fs_per_reel: int = 0,
    max_reg_per_reel: Optional[int] = None,
    min_all_reg_per_reel: int = 0,
) -> Optional[Tuple[int, str, str, List[Dict[str, int]], float]]:
    """枚舉所有 (reel, from_sym, to_sym) 單交換，回傳最能拉近 gap 的那個。

    Constraints：
      - min_wild_per_reel：每輪 WILD ≥ N（wild 通配基本量）
      - min_fs_per_reel：每輪每種 FS_X ≥ N（保證三種 bonus 都能觸發）
      - max_reg_per_reel：每輪任一 非-Wild 符號 ≤ N（避免視覺失衡）
      - min_all_reg_per_reel：iter4 每輪**每個** reg 符號 ≥ N（保留每個 reg 的 3-slot cluster 原料）
    """
    cur = analytic_rtp_from_counts(counts_per_reel, lengths)
    cur_gap = abs(target - cur['total_rtp'])
    best = None
    best_gap = cur_gap
    for r_idx in range(3):
        cnt = counts_per_reel[r_idx]
        for from_s in list(cnt.keys()):
            if cnt[from_s] == 0:
                continue
            # Constraint check：不能把 WILD 換掉到少於 min
            if from_s == 'WILD' and cnt.get('WILD', 0) - 1 < min_wild_per_reel:
                continue
            if from_s in FS_IDS and cnt.get(from_s, 0) - 1 < min_fs_per_reel:
                continue
            if from_s in REG_IDS and cnt.get(from_s, 0) - 1 < min_all_reg_per_reel:
                continue
            for to_s in ALL_IDS:
                if from_s == to_s:
                    continue
                # Constraint check：不能把 reg/FS 符號加到超過 max（WILD 不設上限，讓 cluster 及 base RTP 有調節空間）
                if max_reg_per_reel is not None and SYM[to_s].stype != 'wild' \
                   and cnt.get(to_s, 0) + 1 > max_reg_per_reel:
                    continue
                new_cnt = dict(cnt)
                new_cnt[from_s] -= 1
                new_cnt[to_s] = new_cnt.get(to_s, 0) + 1
                if new_cnt[from_s] == 0:
                    del new_cnt[from_s]
                new_reels = [c if i != r_idx else new_cnt for i, c in enumerate(counts_per_reel)]
                new_r = analytic_rtp_from_counts(new_reels, lengths)
                new_gap = abs(target - new_r['total_rtp'])
                if new_gap < best_gap - 1e-6:
                    best_gap = new_gap
                    best = (r_idx, from_s, to_s, new_reels, new_r['total_rtp'])
    return best

def hl_calibrate(
    initial_counts_per_reel: List[Dict[str, int]],
    lengths: List[int],
    target: float = 0.96,
    tol: float = 0.005,
    max_iter: int = 200,
    verbose: bool = True,
    min_wild_per_reel: int = 0,
    min_fs_per_reel: int = 0,
    max_reg_per_reel: Optional[int] = None,
    min_all_reg_per_reel: int = 0,
) -> Tuple[List[Dict[str, int]], List[Dict]]:
    """HL 主迴圈：single-swap gradient-like search。

    對應 HS 架構（見 concept_heuristic_learning）:
      state    — counts_per_reel（三輪 composition）
      policy   — hl_single_swap_search（規則：選最能收斂 gap 的單交換）
      feedback — analytic_rtp_from_counts 回傳的 RTP + per_symbol_contrib
      memory   — history list（每 iter 記錄 gap、swap、RTP 分解）
      test     — |RTP - target| < tol
    """
    counts = [dict(c) for c in initial_counts_per_reel]
    history: List[Dict] = []
    for it in range(max_iter):
        r = analytic_rtp_from_counts(counts, lengths)
        gap = target - r['total_rtp']
        history.append({
            'iter': it,
            'rtp_total': r['total_rtp'],
            'rtp_base': r['base_rtp'],
            'rtp_bonus': r['bonus_rtp'],
            'gap': gap,
        })
        if verbose:
            print(f"iter {it:3d}: RTP={r['total_rtp']*100:6.2f}% "
                  f"(base={r['base_rtp']*100:5.2f}%, bonus={r['bonus_rtp']*100:5.2f}%) "
                  f"gap={gap*100:+6.2f}pp")
        if abs(gap) < tol:
            if verbose:
                print(f"→ Converged (|gap| < {tol*100:.1f}pp) after {it} iterations.\n")
            break
        step = hl_single_swap_search(counts, lengths, target,
                                     min_wild_per_reel=min_wild_per_reel,
                                     min_fs_per_reel=min_fs_per_reel,
                                     max_reg_per_reel=max_reg_per_reel,
                                     min_all_reg_per_reel=min_all_reg_per_reel)
        if step is None:
            if verbose:
                print(f"→ No improving swap; stopping at iter {it}.\n")
            break
        r_idx, from_s, to_s, new_counts, new_rtp = step
        history[-1]['swap'] = f"reel{r_idx}: -1 {from_s} / +1 {to_s} → RTP={new_rtp*100:.2f}%"
        if verbose:
            print(f"           swap → reel{r_idx}: -1 {from_s}  +1 {to_s}")
        counts = new_counts
    return counts, history

# ==================== 主流程 ====================

def fmt_counts(counts: Dict[str, int]) -> str:
    ordered = sorted(counts.items(), key=lambda kv: ALL_IDS.index(kv[0]))
    return ' '.join(f"{sid}:{c}" for sid, c in ordered)

def report(strips: List[List[str]], label: str) -> Dict:
    print(f"\n===== {label} =====")
    for i, s in enumerate(strips):
        print(f"reel {i} (L={len(s)}) counts: {fmt_counts(counts_of(s))}")
    r = analytic_rtp(strips)
    print(f"\nBase RTP     : {r['base_rtp']*100:6.2f}%")
    print(f"Bonus RTP    : {r['bonus_rtp']*100:6.2f}%")
    print(f"TOTAL RTP    : {r['total_rtp']*100:6.2f}%")
    print(f"\nFS 觸發率（每 spin）:")
    for fs_id in FS_IDS:
        print(f"  {SYM[fs_id].char} {SYM[fs_id].name:<12} 觸發 {r['fs_trigger_rate'][fs_id]*100:.3f}% "
              f"(單觸發期望 bonus={SYM[fs_id].fs_spins*E_MALI_VAL*SYM[fs_id].fs_mult/100:.2f}×bet)")
    print(f"\nBase 各符號 RTP 貢獻:")
    for reg_id in REG_IDS:
        c = r['per_symbol_contrib'][reg_id]
        s = SYM[reg_id]
        print(f"  {s.char} {s.name:<12} payout={s.payout:>3}  → {c*100:5.2f}%")
    return r

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', type=float, default=0.96)
    parser.add_argument('--tol', type=float, default=0.005)
    parser.add_argument('--seed', type=int, default=20260720)
    parser.add_argument('--mc', type=int, default=0, help='Monte Carlo spins for verification')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--lengths', type=str, default=None,
                        help='comma-separated per-reel lengths, e.g. "28,30,32" (default: module REEL_LENGTHS)')
    parser.add_argument('--max-reg', type=int, default=40,
                        help='每輪任一 非-Wild 符號的上限 count（避免視覺失衡；0 = 不設；iter4 長輪帶 default 放大）')
    parser.add_argument('--players', type=int, default=0,
                        help='玩家模擬台數，0=跳過（100000 = 100K 玩家）')
    parser.add_argument('--initial-balance', type=int, default=10000,
                        help='玩家起始信用點數')
    parser.add_argument('--bet', type=int, default=100)
    parser.add_argument('--max-spins', type=int, default=100000,
                        help='玩家單次 session 最大 spin 數上限（避免無限迴圈）')
    args = parser.parse_args()
    if args.max_reg <= 0:
        args.max_reg = None

    lengths = [int(x) for x in args.lengths.split(',')] if args.lengths else list(REEL_LENGTHS)
    assert len(lengths) == 3, f"need exactly 3 reel lengths, got {lengths}"

    # 1) baseline：把 HTML 現行 weights 各自縮放到每輪 length
    baseline_reels = [initial_counts_from_html_weights(L) for L in lengths]
    baseline_strips = [
        make_strip(baseline_reels[i], seed=args.seed + i, length=lengths[i]) for i in range(3)
    ]
    report(baseline_strips, f"BASELINE（HTML weights → 每輪 L={lengths} 物理輪帶）")

    # 2) HL 校準（iter4 constraints：WILD_MIN + 每個 reg ≥ REG_CLUSTER_SIZE + FS ≥ 1）
    #    先補 baseline：wild ≥ WILD_MIN_PER_REEL、每個 reg ≥ REG_CLUSTER_SIZE
    seed_counts: List[Dict[str, int]] = []
    for c in baseline_reels:
        cc = dict(c)
        # 逐一確保每個 reg 至少 REG_CLUSTER_SIZE、WILD 至少 WILD_MIN
        # 若不足，從最豐富的 reg 抽（reg 是 pool 大戶，通常 S8/S9 有得抽）
        def _need_map():
            m = {'WILD': max(0, WILD_MIN_PER_REEL - cc.get('WILD', 0))}
            for rid in REG_IDS:
                m[rid] = max(0, REG_CLUSTER_SIZE - cc.get(rid, 0))
            return m
        needs = _need_map()
        while sum(needs.values()) > 0:
            # 找 pool：最豐富的 reg 且非缺口目標
            reg_by_count = sorted(
                [(sid, cc.get(sid, 0)) for sid in REG_IDS if cc.get(sid, 0) > REG_CLUSTER_SIZE],
                key=lambda kv: -kv[1],
            )
            if not reg_by_count:
                raise RuntimeError(f"baseline 無足夠原料補 iter4 constraints: cc={cc}, needs={needs}")
            donor = reg_by_count[0][0]
            for target_sym, need in list(needs.items()):
                if need == 0:
                    continue
                take = min(need, cc[donor] - REG_CLUSTER_SIZE)
                if take <= 0:
                    break
                cc[donor] -= take
                cc[target_sym] = cc.get(target_sym, 0) + take
            needs = _need_map()
        seed_counts.append(cc)

    print(f"\n===== HL Loop（target RTP={args.target*100:.1f}%, tol={args.tol*100:.1f}pp, "
          f"lengths={lengths}, constraints: WILD≥{WILD_MIN_PER_REEL} + 每 reg ≥{REG_CLUSTER_SIZE} "
          f"+ 每種 FS≥1 + 非-Wild≤{args.max_reg}）=====\n")
    tuned_reels, history = hl_calibrate(
        seed_counts, lengths, target=args.target, tol=args.tol, verbose=not args.quiet,
        min_wild_per_reel=WILD_MIN_PER_REEL,
        min_fs_per_reel=1,
        max_reg_per_reel=args.max_reg,
        min_all_reg_per_reel=REG_CLUSTER_SIZE,
    )
    # 用 iter4 v4 builder：10 個 reg 全 cluster 前 30 slot + wild 打散
    tuned_strips = [
        make_strip_v4(c, seed=args.seed + 100 + i, length=lengths[i])
        for i, c in enumerate(tuned_reels)
    ]
    report(tuned_strips, "TUNED（HL 校準後，iter4：10 個 reg 全 cluster + wild 打散）")

    # 額外驗證：iter4 strip 每個 reg cluster 都存在 + wild 打散
    print(f"\n===== iter4 strip 約束驗證 =====")
    for i, s in enumerate(tuned_strips):
        wild_ok = not _has_wild_run(s, WILD_MAX_CONSECUTIVE)
        cluster_ok = True
        for idx, rid in enumerate(REG_IDS):
            start = idx * REG_CLUSTER_SIZE
            if not all(s[start + k] == rid for k in range(REG_CLUSTER_SIZE)):
                cluster_ok = False
                break
        print(f"reel {i} (L={len(s)}): wild≤{WILD_MAX_CONSECUTIVE} 連續 = {'✅' if wild_ok else '❌'}, "
              f"10 reg cluster prefix[0:30] = {'✅' if cluster_ok else '❌'}")

    # 驗證 27 線可達
    print(f"\n===== 27 線可達性驗證 =====")
    print("每符號每輪的窗口最大匹配數（含 Wild 通配）：")
    for reg_id in REG_IDS:
        maxes = []
        for strip in tuned_strips:
            L = len(strip)
            best = 0
            for off in range(L):
                win = [strip[(off + i) % L] for i in range(3)]
                m = sum(1 for s in win if s == reg_id or s == 'WILD')
                best = max(best, m)
            maxes.append(best)
        max_lines = maxes[0] * maxes[1] * maxes[2]
        marker = " ✅" if max_lines == 27 else f" ⚠ max={max_lines}線"
        print(f"  {SYM[reg_id].char} {SYM[reg_id].name:<12} reel1={maxes[0]} reel2={maxes[1]} reel3={maxes[2]}{marker}")

    # 3) MC 驗證
    mc = None
    if args.mc > 0:
        print(f"\n===== Monte Carlo 驗證（n={args.mc:,} spins, seed={args.seed}） =====")
        mc = mc_simulate(tuned_strips, n_spins=args.mc, seed=args.seed)
        print(f"MC total  RTP: {mc['rtp_total']*100:6.2f}%")
        print(f"MC base   RTP: {mc['rtp_base']*100:6.2f}%")
        print(f"MC bonus  RTP: {mc['rtp_bonus']*100:6.2f}%")
        for fs_id in FS_IDS:
            print(f"MC {fs_id} 觸發率: {mc['fs_trigger_rate'][fs_id]*100:.3f}%")

    # 4) 多台玩家模擬（bust rate + spins-to-bust 分佈）
    player_stats = None
    if args.players > 0:
        print(f"\n===== 玩家模擬（{args.players:,} 台，起始 {args.initial_balance}、下注 {args.bet}、"
              f"cap {args.max_spins} spin） =====")
        player_stats = simulate_players(
            tuned_strips,
            n_players=args.players,
            initial_balance=args.initial_balance,
            bet=args.bet,
            max_spins=args.max_spins,
            seed=args.seed + 1000,
        )
        s = player_stats
        print(f"破產玩家:      {s['bust_count']:>7,} / {s['n_players']:,}  ({s['bust_rate']*100:5.2f}%)")
        print(f"觸 cap 未破產: {s['hit_max_spin_cap']:>7,}  (代表玩家在 {args.max_spins} spin 內沒燒完籌碼)")
        print(f"lifetime RTP: {s['lifetime_rtp']*100:6.2f}%  (與 MC 對照)")
        print(f"\n破產 spin 數分佈（僅破產玩家）:")
        print(f"  平均            = {s['spins_to_bust_mean']:>8.1f}")
        print(f"  q10 / median / q90 = {s['spins_to_bust_q10']:>6.0f} / "
              f"{s['spins_to_bust_median']:>6.0f} / {s['spins_to_bust_q90']:>6.0f}")
        print(f"  q25 / q75          = {s['spins_to_bust_q25']:>6.0f} / {s['spins_to_bust_q75']:>6.0f}")
        print(f"\n期末結餘分佈（含破產者 =0）:")
        print(f"  平均      = {s['final_balance_mean']:>10.1f}")
        print(f"  q10       = {s['final_balance_q10']:>10.1f}")
        print(f"  median    = {s['final_balance_median']:>10.1f}")
        print(f"  q90       = {s['final_balance_q90']:>10.1f}")
        print(f"  top-1%    = {s['final_balance_top1pct']:>10.1f}")
        print(f"\n單次 spin 最大 win: {s['biggest_single_win']:,}  (bet={args.bet}，含 FS session)")

    # 5) 輸出結果 JSON（給 build_html 或人類 review 用）
    out = {
        'target_rtp': args.target,
        'tol': args.tol,
        'seed': args.seed,
        'reel_lengths': lengths,
        'constraints': {
            'WILD_MIN_PER_REEL': WILD_MIN_PER_REEL,
            'WILD_MAX_CONSECUTIVE': WILD_MAX_CONSECUTIVE,
            'REG_CLUSTER_SIZE_all_reg': REG_CLUSTER_SIZE,
            'max_reg_per_reel': args.max_reg,
        },
        'baseline_counts_per_reel': baseline_reels,
        'tuned_counts_per_reel': tuned_reels,
        'tuned_strips': tuned_strips,
        'hl_history': history,
        'final_rtp': analytic_rtp(tuned_strips),
        'mc_verification': mc,
        'player_simulation': player_stats,
    }
    out_path = 'tuned_strips.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n→ 已寫出 {out_path}")

if __name__ == '__main__':
    main()
