"""
Exact enumeration of 3-reel × 3-window RTP + variance + per-line-count 頻率。

Design:
  Outer  — 3M offset triples on physical strips 都是確定性，可精確枚舉
  Inner  — Mali FS session 是隨機的 (layout gen + 10 spins + mystery)，
           對每個 fs_mult 各跑一次 MC 得到 (mean, var) 常數，
           再用 Law of Total Variance 合起來：
             Var(X) = E_outcome[Var(X|outcome)] + Var_outcome(E[X|outcome])

Provides:
  - compute_bonus_moments(n_mc, seed) → {'FS1': (mean, var), ...}
  - exact_rtp_and_moments(strips) → {rtp, var, sigma, cv, p_zero, per_symbol, per_line_count, ...}
  - report_exact(result) → 人類可讀輸出

不動 rtp_sim.py（Karpathy Surgical Changes 原則）。
"""
from __future__ import annotations
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from rtp_sim import (
    SYM, SYMBOLS, REG_IDS, FS_IDS, WILD_ID, ALL_IDS,
    MALI_PRIZES, MYSTERY_PRIZES, E_MALI_VAL,
    counts_of, analytic_rtp,
)


# ==================== Bonus (Mali) MC 常數 ====================

def _one_mali_session(mult: int, rng: random.Random) -> int:
    """一次完整 FS session 的 payoff (bet=100)：10 spins × mult × cell value。"""
    layout: List = [100, 150, 'M'] + [rng.choice(MALI_PRIZES) for _ in range(13)]
    rng.shuffle(layout)
    total = 0
    for _ in range(10):  # fs_spins = 10 (all FS 一致)
        cell = layout[rng.randrange(16)]
        prize = rng.choice(MYSTERY_PRIZES) if cell == 'M' else cell
        total += prize * mult
    return total


def compute_bonus_moments(n_mc: int = 500_000, seed: int = 42) -> Dict[str, Tuple[float, float]]:
    """對每種 FS mult 跑 MC，回傳 {fs_id: (mean_bonus, var_bonus)}，皆為 bet=100 base。

    n_mc=500k 對 mean 的 SE ≈ σ/√N ≈ 0.5，對 var 的 SE 較大但夠用。
    """
    rng = random.Random(seed)
    stats: Dict[str, Tuple[float, float]] = {}
    for fs_id in FS_IDS:
        mult = SYM[fs_id].fs_mult
        # Welford one-pass
        n = 0
        mean = 0.0
        M2 = 0.0
        for _ in range(n_mc):
            x = _one_mali_session(mult, rng)
            n += 1
            delta = x - mean
            mean += delta / n
            M2 += delta * (x - mean)
        var = M2 / n
        stats[fs_id] = (mean, var)
    return stats


# ==================== Exact enumeration ====================

def _precompute_window_stats(strip: List[str]) -> List[Dict]:
    """對每個 offset 計算 3-window 的 per-symbol count（含 Wild 通配版）。
    回傳長度 L 的 list，每 entry: dict with 'reg_match', 'fs_match', 'wild_only'。
    """
    L = len(strip)
    out = []
    for off in range(L):
        w = [strip[(off + i) % L] for i in range(3)]
        wild_cnt = sum(1 for s in w if s == WILD_ID)
        reg_match = {rid: sum(1 for s in w if s == rid or s == WILD_ID) for rid in REG_IDS}
        fs_match = {fid: sum(1 for s in w if s == fid) for fid in FS_IDS}
        out.append({
            'reg_match': reg_match,   # 含 wild 通配
            'fs_match': fs_match,
            'wild_only': wild_cnt,    # 純 wild count (for wild-jackpot)
        })
    return out


def exact_rtp_and_moments(
    strips: List[List[str]],
    bonus_stats: Optional[Dict[str, Tuple[float, float]]] = None,
    bet: int = 100,
) -> Dict:
    """對 L1×L2×L3 offset triple 枚舉，回傳精確 RTP + 全動差 + per-line-count 分佈。

    採 Law of Total Variance 處理 FS bonus 隨機性：
      對每個 outcome，X = base_win + I{FS_i} · bonus_i
      base_win 確定；bonus_i 是條件隨機變數 (mean=μ_i, var=σ²_i from MC)
      E[X | outcome] = base_win + I · μ_i
      Var[X | outcome] = I · σ²_i     (base_win 已定)
    合起來：
      E[X²] = mean over outcomes of (E[X|outcome]² + Var[X|outcome])
      Var[X] = E[X²] - E[X]²
    """
    if bonus_stats is None:
        bonus_stats = compute_bonus_moments()

    L = [len(s) for s in strips]
    N = L[0] * L[1] * L[2]  # 3,042,000 for default lengths

    stats_per_reel = [_precompute_window_stats(s) for s in strips]

    # accumulators
    sum_x = 0.0        # E[X | outcome] 加總
    sum_x2 = 0.0       # E[X²] outer term = E[X|outcome]² 加總
    sum_var_x = 0.0    # E[Var[X|outcome]] 加總（來自 bonus randomness）
    n_zero = 0         # count of outcomes with X = 0 (deterministic zero,
                       # 不含 FS 觸發的 outcome — 那些有隨機 bonus 不會為 0)

    # per-symbol contribution: 用 E[X|outcome] 累加
    per_sym_contrib_sum: Dict[str, float] = defaultdict(float)
    # per-symbol per-line-count 頻率
    per_sym_line_count: Dict[str, Dict[int, int]] = {sid: defaultdict(int) for sid in REG_IDS + [WILD_ID]}
    # FS 觸發次數
    fs_trigger_count: Dict[str, int] = {fid: 0 for fid in FS_IDS}

    payout_by_sym = {sid: SYM[sid].payout for sid in REG_IDS + [WILD_ID]}

    for o0 in range(L[0]):
        w0 = stats_per_reel[0][o0]
        r0 = w0['reg_match']
        f0 = w0['fs_match']
        wo0 = w0['wild_only']
        for o1 in range(L[1]):
            w1 = stats_per_reel[1][o1]
            r1 = w1['reg_match']
            f1 = w1['fs_match']
            wo1 = w1['wild_only']
            for o2 in range(L[2]):
                w2 = stats_per_reel[2][o2]
                r2 = w2['reg_match']
                f2 = w2['fs_match']
                wo2 = w2['wild_only']

                # ---- base win（deterministic）----
                base_win = 0

                # Wild jackpot line (純 Wild 三格)
                if wo0 and wo1 and wo2:
                    lines_w = wo0 * wo1 * wo2
                    base_win += lines_w * payout_by_sym[WILD_ID]
                    per_sym_contrib_sum[WILD_ID] += lines_w * payout_by_sym[WILD_ID]
                    per_sym_line_count[WILD_ID][lines_w] += 1
                else:
                    per_sym_line_count[WILD_ID][0] += 1

                for rid in REG_IDS:
                    m0, m1, m2 = r0[rid], r1[rid], r2[rid]
                    if m0 and m1 and m2:
                        lines = m0 * m1 * m2
                        pay = lines * payout_by_sym[rid]
                        base_win += pay
                        per_sym_contrib_sum[rid] += pay
                        per_sym_line_count[rid][lines] += 1
                    else:
                        per_sym_line_count[rid][0] += 1

                # ---- FS 優先權觸發 ----
                fs_hit: Optional[str] = None
                for fid in FS_IDS:
                    if f0[fid] and f1[fid] and f2[fid]:
                        fs_hit = fid
                        break

                # 條件期望與條件變異
                if fs_hit is None:
                    ex = float(base_win)
                    varx = 0.0
                    if base_win == 0:
                        n_zero += 1
                else:
                    fs_trigger_count[fs_hit] += 1
                    mu_b, var_b = bonus_stats[fs_hit]
                    ex = base_win + mu_b
                    varx = var_b
                    # 注意：FS 觸發的 outcome 不算 zero-payoff（bonus>0 幾乎必然）

                sum_x += ex
                sum_x2 += ex * ex
                sum_var_x += varx

    # ---- 動差 ----
    e_x = sum_x / N
    e_x2 = (sum_x2 + sum_var_x) / N
    var_x = e_x2 - e_x * e_x
    sigma = var_x ** 0.5

    rtp_total = e_x / bet
    cv = sigma / e_x if e_x > 0 else float('nan')
    vol_idx = sigma / bet

    # 拆 base / bonus
    base_only_sum = sum_x - sum(fs_trigger_count[fid] * bonus_stats[fid][0] for fid in FS_IDS)
    rtp_base = base_only_sum / N / bet
    rtp_bonus = rtp_total - rtp_base

    # per-symbol RTP 貢獻
    per_symbol_rtp = {sid: v / N / bet for sid, v in per_sym_contrib_sum.items()}

    # per-symbol per-line-count 頻率
    per_symbol_line_freq = {
        sid: {k: cnt / N for k, cnt in sorted(per_sym_line_count[sid].items())}
        for sid in per_sym_line_count
    }

    fs_trigger_rate = {fid: fs_trigger_count[fid] / N for fid in FS_IDS}

    return {
        'n_outcomes': N,
        'rtp_total': rtp_total,
        'rtp_base': rtp_base,
        'rtp_bonus': rtp_bonus,
        'e_x': e_x,           # E[X] at bet=100
        'var_x': var_x,
        'sigma': sigma,
        'cv': cv,
        'vol_idx': vol_idx,   # σ/bet
        'p_zero_deterministic': n_zero / N,
        'per_symbol_rtp': per_symbol_rtp,
        'per_symbol_line_freq': per_symbol_line_freq,
        'fs_trigger_rate': fs_trigger_rate,
        'bonus_stats': bonus_stats,
    }


# ==================== Reporting ====================

def report_exact(result: Dict, focus_symbol: Optional[str] = 'S9') -> None:
    r = result
    print(f"\n===== Exact Enumeration ({r['n_outcomes']:,} outcomes) =====")
    print(f"Total RTP    : {r['rtp_total']*100:7.4f}%")
    print(f"  Base RTP   : {r['rtp_base']*100:7.4f}%")
    print(f"  Bonus RTP  : {r['rtp_bonus']*100:7.4f}%")
    print(f"E[X]         : {r['e_x']:8.4f}   (bet=100)")
    print(f"Var[X]       : {r['var_x']:10.2f}")
    print(f"σ (sd)       : {r['sigma']:8.4f}")
    print(f"CV (σ/E)     : {r['cv']:8.4f}")
    print(f"Vol Idx (σ/bet): {r['vol_idx']:6.4f}")
    print(f"P(X=0)       : {r['p_zero_deterministic']*100:7.4f}%")

    print(f"\nFS 觸發率:")
    for fid in FS_IDS:
        print(f"  {SYM[fid].char} {SYM[fid].name:<12} {r['fs_trigger_rate'][fid]*100:7.4f}%  "
              f"E[bonus]={r['bonus_stats'][fid][0]:7.2f}  σ_bonus={r['bonus_stats'][fid][1]**0.5:7.2f}")

    print(f"\nPer-symbol RTP 貢獻（由高至低）:")
    for sid, v in sorted(r['per_symbol_rtp'].items(), key=lambda kv: -kv[1]):
        s = SYM[sid]
        print(f"  {s.char} {s.name:<12} payout={s.payout:>3}  {v*100:7.4f}%")

    if focus_symbol and focus_symbol in r['per_symbol_line_freq']:
        s = SYM[focus_symbol]
        freq = r['per_symbol_line_freq'][focus_symbol]
        payout = s.payout
        print(f"\n{s.char} {s.name} per-line-count 精確頻率:")
        print(f"{'k':>4} {'P(lines=k)':>14} {'contrib RTP':>14} {'占 sym total':>14}")
        print('-' * 60)
        total_contrib = r['per_symbol_rtp'][focus_symbol]
        for k in sorted(freq.keys()):
            p = freq[k]
            contrib = k * p * payout / 100
            share = (contrib / total_contrib * 100) if total_contrib > 0 and k > 0 else 0
            marker = ' ⭐' if k > 0 and contrib == max(kk * freq[kk] * payout / 100 for kk in freq if kk > 0) else ''
            print(f"{k:>4} {p*100:>13.6f}% {contrib*100:>13.6f}% {share:>12.2f}%{marker}")


if __name__ == '__main__':
    import argparse, json, re, time

    ap = argparse.ArgumentParser()
    ap.add_argument('--source', default='html', choices=['html', 'json'],
                    help='html: 從 pachislot_mali.html 抓 REEL_STRIPS；json: 從 tuned_strips.json 讀')
    ap.add_argument('--bonus-mc', type=int, default=500_000)
    ap.add_argument('--bonus-seed', type=int, default=42)
    ap.add_argument('--focus', default='S9', help='per-line-count 詳表要看哪個符號')
    args = ap.parse_args()

    if args.source == 'html':
        html = open('pachislot_mali.html', encoding='utf-8').read()
        m = re.search(r'const REEL_STRIPS = \[(.*?)\n\];', html, re.S)
        rows = re.findall(r"\[([^\]]+)\]", m.group(1))
        strips = [[x.strip().strip("'") for x in row.split(',') if x.strip()] for row in rows]
    else:
        data = json.load(open('tuned_strips.json', encoding='utf-8'))
        strips = data['tuned_strips']

    print(f"Reels: L = {[len(s) for s in strips]}, product = {len(strips[0])*len(strips[1])*len(strips[2]):,}")

    t0 = time.time()
    print(f"\n[1/2] Compute bonus (Mali) moments via MC (n={args.bonus_mc:,})...")
    bonus_stats = compute_bonus_moments(n_mc=args.bonus_mc, seed=args.bonus_seed)
    t1 = time.time()
    print(f"      done in {t1-t0:.2f}s")
    for fid, (mu, var) in bonus_stats.items():
        print(f"      {fid}: mean={mu:.3f}  sd={var**0.5:.3f}")

    print(f"\n[2/2] Exact enumeration...")
    result = exact_rtp_and_moments(strips, bonus_stats=bonus_stats)
    t2 = time.time()
    print(f"      done in {t2-t1:.2f}s")

    report_exact(result, focus_symbol=args.focus)

    # 對照 analytic
    print(f"\n===== 對照 analytic_rtp（獨立近似）=====")
    a = analytic_rtp(strips)
    print(f"Analytic Total RTP : {a['total_rtp']*100:7.4f}%   vs Exact {result['rtp_total']*100:7.4f}%   "
          f"Δ={( result['rtp_total']-a['total_rtp'])*100:+.4f}pp")
    print(f"Analytic Base  RTP : {a['base_rtp']*100:7.4f}%   vs Exact {result['rtp_base']*100:7.4f}%   "
          f"Δ={( result['rtp_base']-a['base_rtp'])*100:+.4f}pp")
    print(f"Analytic Bonus RTP : {a['bonus_rtp']*100:7.4f}%   vs Exact {result['rtp_bonus']*100:7.4f}%   "
          f"Δ={( result['rtp_bonus']-a['bonus_rtp'])*100:+.4f}pp")
    if args.focus in a['per_symbol_contrib']:
        print(f"Analytic {args.focus} 貢獻    : {a['per_symbol_contrib'][args.focus]*100:7.4f}%   "
              f"vs Exact {result['per_symbol_rtp'][args.focus]*100:7.4f}%   "
              f"Δ={(result['per_symbol_rtp'][args.focus]-a['per_symbol_contrib'][args.focus])*100:+.4f}pp")
