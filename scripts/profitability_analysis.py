import pandas as pd
import numpy as np

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading data...")
demo = pd.read_csv('/mnt/user-data/uploads/SecondSeshData1Demographics.csv')
cash = pd.read_csv('/mnt/user-data/uploads/SecondSeshData2CashGames.csv')
tourney = pd.read_csv('/mnt/user-data/uploads/SecondSeshData3Tournaments.csv')

print(f"Loaded: {len(demo)} players")
print("="*70)

# =============================================================================
# PROFITABILITY 1: Cash Game Players
# =============================================================================
print("\n📊 PROFITABILITY 1: Cash Game Analysis")
print("-"*70)

cash_profit = cash.groupby('UserID').agg(
    total_sessions=('Windows', 'sum'),
    days_played=('Date', 'nunique'),
    total_stakes=('StakesC', 'sum'),
    total_winnings=('WinningsC', 'sum')
).reset_index()

cash_profit['net_profit'] = cash_profit['total_winnings'] - cash_profit['total_stakes']
cash_profit['profit_margin'] = ((cash_profit['net_profit'] / cash_profit['total_stakes']) * 100).round(2)

# Winners vs Losers
cash_winners = cash_profit[cash_profit['net_profit'] > 0]
cash_losers = cash_profit[cash_profit['net_profit'] < 0]
cash_breakeven = cash_profit[cash_profit['net_profit'] == 0]

print(f"\nCash Game Players: {len(cash_profit)}")
print(f"  Winners: {len(cash_winners)} ({len(cash_winners)/len(cash_profit)*100:.1f}%)")
print(f"  Losers:  {len(cash_losers)} ({len(cash_losers)/len(cash_profit)*100:.1f}%)")
print(f"  Break-even: {len(cash_breakeven)} ({len(cash_breakeven)/len(cash_profit)*100:.1f}%)")

print(f"\nTotal Stakes: €{cash_profit['total_stakes'].sum():,.2f}")
print(f"Total Winnings: €{cash_profit['total_winnings'].sum():,.2f}")
print(f"House Revenue (Rake): €{cash_profit['total_stakes'].sum() - cash_profit['total_winnings'].sum():,.2f}")

print(f"\nAverage profit per player: €{cash_profit['net_profit'].mean():,.2f}")
print(f"Median profit per player: €{cash_profit['net_profit'].median():,.2f}")

print("\nTop 5 Cash Game Winners:")
print(cash_profit.nlargest(5, 'net_profit')[['UserID', 'days_played', 'total_stakes', 'total_winnings', 'net_profit']].to_string(index=False))

print("\nTop 5 Cash Game Losers:")
print(cash_profit.nsmallest(5, 'net_profit')[['UserID', 'days_played', 'total_stakes', 'total_winnings', 'net_profit']].to_string(index=False))

# =============================================================================
# PROFITABILITY 2: Tournament Players
# =============================================================================
print("\n\n📊 PROFITABILITY 2: Tournament Analysis")
print("-"*70)

tourney_profit = tourney.groupby('UserID').agg(
    total_tournaments=('Trnmnts', 'sum'),
    days_played=('Date', 'nunique'),
    total_stakes=('StakesT', 'sum'),
    total_winnings=('WinningsT', 'sum')
).reset_index()

tourney_profit['net_profit'] = tourney_profit['total_winnings'] - tourney_profit['total_stakes']
tourney_profit['profit_margin'] = ((tourney_profit['net_profit'] / tourney_profit['total_stakes']) * 100).round(2)

# Winners vs Losers
tourney_winners = tourney_profit[tourney_profit['net_profit'] > 0]
tourney_losers = tourney_profit[tourney_profit['net_profit'] < 0]
tourney_breakeven = tourney_profit[tourney_profit['net_profit'] == 0]

print(f"\nTournament Players: {len(tourney_profit)}")
print(f"  Winners: {len(tourney_winners)} ({len(tourney_winners)/len(tourney_profit)*100:.1f}%)")
print(f"  Losers:  {len(tourney_losers)} ({len(tourney_losers)/len(tourney_profit)*100:.1f}%)")
print(f"  Break-even: {len(tourney_breakeven)} ({len(tourney_breakeven)/len(tourney_profit)*100:.1f}%)")

print(f"\nTotal Stakes (Entry Fees): €{tourney_profit['total_stakes'].sum():,.2f}")
print(f"Total Winnings (Prizes): €{tourney_profit['total_winnings'].sum():,.2f}")
print(f"House Revenue (Rake): €{tourney_profit['total_stakes'].sum() - tourney_profit['total_winnings'].sum():,.2f}")

print(f"\nAverage profit per player: €{tourney_profit['net_profit'].mean():,.2f}")
print(f"Median profit per player: €{tourney_profit['net_profit'].median():,.2f}")

print("\nTop 5 Tournament Winners:")
print(tourney_profit.nlargest(5, 'net_profit')[['UserID', 'total_tournaments', 'total_stakes', 'total_winnings', 'net_profit']].to_string(index=False))

print("\nTop 5 Tournament Losers:")
print(tourney_profit.nsmallest(5, 'net_profit')[['UserID', 'total_tournaments', 'total_stakes', 'total_winnings', 'net_profit']].to_string(index=False))

# =============================================================================
# PROFITABILITY 3: Combined (Cash + Tournament)
# =============================================================================
print("\n\n📊 PROFITABILITY 3: Combined Player Analysis")
print("-"*70)

# Merge cash and tournament profits
cash_summary = cash_profit[['UserID', 'net_profit', 'total_stakes']].copy()
cash_summary.columns = ['UserID', 'cash_profit', 'cash_stakes']

tourney_summary = tourney_profit[['UserID', 'net_profit', 'total_stakes']].copy()
tourney_summary.columns = ['UserID', 'tourney_profit', 'tourney_stakes']

# Start with all players from demographics
combined = demo[['UserID']].copy()
combined = combined.merge(cash_summary, on='UserID', how='left')
combined = combined.merge(tourney_summary, on='UserID', how='left')
combined = combined.fillna(0)

combined['total_profit'] = combined['cash_profit'] + combined['tourney_profit']
combined['total_stakes'] = combined['cash_stakes'] + combined['tourney_stakes']

# Player type
def player_type(row):
    if row['cash_stakes'] > 0 and row['tourney_stakes'] > 0:
        return 'Both'
    elif row['cash_stakes'] > 0:
        return 'Cash Only'
    elif row['tourney_stakes'] > 0:
        return 'Tournament Only'
    else:
        return 'No Play'

combined['player_type'] = combined.apply(player_type, axis=1)

print("\nPlayer Type Distribution:")
print(combined['player_type'].value_counts())

# Profitability by player type
print("\nProfitability by Player Type:")
type_profit = combined.groupby('player_type').agg(
    players=('UserID', 'count'),
    avg_profit=('total_profit', 'mean'),
    total_profit=('total_profit', 'sum'),
    total_stakes=('total_stakes', 'sum')
).round(2)
print(type_profit)

# Overall winners vs losers (excluding no play)
active_players = combined[combined['total_stakes'] > 0]
winners = active_players[active_players['total_profit'] > 0]
losers = active_players[active_players['total_profit'] < 0]

print(f"\n\nOverall Active Player Profitability:")
print(f"  Total Active Players: {len(active_players)}")
print(f"  Winners: {len(winners)} ({len(winners)/len(active_players)*100:.1f}%)")
print(f"  Losers: {len(losers)} ({len(losers)/len(active_players)*100:.1f}%)")

# =============================================================================
# PROFITABILITY 4: By Demographics
# =============================================================================
print("\n\n📊 PROFITABILITY 4: By Demographics")
print("-"*70)

# Merge with demographics
combined_demo = combined.merge(demo, on='UserID')

# By Gender
print("\nProfitability by Gender:")
gender_profit = combined_demo[combined_demo['total_stakes'] > 0].groupby('Gender').agg(
    players=('UserID', 'count'),
    avg_profit=('total_profit', 'mean'),
    median_profit=('total_profit', 'median'),
    total_profit=('total_profit', 'sum')
).round(2)
print(gender_profit)

# By Age Group
combined_demo['age_group'] = pd.cut(combined_demo['SystemAgeAsOfReg'], 
                                     bins=[0, 25, 35, 45, 55, 100], 
                                     labels=['18-25', '26-35', '36-45', '46-55', '55+'])

print("\nProfitability by Age Group:")
age_profit = combined_demo[combined_demo['total_stakes'] > 0].groupby('age_group').agg(
    players=('UserID', 'count'),
    avg_profit=('total_profit', 'mean'),
    median_profit=('total_profit', 'median'),
    pct_winners=('total_profit', lambda x: (x > 0).sum() / len(x) * 100)
).round(2)
print(age_profit)

# =============================================================================
# PROFITABILITY 5: Profit Distribution
# =============================================================================
print("\n\n📊 PROFITABILITY 5: Profit Distribution")
print("-"*70)

active = combined[combined['total_stakes'] > 0]['total_profit']

print(f"\nProfit Distribution Statistics:")
print(f"  Min:    €{active.min():,.2f}")
print(f"  25%:    €{active.quantile(0.25):,.2f}")
print(f"  50%:    €{active.quantile(0.50):,.2f}")
print(f"  75%:    €{active.quantile(0.75):,.2f}")
print(f"  Max:    €{active.max():,.2f}")
print(f"  Mean:   €{active.mean():,.2f}")
print(f"  Std:    €{active.std():,.2f}")

# Profit brackets
def profit_bracket(p):
    if p < -1000: return '1. Lost >€1000'
    elif p < -100: return '2. Lost €100-1000'
    elif p < 0: return '3. Lost €0-100'
    elif p == 0: return '4. Break-even'
    elif p < 100: return '5. Won €0-100'
    elif p < 1000: return '6. Won €100-1000'
    else: return '7. Won >€1000'

combined['profit_bracket'] = combined[combined['total_stakes'] > 0]['total_profit'].apply(profit_bracket)

print("\nProfit Brackets:")
print(combined['profit_bracket'].value_counts().sort_index())

# =============================================================================
# SUMMARY
# =============================================================================
print("\n\n" + "="*70)
print("📋 PROFITABILITY SUMMARY")
print("="*70)

print(f"""
KEY FINDINGS:

1. CASH GAMES:
   • {len(cash_winners)}/{len(cash_profit)} players profitable ({len(cash_winners)/len(cash_profit)*100:.1f}%)
   • House rake: €{cash_profit['total_stakes'].sum() - cash_profit['total_winnings'].sum():,.2f}

2. TOURNAMENTS:
   • {len(tourney_winners)}/{len(tourney_profit)} players profitable ({len(tourney_winners)/len(tourney_profit)*100:.1f}%)
   • House rake: €{tourney_profit['total_stakes'].sum() - tourney_profit['total_winnings'].sum():,.2f}

3. OVERALL:
   • {len(winners)}/{len(active_players)} active players profitable ({len(winners)/len(active_players)*100:.1f}%)
   • Average player loss: €{active.mean()*-1:,.2f}
   
4. PLAYER TYPES:
   • {len(combined[combined['player_type']=='Cash Only'])} cash-only players
   • {len(combined[combined['player_type']=='Tournament Only'])} tournament-only players  
   • {len(combined[combined['player_type']=='Both'])} play both

BUSINESS INSIGHT:
The majority of players lose money, which is expected in poker (house takes rake).
However, ~30-33% of players are profitable - these are likely skilled players
who are taking money from recreational players.
""")

# Save for Power BI
combined.to_csv('/home/claude/player_profitability.csv', index=False)
combined_demo.to_csv('/home/claude/player_profitability_demographics.csv', index=False)
print("✅ Profitability data saved to CSV")
