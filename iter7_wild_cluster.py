"""
iter7: iter6 基礎上加 Wild cluster prefix → Wild 27 線可觸發

相對 iter6 的改動:
  - Wild payout 200 → 220
  - prefix layout: [S0]*3 [S1]*3 ... [S9]*3 [WILD]*3  (30 → 33 slots)
  - 三輪同停 offset 30 → 觸發 Wild 3-3-3 → 27 線大獎
  - Wild 27 線機率 = 3/L1 × 3/L2 × 3/L3 = 27/(L1·L2·L3) ≈ 8.87e-6

其餘設計沿用 iter6:
  - 撤 wild max cluster limit
  - HL target 93.5%, tol ±0.8pp
  - counts 保留 iter5 base（reg cluster + wild min 3 + fs min 1）

不動 rtp_sim.py（monkey-patch approach）。
"""
from __future__ import annotations
import json
import random
import time
from typing import Dict, List

import rtp_sim
from rtp_sim import (
    SYM, ALL_IDS, REG_IDS, FS_IDS, WILD_ID,
    REEL_LENGTHS, WILD_MIN_PER_REEL, REG_CLUSTER_SIZE, FS_MIN_GAP,
    initial_counts_from_html_weights,
    hl_calibrate, analytic_rtp, mc_simulate, simulate_players,
    counts_of, fmt_counts,
    _fs_gap_violated,
)
from exact_moments import (
    exact_rtp_and_moments, compute_bonus_moments, report_exact,
)

# ==================== iter7 design ====================
NEW_WILD_PAYOUT = 220
WILD_CLUSTER_SIZE = 3
TARGET_RTP = 0.935
TOL = 0.008
LENGTHS = list(REEL_LENGTHS)
HL_SEED = 20260722
MAX_REG_PER_REEL = 40

# 1) Wild payout 220
SYM['WILD'].payout = NEW_WILD_PAYOUT

# 2) 撤 wild max cluster limit
rtp_sim._has_wild_run = lambda strip, max_ok: False


# 3) 新 strip builder：加 wild cluster prefix
def make_strip_v5(
    counts: Dict[str, int],
    seed: int,
    length: int,
    reg_cluster_size: int = REG_CLUSTER_SIZE,
    wild_cluster_size: int = WILD_CLUSTER_SIZE,
    max_retries: int = 500,
) -> List[str]:
    """iter7 strip builder：prefix 包含所有 reg cluster + wild cluster

      prefix = [S0]*3 [S1]*3 ... [S9]*3 [WILD]*3  (33 slots for size=3)
      三輪停 offset 30 → windows = [WILD,WILD,WILD]×3 → Wild 27 線大獎
      offset i·3 for i=0..9 → 對應 reg cluster i 的 27 線
    """
    for rid in REG_IDS:
        assert counts.get(rid, 0) >= reg_cluster_size, \
            f"iter7 需要每個 reg ≥ {reg_cluster_size}，{rid}={counts.get(rid, 0)}"
    assert counts.get(WILD_ID, 0) >= wild_cluster_size, \
        f"iter7 需要 WILD ≥ {wild_cluster_size}，實際={counts.get(WILD_ID, 0)}"
    assert sum(counts.values()) == length, \
        f"counts must sum to {length}, got {sum(counts.values())}"

    # Build prefix: 每個 reg 3 連 + wild 3 連
    prefix: List[str] = []
    for rid in REG_IDS:
        prefix.extend([rid] * reg_cluster_size)
    prefix.extend([WILD_ID] * wild_cluster_size)
    prefix_len = len(prefix)  # 30 + 3 = 33

    # Remaining pool
    remaining = dict(counts)
    for rid in REG_IDS:
        remaining[rid] -= reg_cluster_size
    remaining[WILD_ID] -= wild_cluster_size

    others: List[str] = []
    for sid, c in remaining.items():
        if c > 0:
            others.extend([sid] * c)
    assert len(others) == length - prefix_len, \
        f"pool size {len(others)} != {length - prefix_len}"

    # Retry until FS gap constraint 滿足（wild 已撤限）
    for retry in range(max_retries):
        rng = random.Random(seed + retry * 10007)
        shuffled = list(others)
        rng.shuffle(shuffled)
        strip = prefix + shuffled
        if _fs_gap_violated(strip, FS_MIN_GAP):
            continue
        return strip
    raise RuntimeError(
        f"make_strip_v5: {max_retries} retry 內無法滿足 FS min gap {FS_MIN_GAP}"
    )


def build_seed_counts():
    """iter7 seed：wild ≥ WILD_CLUSTER_SIZE + 每 reg ≥ REG_CLUSTER_SIZE"""
    baseline_reels = [initial_counts_from_html_weights(L) for L in LENGTHS]
    seed_counts = []
    for c in baseline_reels:
        cc = dict(c)

        def _need_map():
            m = {'WILD': max(0, WILD_CLUSTER_SIZE - cc.get('WILD', 0))}
            for rid in REG_IDS:
                m[rid] = max(0, REG_CLUSTER_SIZE - cc.get(rid, 0))
            return m

        needs = _need_map()
        while sum(needs.values()) > 0:
            reg_by_count = sorted(
                [(sid, cc.get(sid, 0)) for sid in REG_IDS if cc.get(sid, 0) > REG_CLUSTER_SIZE],
                key=lambda kv: -kv[1],
            )
            if not reg_by_count:
                raise RuntimeError(f"insufficient reg pool: cc={cc}, needs={needs}")
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
    return baseline_reels, seed_counts


def verify_wild_cluster(strip: List[str]) -> bool:
    """驗證 strip 前 33 slot 是 [S0]*3 ... [S9]*3 [WILD]*3。"""
    for i, rid in enumerate(REG_IDS):
        start = i * REG_CLUSTER_SIZE
        if not all(strip[start + k] == rid for k in range(REG_CLUSTER_SIZE)):
            return False
    wild_start = len(REG_IDS) * REG_CLUSTER_SIZE  # = 30
    for k in range(WILD_CLUSTER_SIZE):
        if strip[wild_start + k] != WILD_ID:
            return False
    return True


def main():
    print(f"===== iter7 設計 =====")
    print(f"Wild payout      : 200 → {NEW_WILD_PAYOUT}")
    print(f"Prefix layout    : [S0..S9]*3 [WILD]*3  (33 slot)")
    print(f"Wild 27 線 offset: 三輪同停 offset=30")
    print(f"Wild 27 線機率   : 3/L1×3/L2×3/L3 = 27/{LENGTHS[0]*LENGTHS[1]*LENGTHS[2]:,} = {27/(LENGTHS[0]*LENGTHS[1]*LENGTHS[2])*100:.6f}%")

    baseline_reels, seed_counts = build_seed_counts()

    print(f"\n===== HL Loop (target {TARGET_RTP*100:.1f}%, tol ±{TOL*100:.1f}pp) =====\n")
    tuned_reels, history = hl_calibrate(
        seed_counts, LENGTHS,
        target=TARGET_RTP, tol=TOL,
        min_wild_per_reel=WILD_CLUSTER_SIZE,  # 用 WILD_CLUSTER_SIZE 確保 v5 builder 能建
        min_fs_per_reel=1,
        max_reg_per_reel=MAX_REG_PER_REEL,
        min_all_reg_per_reel=REG_CLUSTER_SIZE,
        max_iter=300, verbose=True,
    )

    # 用 v5 builder（含 Wild cluster）
    tuned_strips = [
        make_strip_v5(c, seed=HL_SEED + 100 + i, length=LENGTHS[i])
        for i, c in enumerate(tuned_reels)
    ]

    # 驗證 wild cluster 就位
    print(f"\n===== iter7 strip 驗證 =====")
    for i, s in enumerate(tuned_strips):
        ok = verify_wild_cluster(s)
        print(f"reel {i} (L={len(s)}): prefix layout {'✅' if ok else '❌'}  "
              f"[30:33]={''.join(SYM[s[j]].char for j in range(30, 33))}")

    print(f"\n===== TUNED counts =====")
    for i, s in enumerate(tuned_strips):
        print(f"reel {i} (L={len(s)}): {fmt_counts(counts_of(s))}")

    a = analytic_rtp(tuned_strips)
    print(f"\nAnalytic Total RTP: {a['total_rtp']*100:.4f}%")

    # ===== exact + variance =====
    print(f"\n===== Bonus MC (500k) =====")
    t0 = time.time()
    bonus_stats = compute_bonus_moments(n_mc=500_000, seed=42)
    print(f"done in {time.time()-t0:.1f}s")

    print(f"\n===== Exact Enumeration =====")
    t0 = time.time()
    exact_r = exact_rtp_and_moments(tuned_strips, bonus_stats=bonus_stats)
    print(f"done in {time.time()-t0:.1f}s")
    report_exact(exact_r, focus_symbol='WILD')

    # 驗證 P(Wild lines=27)
    wild_freq = exact_r['per_symbol_line_freq']['WILD']
    p_27 = wild_freq.get(27, 0)
    expected = 3 * 3 * 3 / (LENGTHS[0] * LENGTHS[1] * LENGTHS[2])
    print(f"\n===== Wild 27 線頻率驗證 =====")
    print(f"實測 P(Wild lines=27) = {p_27*100:.8f}%")
    print(f"預期 27/{LENGTHS[0]*LENGTHS[1]*LENGTHS[2]:,} = {expected*100:.8f}%")
    print(f"比值 = {p_27/expected if expected > 0 else 'inf':.4f} ({'✅ 精確' if abs(p_27/expected - 1) < 0.01 else '⚠️ 有額外命中（shuffle 部分也有 wild 3 連）'})")

    # ===== player sim =====
    print(f"\n===== Player Simulation (100K players, 10000 起始, 100 下注, cap 30000 spin) =====")
    t0 = time.time()
    p = simulate_players(
        tuned_strips,
        n_players=100_000,
        initial_balance=10_000,
        bet=100,
        max_spins=30_000,
        seed=HL_SEED + 1000,
    )
    print(f"done in {time.time()-t0:.1f}s\n")

    print(f"破產玩家       : {p['bust_count']:>7,} / {p['n_players']:,}  ({p['bust_rate']*100:5.2f}%)")
    print(f"觸 cap 未破產  : {p['hit_max_spin_cap']:>7,}")
    print(f"lifetime RTP   : {p['lifetime_rtp']*100:6.3f}%  (exact {exact_r['rtp_total']*100:.3f}% 對照)")
    print(f"\n破產 spin 數分佈（僅破產玩家）:")
    print(f"  平均       = {p['spins_to_bust_mean']:>10.1f} spin")
    print(f"  median     = {p['spins_to_bust_median']:>10.0f}")
    print(f"  q10 / q90  = {p['spins_to_bust_q10']:>6.0f} / {p['spins_to_bust_q90']:>.0f}")
    print(f"  q25 / q75  = {p['spins_to_bust_q25']:>6.0f} / {p['spins_to_bust_q75']:>.0f}")
    print(f"\n單次 spin 最大 win: {p['biggest_single_win']:,}  (bet=100，含 FS session)")

    # 儲存
    out = {
        'design': {
            'wild_payout': NEW_WILD_PAYOUT,
            'wild_cluster_size': WILD_CLUSTER_SIZE,
            'prefix_layout': '[S0..S9]*3 [WILD]*3 (33 slot)',
            'target_rtp': TARGET_RTP,
            'tol': TOL,
            'reel_lengths': LENGTHS,
        },
        'tuned_counts_per_reel': tuned_reels,
        'tuned_strips': tuned_strips,
        'hl_history': history,
        'analytic_rtp': a,
        'exact_summary': {k: v for k, v in exact_r.items() if k != 'per_symbol_line_freq'},
        'exact_WILD_line_freq': wild_freq,
        'exact_S9_line_freq': exact_r['per_symbol_line_freq'].get('S9', {}),
        'wild_27_line_prob': p_27,
        'wild_27_line_prob_theoretical': expected,
        'player_simulation': p,
    }
    with open('tuned_strips_iter7.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n→ 已寫出 tuned_strips_iter7.json")


if __name__ == '__main__':
    main()
