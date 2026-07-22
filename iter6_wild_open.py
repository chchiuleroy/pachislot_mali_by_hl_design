"""
iter6: 撤掉 Wild max cluster 限制 + 給 Wild 3-line payout=200 + HL 校準到 93.5%

設計改動（相對 iter5）:
  1. 撤 WILD_MAX_CONSECUTIVE：Wild 可 3 連 → 可觸發 Wild 27 線
  2. SYM['WILD'].payout: 0 → 200（Wild 3-line 額外獎金 on top of reg 通配）
  3. HL target: 96% → 93.5%（區間 92-95%，tol=±0.8pp）

用 monkey-patch 不動 rtp_sim.py 原始檔（Surgical Changes）。
"""
from __future__ import annotations
import json
import time

import rtp_sim
from rtp_sim import (
    SYM, ALL_IDS, REG_IDS, FS_IDS, WILD_ID,
    REEL_LENGTHS, WILD_MIN_PER_REEL, REG_CLUSTER_SIZE,
    make_strip_v4, initial_counts_from_html_weights,
    hl_calibrate, analytic_rtp, mc_simulate, simulate_players,
    counts_of, fmt_counts,
)
from exact_moments import (
    exact_rtp_and_moments, compute_bonus_moments, report_exact,
)

# ==================== iter6 design overrides ====================

NEW_WILD_PAYOUT = 200
TARGET_RTP = 0.935
TOL = 0.008         # 92.7% ~ 94.3% 收斂窗
LENGTHS = list(REEL_LENGTHS)
HL_SEED = 20260722
MAX_REG_PER_REEL = 40  # 每輪任一非-Wild 符號上限（避免視覺失衡）

# 1) 給 Wild payout
SYM['WILD'].payout = NEW_WILD_PAYOUT

# 2) 撤 Wild max cluster 限制：monkey-patch _has_wild_run 永遠回 False
rtp_sim._has_wild_run = lambda strip, max_ok: False


def build_seed_counts():
    """從 HTML weights 縮放到 LENGTHS，補到滿足 iter4 constraints：
    每輪 WILD ≥ WILD_MIN_PER_REEL 且每個 reg ≥ REG_CLUSTER_SIZE。"""
    baseline_reels = [initial_counts_from_html_weights(L) for L in LENGTHS]
    seed_counts = []
    for c in baseline_reels:
        cc = dict(c)

        def _need_map():
            m = {'WILD': max(0, WILD_MIN_PER_REEL - cc.get('WILD', 0))}
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


def main():
    print(f"===== iter6 設計 =====")
    print(f"Wild payout      : 0 → {NEW_WILD_PAYOUT}")
    print(f"Wild max cluster : 2 → ∞ (撤限制)")
    print(f"HL target        : 96.0% → {TARGET_RTP*100:.1f}%  tol=±{TOL*100:.1f}pp  (窗 {(TARGET_RTP-TOL)*100:.1f}~{(TARGET_RTP+TOL)*100:.1f}%)")
    print(f"Reel lengths     : {LENGTHS}")

    baseline_reels, seed_counts = build_seed_counts()

    # 觀察 baseline 在新 payout 下的 RTP（不改 counts，只換 payout）
    baseline_strips = [
        rtp_sim.make_strip(baseline_reels[i], seed=HL_SEED + i, length=LENGTHS[i])
        for i in range(3)
    ]
    a_base = analytic_rtp(baseline_strips)
    print(f"\n[baseline in new payout] Total RTP = {a_base['total_rtp']*100:.4f}%  base={a_base['base_rtp']*100:.4f}%  bonus={a_base['bonus_rtp']*100:.4f}%")

    # HL loop
    print(f"\n===== HL Loop (target {TARGET_RTP*100:.1f}%, tol ±{TOL*100:.1f}pp) =====\n")
    tuned_reels, history = hl_calibrate(
        seed_counts, LENGTHS,
        target=TARGET_RTP, tol=TOL,
        min_wild_per_reel=WILD_MIN_PER_REEL,
        min_fs_per_reel=1,
        max_reg_per_reel=MAX_REG_PER_REEL,
        min_all_reg_per_reel=REG_CLUSTER_SIZE,
        max_iter=300, verbose=True,
    )
    tuned_strips = [
        make_strip_v4(c, seed=HL_SEED + 100 + i, length=LENGTHS[i])
        for i, c in enumerate(tuned_reels)
    ]

    print(f"\n===== TUNED counts =====")
    for i, s in enumerate(tuned_strips):
        print(f"reel {i} (L={len(s)}): {fmt_counts(counts_of(s))}")

    a = analytic_rtp(tuned_strips)
    print(f"\nAnalytic Total RTP: {a['total_rtp']*100:.4f}%")
    print(f"        Base  RTP: {a['base_rtp']*100:.4f}%")
    print(f"        Bonus RTP: {a['bonus_rtp']*100:.4f}%")

    # ===== exact enumeration + variance =====
    print(f"\n===== Bonus MC (500k) =====")
    t0 = time.time()
    bonus_stats = compute_bonus_moments(n_mc=500_000, seed=42)
    print(f"done in {time.time()-t0:.1f}s")

    print(f"\n===== Exact Enumeration =====")
    t0 = time.time()
    exact_r = exact_rtp_and_moments(tuned_strips, bonus_stats=bonus_stats)
    print(f"done in {time.time()-t0:.1f}s")
    report_exact(exact_r, focus_symbol='WILD')

    # ===== player simulation =====
    print(f"\n===== Player Simulation (100K players, 10000 起始, 100 下注, cap 20000 spin) =====")
    t0 = time.time()
    p = simulate_players(
        tuned_strips,
        n_players=100_000,
        initial_balance=10_000,
        bet=100,
        max_spins=20_000,
        seed=HL_SEED + 1000,
    )
    print(f"done in {time.time()-t0:.1f}s\n")

    print(f"破產玩家       : {p['bust_count']:>7,} / {p['n_players']:,}  ({p['bust_rate']*100:5.2f}%)")
    print(f"觸 cap 未破產  : {p['hit_max_spin_cap']:>7,}  (代表玩家在 {20_000} spin 內沒燒完)")
    print(f"lifetime RTP   : {p['lifetime_rtp']*100:6.3f}%  (與 exact {exact_r['rtp_total']*100:.3f}% 對照)")
    print(f"\n破產 spin 數分佈（僅破產玩家）:")
    print(f"  平均       = {p['spins_to_bust_mean']:>10.1f} spin")
    print(f"  median     = {p['spins_to_bust_median']:>10.0f}")
    print(f"  q10 / q90  = {p['spins_to_bust_q10']:>6.0f} / {p['spins_to_bust_q90']:>.0f}")
    print(f"  q25 / q75  = {p['spins_to_bust_q25']:>6.0f} / {p['spins_to_bust_q75']:>.0f}")
    print(f"\n期末結餘分佈（含破產者=0）:")
    print(f"  平均       = {p['final_balance_mean']:>10.1f}")
    print(f"  median     = {p['final_balance_median']:>10.1f}")
    print(f"  q90        = {p['final_balance_q90']:>10.1f}")
    print(f"  top-1%     = {p['final_balance_top1pct']:>10.1f}")
    print(f"\n單次 spin 最大 win: {p['biggest_single_win']:,}  (bet=100，含 FS session)")

    # 儲存
    out = {
        'design': {
            'wild_payout': NEW_WILD_PAYOUT,
            'wild_max_cluster': 'unlimited',
            'target_rtp': TARGET_RTP,
            'tol': TOL,
            'reel_lengths': LENGTHS,
        },
        'tuned_counts_per_reel': tuned_reels,
        'tuned_strips': tuned_strips,
        'hl_history': history,
        'analytic_rtp': a,
        'exact_rtp_and_moments': {
            k: v for k, v in exact_r.items()
            if k not in ('per_symbol_line_freq',)  # 太大略去 json 檔
        },
        'exact_S9_line_freq': exact_r['per_symbol_line_freq'].get('S9', {}),
        'exact_WILD_line_freq': exact_r['per_symbol_line_freq'].get('WILD', {}),
        'player_simulation': p,
    }
    with open('tuned_strips_iter6.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n→ 已寫出 tuned_strips_iter6.json")


if __name__ == '__main__':
    main()
