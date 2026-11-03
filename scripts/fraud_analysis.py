import pandas as pd
import numpy as np

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading data...")
demo = pd.read_csv('/mnt/user-data/uploads/SecondSeshData1Demographics.csv')
cash = pd.read_csv('/mnt/user-data/uploads/SecondSeshData2CashGames.csv')
tourney = pd.read_csv('/mnt/user-data/uploads/SecondSeshData3Tournaments.csv')
deposits = pd.read_csv('/mnt/user-data/uploads/SecondSeshData4Deposits.csv')
withdrawals = pd.read_csv('/mnt/user-data/uploads/SecondSeshData5Withdrawals.csv')

print(f"Loaded: {len(demo)} players, {len(deposits)} deposits, {len(withdrawals)} withdrawals")
print("="*70)

# =============================================================================
# FRAUD SIGNAL 1: Failed Deposit Rate by Payment Method
# =============================================================================
print("\n📊 FRAUD SIGNAL 1: Failed Deposits by Payment Method")
print("-"*70)

# Group by payment method, count successes and failures
deposit_by_method = deposits.groupby('PayMethCat').agg(
    total_deposits=('DepositID', 'count'),
    failed_deposits=('Status', lambda x: (x == 'F').sum()),
    total_amount=('Amount', 'sum')
).reset_index()

deposit_by_method['failure_rate'] = (deposit_by_method['failed_deposits'] / deposit_by_method['total_deposits'] * 100).round(2)
deposit_by_method = deposit_by_method.sort_values('failure_rate', ascending=False)

print("\nPayment Method Failure Rates:")
print(deposit_by_method.to_string(index=False))

# =============================================================================
# FRAUD SIGNAL 2: Failed Deposit Rate by Player
# =============================================================================
print("\n\n📊 FRAUD SIGNAL 2: Players with High Failed Deposit Rates")
print("-"*70)

# Calculate per player
player_deposits = deposits.groupby('UserID').agg(
    total_deposits=('DepositID', 'count'),
    failed_deposits=('Status', lambda x: (x == 'F').sum()),
    successful_deposits=('Status', lambda x: (x == 'S').sum()),
    total_amount_attempted=('Amount', 'sum')
).reset_index()

player_deposits['failure_rate'] = (player_deposits['failed_deposits'] / player_deposits['total_deposits'] * 100).round(2)

# Flag players with high failure rate (>50%) AND multiple attempts (>5)
high_fail_players = player_deposits[
    (player_deposits['failure_rate'] > 50) & 
    (player_deposits['total_deposits'] >= 5)
].sort_values('failure_rate', ascending=False)

print(f"\nPlayers with >50% failure rate (min 5 attempts): {len(high_fail_players)}")
print(f"\nTop 10 suspicious players:")
print(high_fail_players.head(10).to_string(index=False))

# =============================================================================
# FRAUD SIGNAL 3: Withdrawal Reversal Rate by Payment Method
# =============================================================================
print("\n\n📊 FRAUD SIGNAL 3: Withdrawal Reversals by Payment Method")
print("-"*70)

withdrawal_by_method = withdrawals.groupby('PayMethCat').agg(
    total_withdrawals=('WithdrawalID', 'count'),
    reversed_withdrawals=('Status', lambda x: (x == 'R').sum()),
    total_amount=('Amount', 'sum')
).reset_index()

withdrawal_by_method['reversal_rate'] = (withdrawal_by_method['reversed_withdrawals'] / withdrawal_by_method['total_withdrawals'] * 100).round(2)
withdrawal_by_method = withdrawal_by_method.sort_values('reversal_rate', ascending=False)

print("\nPayment Method Reversal Rates:")
print(withdrawal_by_method.to_string(index=False))

# =============================================================================
# FRAUD SIGNAL 4: Players with High Withdrawal Reversals
# =============================================================================
print("\n\n📊 FRAUD SIGNAL 4: Players with High Withdrawal Reversal Rates")
print("-"*70)

player_withdrawals = withdrawals.groupby('UserID').agg(
    total_withdrawals=('WithdrawalID', 'count'),
    reversed_withdrawals=('Status', lambda x: (x == 'R').sum()),
    successful_withdrawals=('Status', lambda x: (x == 'S').sum()),
    total_amount_requested=('Amount', 'sum')
).reset_index()

player_withdrawals['reversal_rate'] = (player_withdrawals['reversed_withdrawals'] / player_withdrawals['total_withdrawals'] * 100).round(2)

# Flag players with high reversal rate (>70%) AND multiple withdrawals (>3)
high_reversal_players = player_withdrawals[
    (player_withdrawals['reversal_rate'] > 70) & 
    (player_withdrawals['total_withdrawals'] >= 3)
].sort_values('reversal_rate', ascending=False)

print(f"\nPlayers with >70% reversal rate (min 3 attempts): {len(high_reversal_players)}")
print(f"\nTop 10 suspicious players:")
print(high_reversal_players.head(10).to_string(index=False))

# =============================================================================
# FRAUD SIGNAL 5: Quick Deposit-to-Withdrawal (Potential Money Laundering)
# =============================================================================
print("\n\n📊 FRAUD SIGNAL 5: Quick Deposit-to-Withdrawal Pattern")
print("-"*70)

# Convert dates
deposits['ProcessDate'] = pd.to_datetime(deposits['ProcessDate'])
withdrawals['ProcessDate'] = pd.to_datetime(withdrawals['ProcessDate'])

# Get first successful deposit and first successful withdrawal per player
first_deposit = deposits[deposits['Status'] == 'S'].groupby('UserID')['ProcessDate'].min().reset_index()
first_deposit.columns = ['UserID', 'first_deposit_date']

first_withdrawal = withdrawals[withdrawals['Status'] == 'S'].groupby('UserID')['ProcessDate'].min().reset_index()
first_withdrawal.columns = ['UserID', 'first_withdrawal_date']

# Merge
deposit_to_withdrawal = first_deposit.merge(first_withdrawal, on='UserID', how='inner')
deposit_to_withdrawal['days_to_withdraw'] = (deposit_to_withdrawal['first_withdrawal_date'] - deposit_to_withdrawal['first_deposit_date']).dt.days

# Quick withdrawals (within 1 day)
quick_withdrawers = deposit_to_withdrawal[deposit_to_withdrawal['days_to_withdraw'] <= 1]

print(f"\nPlayers who withdrew within 1 day of first deposit: {len(quick_withdrawers)}")
print(f"Percentage of withdrawing players: {len(quick_withdrawers)/len(deposit_to_withdrawal)*100:.1f}%")

# Distribution
print("\nDays to first withdrawal distribution:")
print(deposit_to_withdrawal['days_to_withdraw'].describe())

# =============================================================================
# FRAUD SIGNAL 6: Deposited but Didn't Play (Potential Money Laundering)
# =============================================================================
print("\n\n📊 FRAUD SIGNAL 6: Deposited but Low/No Gameplay")
print("-"*70)

# Get total deposits per player
total_deposits_per_player = deposits[deposits['Status'] == 'S'].groupby('UserID')['Amount'].sum().reset_index()
total_deposits_per_player.columns = ['UserID', 'total_deposited']

# Get total stakes (gameplay) per player - combine cash and tournament
cash_stakes = cash.groupby('UserID')['StakesC'].sum().reset_index()
cash_stakes.columns = ['UserID', 'cash_stakes']

tourney_stakes = tourney.groupby('UserID')['StakesT'].sum().reset_index()
tourney_stakes.columns = ['UserID', 'tourney_stakes']

# Merge all
activity = total_deposits_per_player.merge(cash_stakes, on='UserID', how='left')
activity = activity.merge(tourney_stakes, on='UserID', how='left')
activity = activity.fillna(0)
activity['total_stakes'] = activity['cash_stakes'] + activity['tourney_stakes']

# Calculate play ratio (how much of deposit was actually played)
activity['play_ratio'] = (activity['total_stakes'] / activity['total_deposited']).round(2)

# Low play ratio = suspicious (deposited money but didn't play much)
low_play = activity[
    (activity['play_ratio'] < 0.5) & 
    (activity['total_deposited'] >= 100)  # Minimum €100 deposited
].sort_values('play_ratio')

print(f"\nPlayers who played <50% of deposits (min €100 deposited): {len(low_play)}")
print(f"\nTop 10 low-activity depositors:")
print(low_play.head(10).to_string(index=False))

# =============================================================================
# SUMMARY: Fraud Risk Flags
# =============================================================================
print("\n\n" + "="*70)
print("📋 FRAUD SIGNAL SUMMARY")
print("="*70)

print(f"""
DEPOSIT FRAUD INDICATORS:
• High-risk payment method: Cards (see failure rates above)
• Players with >50% failed deposits: {len(high_fail_players)}

WITHDRAWAL FRAUD INDICATORS:  
• High-risk payment method: (see reversal rates above)
• Players with >70% reversal rate: {len(high_reversal_players)}

MONEY LAUNDERING INDICATORS:
• Players withdrawing within 1 day: {len(quick_withdrawers)}
• Players with low play ratio (<50%): {len(low_play)}

RECOMMENDED ACTIONS:
1. Review players flagged in multiple categories
2. Investigate payment methods with high failure/reversal rates
3. Set up automated alerts for quick deposit-to-withdrawal patterns
4. Monitor low-activity high-deposit accounts
""")

# =============================================================================
# SAVE FLAGGED PLAYERS FOR FURTHER REVIEW
# =============================================================================
# Combine all flags
high_fail_players['flag_failed_deposits'] = 1
high_reversal_players['flag_high_reversals'] = 1
quick_withdrawers['flag_quick_withdrawal'] = 1
low_play['flag_low_play'] = 1

# We'll save these for Power BI later
high_fail_players.to_csv('/home/claude/flagged_failed_deposits.csv', index=False)
high_reversal_players.to_csv('/home/claude/flagged_high_reversals.csv', index=False)
quick_withdrawers.to_csv('/home/claude/flagged_quick_withdrawals.csv', index=False)
low_play.to_csv('/home/claude/flagged_low_play.csv', index=False)

print("\n✅ Flagged player lists saved to CSV files")
