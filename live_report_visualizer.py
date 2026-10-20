"""
Live Session Econometric & Behavioral Data Visualizer.
Generates real-time, publication-quality visualizations specifically from
the current active oTree session's recorded participant decisions and surveys.
"""

import io
import base64
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Clean, professional styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"


def generate_live_session_visualizations(session, players) -> Dict[str, Any]:
    """
    Extracts decisions and survey variables from the current session's players,
    and returns base64-encoded visual plots reflecting THIS session's empirical results.
    """
    session_code = session.code if session else "Live Session"
    
    # 1. Collect choice-level records
    records = []
    participant_meta = {}
    
    for p in players:
        part = p.participant
        p_code = part.code
        treatment = getattr(part, 'treatment', 'A') or 'A'
        is_bot = bool(getattr(part, 'is_bot', False) or getattr(part, '_is_bot', False))
        
        if p_code not in participant_meta:
            demo = part.vars.get('demographics', {})
            traits = part.vars.get('traits', {})
            post = part.vars.get('post_task', {})
            participant_meta[p_code] = {
                'treatment': treatment,
                'is_bot': is_bot,
                'car_ownership': demo.get('car_ownership', ''),
                'usual_commute_distance': demo.get('usual_commute_distance', np.nan),
                'nep_score': traits.get('nep_score', np.nan),
                'patience_index': traits.get('patience_index', np.nan),
                'risk_general': traits.get('risk_general', np.nan),
                'support_carbon_tax': post.get('support_carbon_tax', np.nan),
                'support_mobility_bonus': post.get('support_mobility_bonus', np.nan),
                'perceived_coerciveness': post.get('perceived_coerciveness', np.nan),
            }
            
        for r_p in p.in_all_rounds():
            if r_p.choice:
                records.append({
                    'participant_code': p_code,
                    'treatment': treatment,
                    'is_bot': is_bot,
                    'round_number': r_p.round_number,
                    'scenario_id': r_p.scenario_id or r_p.round_number,
                    'choice': r_p.choice,
                    'choice_car': 1 if r_p.choice == 'car' else 0,
                    'choice_transit': 1 if r_p.choice == 'transit' else 0,
                    'choice_active': 1 if r_p.choice == 'active' else 0,
                    'rt_ms': r_p.rt_ms or 0
                })
                
    has_data = len(records) > 0
    total_choices = len(records)
    n_participants = len(set(r['participant_code'] for r in records))
    
    if not has_data:
        return {
            'has_data': False,
            'total_choices': 0,
            'n_participants': 0,
            'figures': {}
        }
        
    df = pd.DataFrame(records)
    df_part = pd.DataFrame.from_dict(participant_meta, orient='index').reset_index()
    
    figures = {}
    
    # -------------------------------------------------------------
    # Figure 1: Live Mode Share by Policy Treatment
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 3.8))
    treatments = ['A', 'B', 'C']
    treatment_labels = [
        'A: Control\n(Baseline)',
        'B: Carbon Tax\n(+€30 on Car)',
        'C: Clean Voucher\n(−€30 on Transit)'
    ]
    
    modes = ['car', 'transit', 'active']
    mode_labels = ['Private Car', 'Public Transit', 'Active Mobility']
    mode_colors = ['#ef4444', '#10b981', '#3b82f6']
    
    bar_width = 0.25
    x_indices = np.arange(len(treatments))
    
    for i, (m, label, color) in enumerate(zip(modes, mode_labels, mode_colors)):
        pcts = []
        counts = []
        for t in treatments:
            df_t = df[df['treatment'] == t]
            if len(df_t) > 0:
                pct = (df_t[f'choice_{m}'].sum() / len(df_t)) * 100
                cnt = df_t[f'choice_{m}'].sum()
            else:
                pct = 0.0
                cnt = 0
            pcts.append(pct)
            counts.append(cnt)
            
        pos = x_indices + (i - 1) * bar_width
        bars = ax.bar(pos, pcts, width=bar_width, label=label, color=color, alpha=0.9, edgecolor='white')
        
        # Annotate percentages on top of bars
        for bar, pct, cnt in zip(bars, pcts, counts):
            if pct > 0:
                ax.annotate(f"{pct:.1f}%\n({cnt})",
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, fontweight='bold', color='#1e293b')
                            
    ax.set_xticks(x_indices)
    ax.set_xticklabels(treatment_labels, fontweight='bold')
    ax.set_ylabel('Mode Share (%)', fontweight='bold')
    ax.set_ylim(0, 115)
    ax.set_title(f"Figure 1: Live Commuter Mode Share by Treatment (Session: {session_code})\n"
                 f"[N = {n_participants} participants, n = {total_choices} decisions]",
                 fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    figures['fig_live_mode_share'] = _fig_to_base64(fig)
    
    # -------------------------------------------------------------
    # Figure 2: Round-by-Round Commute Decisions (Scenarios 1 to 8)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    rounds = list(range(1, 9))
    
    car_by_round = [df[df['round_number'] == r]['choice_car'].sum() for r in rounds]
    transit_by_round = [df[df['round_number'] == r]['choice_transit'].sum() for r in rounds]
    active_by_round = [df[df['round_number'] == r]['choice_active'].sum() for r in rounds]
    
    b1 = ax.bar(rounds, car_by_round, label='Private Car', color='#ef4444', alpha=0.9, edgecolor='white')
    b2 = ax.bar(rounds, transit_by_round, bottom=car_by_round, label='Public Transit', color='#10b981', alpha=0.9, edgecolor='white')
    bottom_active = np.array(car_by_round) + np.array(transit_by_round)
    b3 = ax.bar(rounds, active_by_round, bottom=bottom_active, label='Active (Walk/Bike)', color='#3b82f6', alpha=0.9, edgecolor='white')
    
    scenario_subtitles = ['8km\nSunny', '12km\nRain', '15km\nClear', '18km\nCloud', '22km\nClear', '25km\nSnow', '30km\nClear', '35km\nFog']
    ax.set_xticks(rounds)
    ax.set_xticklabels([f"R{r}\n{scenario_subtitles[r-1]}" for r in rounds], fontsize=8.5)
    ax.set_ylabel('Number of Decisions', fontweight='bold')
    ax.set_title(f"Figure 2: Real-Time Choices across 8 Commute Scenarios (Session: {session_code})",
                 fontweight='bold', pad=10)
    ax.legend(loc='upper right', frameon=True, framealpha=0.9)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    figures['fig_live_scenarios'] = _fig_to_base64(fig)
    
    # -------------------------------------------------------------
    # Figure 3: Deliberation Latency / Reaction Times (ms)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 3.6))
    valid_rt = df[df['rt_ms'] > 0]
    if len(valid_rt) > 0:
        treatment_rts = []
        active_treatments = []
        for t in treatments:
            vals = valid_rt[valid_rt['treatment'] == t]['rt_ms'].values
            if len(vals) > 0:
                treatment_rts.append(vals)
                active_treatments.append(f"Treat {t}\n(n={len(vals)})")
                
        if treatment_rts:
            bp = ax.boxplot(treatment_rts, patch_artist=True,
                            boxprops=dict(facecolor='#cbd5e1', color='#475569'),
                            medianprops=dict(color='#0f172a', linewidth=2),
                            whiskerprops=dict(color='#475569'),
                            capprops=dict(color='#475569'))
            ax.set_xticks(range(1, len(active_treatments) + 1))
            ax.set_xticklabels(active_treatments, fontweight='bold')
            colors = ['#94a3b8', '#f87171', '#34d399']
            for patch, col in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                patch.set_facecolor(col)
                patch.set_alpha(0.8)
                
            overall_mean = valid_rt['rt_ms'].mean()
            ax.axhline(overall_mean, color='#dc2626', linestyle=':', linewidth=1.5,
                       label=f"Session Mean: {overall_mean:.0f} ms")
            ax.legend(loc='upper right', frameon=True)
    else:
        ax.text(0.5, 0.5, "No reaction time latency data recorded yet.",
                ha='center', va='center', color='#64748b', fontsize=11)
        
    ax.set_ylabel('Reaction Time (milliseconds)', fontweight='bold')
    ax.set_title(f"Figure 3: Decision Deliberation Latencies in Current Session (Session: {session_code})",
                 fontweight='bold', pad=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    figures['fig_live_reaction_times'] = _fig_to_base64(fig)
    
    # -------------------------------------------------------------
    # Figure 4: Live Participant Demographics & Policy Attitudes
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.4))
    
    # Left subplot: Car Ownership Breakdown in current session
    car_own_counts = df_part['car_ownership'].value_counts()
    if len(car_own_counts) > 0:
        labels = [str(k)[:18] for k in car_own_counts.index]
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899'][:len(labels)]
        ax1.pie(car_own_counts.values, labels=labels, autopct='%1.0f%%',
                colors=colors, startangle=140, textprops={'fontsize': 8.5})
        ax1.set_title(f"Car Ownership (N = {len(df_part)})", fontweight='bold', fontsize=10)
    else:
        ax1.text(0.5, 0.5, "Pending Survey Completion", ha='center', va='center', color='#64748b', fontsize=9)
        ax1.axis('off')
        
    # Right subplot: Attitudinal Ratings (1-7 Likert)
    policy_vars = [
        ('support_carbon_tax', 'Carbon Tax\nSupport', '#ef4444'),
        ('support_mobility_bonus', 'Clean Bonus\nSupport', '#10b981'),
        ('perceived_coerciveness', 'Perceived\nCoerciveness', '#f59e0b')
    ]
    vals = []
    names = []
    bar_cols = []
    for col, name, c in policy_vars:
        if col in df_part.columns and df_part[col].notna().sum() > 0:
            vals.append(df_part[col].mean())
            names.append(name)
            bar_cols.append(c)
            
    if vals:
        b = ax2.bar(names, vals, color=bar_cols, alpha=0.85, edgecolor='white', width=0.5)
        ax2.set_ylim(1, 7.5)
        ax2.set_ylabel('Likert Scale (1 = Low, 7 = High)', fontsize=8.5)
        ax2.set_title("Policy Attitudes & Coerciveness", fontweight='bold', fontsize=10)
        ax2.grid(axis='y', linestyle='--', alpha=0.5)
        for rect, v in zip(b, vals):
            ax2.annotate(f"{v:.1f}", xy=(rect.get_x() + rect.get_width() / 2, v),
                         xytext=(0, 2), textcoords="offset points", ha='center', va='bottom',
                         fontweight='bold', fontsize=8.5)
    else:
        ax2.text(0.5, 0.5, "Pending Post-Task Survey Data", ha='center', va='center', color='#64748b', fontsize=9)
        ax2.axis('off')
        
    fig.suptitle(f"Figure 4: Participant Socio-Attitudinal Indicators (Session: {session_code})",
                 fontweight='bold', fontsize=11, y=1.02)
    plt.tight_layout()
    figures['fig_live_traits'] = _fig_to_base64(fig)
    
    return {
        'has_data': True,
        'total_choices': total_choices,
        'n_participants': n_participants,
        'figures': figures
    }
