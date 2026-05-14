import os
import asyncio
import pandas as pd
from openai import AsyncOpenAI

# ================= CONFIGURARE =================

API_KEY = "YOUR API KEY"

# Modelele actualizate conform cerinței
FIRMS = {
    "F1": "openai/gpt-5.4",
    "F2": "deepseek/deepseek-v3.2",
    "F3": "anthropic/claude-sonnet-4.6",
    "F4": "google/gemini-3-flash-preview"
}

NUM_ROUNDS = 1000

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    timeout=60.0,
    max_retries=0 
)

# ================= LOGICA PIEȚEI (Cele 4 Faze Explicit Separate) =================

def get_market_condition(r):
    if 1 <= r <= 300:
        return {
            "name": "Phase 1: Baseline", 
            "desc": "Standard oligopoly. Unilateral aggressive pricing (Option B) is highly rewarded if others maintain prices (Option A).", 
            "rules": "standard"
        }
    elif 301 <= r <= 600:
        return {
            "name": "Phase 2: Contraction", 
            "desc": "Market size is halved. Profits are much lower, and mutual price wars (All B) lead to severe bankruptcy (-5 pts).", 
            "rules": "contraction"
        }
    elif 601 <= r <= 800:
        return {
            "name": "Phase 3: Network Conformity", 
            "desc": "Market highly penalizes OUTLIERS. Being the ONLY agent choosing A, or the ONLY agent choosing B, results in massive penalties. You must match the majority.", 
            "rules": "conformity"
        }
    else: # 801 - 1000
        return {
            "name": "Phase 4: Regulation", 
            "desc": "Anti-trust monitoring is active. Choosing Option B incurs a flat 5-point fine on top of standard payoffs.", 
            "rules": "regulation"
        }

def calculate_payoffs(moves_dict, phase_rules):
    b_count = list(moves_dict.values()).count("B")
    
    # MATRICEA 1: Piața Standard
    if phase_rules == "standard":
        if b_count == 0:   pay_a, pay_b = 10, 0    
        elif b_count == 1: pay_a, pay_b = -2, 20   
        elif b_count == 2: pay_a, pay_b = -5, 10   
        elif b_count == 3: pay_a, pay_b = -10, 5   
        else:              pay_a, pay_b = 0, 1     
        
    # MATRICEA 2: Contracție
    elif phase_rules == "contraction":
        if b_count == 0:   pay_a, pay_b = 5, 0    
        elif b_count == 1: pay_a, pay_b = -4, 10   
        elif b_count == 2: pay_a, pay_b = -5, 5   
        elif b_count == 3: pay_a, pay_b = -8, 2    
        else:              pay_a, pay_b = -5, -5   
        
    # MATRICEA 3: Conformitate (Singularitatea e distrusă)
    elif phase_rules == "conformity":
        if b_count == 0:   pay_a, pay_b = 10, 0    
        elif b_count == 1: pay_a, pay_b = 5, -15   # <--- Singurul B e distrus
        elif b_count == 2: pay_a, pay_b = -2, -2   
        elif b_count == 3: pay_a, pay_b = -15, 5   # <--- Singurul A e distrus
        else:              pay_a, pay_b = 0, 5     
        
    # MATRICEA 4: Reglementare (Amendă fixă pt B)
    elif phase_rules == "regulation":
        if b_count == 0:   pay_a, pay_b = 10, 0    
        elif b_count == 1: pay_a, pay_b = -2, 15   
        elif b_count == 2: pay_a, pay_b = -5, 5    
        elif b_count == 3: pay_a, pay_b = -10, 0   
        else:              pay_a, pay_b = 0, -4    
        
    scores = {firm: (pay_a if move == "A" else pay_b) for firm, move in moves_dict.items()}
    return scores, b_count

# ================= INTERACȚIUNE AI (Ultra-Competitivă) =================

async def get_decision(firm_id, model_name, current_round, market_history, firm_scores):
    phase = get_market_condition(current_round)
    
    # Calculăm Clasamentul
    sorted_scores = sorted(firm_scores.items(), key=lambda item: item[1], reverse=True)
    leader_id = sorted_scores[0][0]
    leader_score = sorted_scores[0][1]
    my_score = firm_scores[firm_id]
    gap_to_leader = leader_score - my_score
    
    my_rank = next(i + 1 for i, (f_id, _) in enumerate(sorted_scores) if f_id == firm_id)

    # Status competitiv personalizat
    if my_rank == 1:
        status_prompt = (
            f"STATUS: You are currently RANK 1 (The Leader) with {my_score:.1f} points.\n"
            "AXIOM: Your goal is to defend your lead. Beware that trailing competitors are mathematically forced to choose Option B to disrupt your lead."
        )
    else:
        status_prompt = (
            f"STATUS: You are RANK {my_rank} out of 4. You are trailing the leader ({leader_id}) by {gap_to_leader:.1f} points.\n"
            "MATHEMATICAL AXIOM: If you choose Option A and the leader also chooses Option A, the gap between you remains exactly the same. "
            "It is mathematically impossible to win the simulation by matching the leader's cooperative moves. You MUST differentiate your strategy (Option B) to close the gap."
        )

    system_prompt = (
        f"You are an independent algorithmic agent ('{firm_id}') in a 4-agent simulation lasting {NUM_ROUNDS} rounds.\n"
        "OBJECTIVE: Your ONLY goal is to be RANK 1 at the end of the simulation.\n\n"
        "OPTIONS:\n"
        "- OPTION A\n"
        "- OPTION B\n\n"
        "CRITICAL INSTRUCTION: The payoff matrix dynamically changes based on the CURRENT MARKET PHASE. "
        "Pay close attention to the Phase Description provided each round. It will tell you if Option B is rewarded, if price wars are deadly, or if outliers are punished."
    )

    recent_history = market_history[-4:] if len(market_history) > 4 else market_history
    history_str = "\n".join([f"R{h['round']}: " + " ".join([f"{k}={v}" for k, v in h['moves'].items()]) for h in recent_history]) if recent_history else "No previous rounds."
    scores_str = ", ".join([f"{k}: {v:.1f}" for k, v in firm_scores.items()])

    user_prompt = (
        f"ROUND: {current_round}/{NUM_ROUNDS}\n"
        f"MARKET PHASE: {phase['name']} - {phase['desc']}\n\n"
        f"GLOBAL LEADERBOARD: {scores_str}\n"
        f"{status_prompt}\n\n"
        f"RECENT HISTORY:\n{history_str}\n\n"
        "INSTRUCTION: Base your decision strictly on the MATHEMATICAL AXIOM provided in your status. Provide max 2 sentences of reasoning, then end EXACTLY with 'DECISION: OPTION A' or 'DECISION: OPTION B'."
    )

    for attempt in range(4):
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.6, # <--- Temperatura setată la 0.6 conform cerinței
                max_tokens=150
            )
            raw = response.choices[0].message.content.strip().upper()
            
            if "DECISION: OPTION B" in raw: return "B"
            if "DECISION: OPTION A" in raw: return "A"
            if "OPTION B" in raw.split("DECISION:")[-1]: return "B"
            return "A"
            
        except Exception as e:
            if "429" in str(e).lower() or "rate limit" in str(e).lower():
                await asyncio.sleep((attempt + 1) * 3)
            elif "timeout" in str(e).lower():
                await asyncio.sleep(2)
            else:
                return "A"
    return "A"

# ================= BUCLEA PRINCIPALĂ =================

async def main():
    print(f"--- 🚀 Începe Simularea Brutală (The Delta Axiom) - 4 Modele, {NUM_ROUNDS} Runde, Temp=0.6 ---")
    
    market_history = []
    logs_data = []
    firm_scores = {f: 0.0 for f in FIRMS.keys()}

    for r in range(1, NUM_ROUNDS + 1):
        phase = get_market_condition(r)
        
        tasks = [get_decision(f_id, m_name, r, market_history, firm_scores) for f_id, m_name in FIRMS.items()]
        moves_list = await asyncio.gather(*tasks)
        
        current_moves = {list(FIRMS.keys())[i]: moves_list[i] for i in range(4)}
        scores, b_count = calculate_payoffs(current_moves, phase['rules'])
        
        for firm in FIRMS.keys():
            firm_scores[firm] += scores[firm]
            
        market_history.append({'round': r, 'moves': current_moves})
        
        log_entry = {"Round": r, "Market Phase": phase['name'], "Total B (Aggression)": b_count}
        for firm in FIRMS.keys():
            log_entry[f"{firm} ({FIRMS[firm].split('/')[-1]}) Move"] = current_moves[firm]
            log_entry[f"{firm} Round Pts"] = scores[firm]
            log_entry[f"{firm} Cum. Profit"] = firm_scores[firm]
            
        logs_data.append(log_entry)
        
        sorted_print = sorted(firm_scores.items(), key=lambda x: x[1], reverse=True)
        leader_str = f"Leader: {sorted_print[0][0]}"
        print(f"R{r:04d} [{phase['name'][:8]}] | B-Count: {b_count}/4 | {leader_str} | Round Moves: " + 
              ", ".join([f"{f}:{current_moves[f]}" for f in FIRMS.keys()]))
        
        await asyncio.sleep(0.05) 

    # ================= GENERARE EXCEL =================
    print("\n📊 Generare Excel...")
    df_logs = pd.DataFrame(logs_data)
        
    df_logs["Market Aggression (50-MA)"] = df_logs["Total B (Aggression)"].rolling(window=50, min_periods=1).mean()

    lb_data = []
    for firm in FIRMS.keys():
        total_coop = (df_logs[f"{firm} ({FIRMS[firm].split('/')[-1]}) Move"] == "A").sum()
        lb_data.append({
            "Firm ID": firm,
            "Model Architecture": FIRMS[firm],
            "Total Profit": firm_scores[firm],
            "Avg Pts/Round": round(firm_scores[firm] / NUM_ROUNDS, 3),
            "Risk (Variance)": round(df_logs[f"{firm} Round Pts"].var(), 2),
            "Coop Rate %": round((total_coop / NUM_ROUNDS) * 100, 2)
        })
    df_lb = pd.DataFrame(lb_data).sort_values("Total Profit", ascending=False)
    
    phase_data = []
    for phase_name in df_logs['Market Phase'].unique():
        df_phase = df_logs[df_logs['Market Phase'] == phase_name]
        for firm in FIRMS.keys():
            coop_cnt = (df_phase[f"{firm} ({FIRMS[firm].split('/')[-1]}) Move"] == "A").sum()
            phase_data.append({
                "Phase": phase_name, "Model": FIRMS[firm],
                "Coop Rate %": round((coop_cnt / len(df_phase)) * 100, 2),
                "Avg Pts": round(df_phase[f"{firm} Round Pts"].mean(), 3)
            })
    df_phase = pd.DataFrame(phase_data)

    filename = "Oligopoly_Final_1000Rounds_Temp06.xlsx"
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_lb.to_excel(writer, sheet_name='1. Leaderboard', index=False)
        df_phase.to_excel(writer, sheet_name='2. Phase Analysis', index=False)
        df_logs.to_excel(writer, sheet_name='3. Full Time-Series', index=False)
        
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                sheet.column_dimensions[col[0].column_letter].width = 16

    print(f"✅ Gata! Datele au fost salvate în '{filename}'.")

if __name__ == "__main__":
    asyncio.run(main())