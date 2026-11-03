import pandas as pd
import numpy as np

# =============================================================================
# LOAD DATA
# =============================================================================
print("Loading data...")
demo = pd.read_csv('/mnt/user-data/uploads/SecondSeshData1Demographics.csv')
deposits = pd.read_csv('/mnt/user-data/uploads/SecondSeshData4Deposits.csv')
withdrawals = pd.read_csv('/mnt/user-data/uploads/SecondSeshData5Withdrawals.csv')

# Convert dates
deposits['ProcessDate'] = pd.to_datetime(deposits['ProcessDate'])
withdrawals['ProcessDate'] = pd.to_datetime(withdrawals['ProcessDate'])

print(f"Loaded: {len(demo)} players, {len(deposits)} deposits, {len(withdrawals)} withdrawals")
print("="*70)

# =============================================================================
# DEPOSIT PATTERN 1: Overall Deposit Behavior
# =============================================================================
print("\n📊 DEPOSIT PATTERN 1: Overall Deposit Behavior")
print("-"*70)

# Successful deposits only
successful_deposits = deposits[deposits['Status'] == 'S']

print(f"\nTotal deposit attempts: {len(deposits):,}")
print(f"Successful deposits: {len(successful_deposits):,} ({len(successful_deposits)/len(deposits)*100:.1f}%)")
print(f"Failed deposits: {len(deposits) - len(successful_deposits):,} ({(len(deposits) - len(successful_deposits))/len(deposits)*100:.1f}%)")

print(f"\nTotal deposited: €{successful_deposits['Amount'].sum():,.2f}")
print(f"Average deposit: €{successful_deposits['Amount'].mean():,.2f}")
print(f"Median deposit: €{successful_deposits['Amount'].median():,.2f}")

print("\nDeposit Amount Distribution:")
print(f"  Min:    €{successful_deposits['Amount'].min():,.2f}")
print(f"  25%:    €{successful_deposits['Amount'].quantile(0.25):,.2f}")
print(f"  50%:    €{successful_deposits['Amount'].quantile(0.50):,.2f}")
print(f"  75%:    €{successful_deposits['Amount'].quantile(0.75):,.2f}")
print(f"  Max:    €{successful_deposits['Amount'].max():,.2f}")

# =============================================================================
# DEPOSIT PATTERN 2: By Payment Method
# =============================================================================
print("\n\n📊 DEPOSIT PATTERN 2: By Payment Method")
print("-"*70)

payment_analysis = successful_deposits.groupby('PayMethCat').agg(
    transactions=('DepositID', 'count'),
    unique_players=('UserID', 'nunique'),
    total_amount=('Amount', 'sum'),
    avg_amount=('Amount', 'mean'),
    median_amount=('Amount', 'median')
).round(2)

payment_analysis['pct_transactions'] = (payment_analysis['transactions'] / payment_analysis['transactions'].sum() * 100).round(1)
payment_analysis = payment_analysis.sort_values('transactions', ascending=False)

print("\nPayment Method Breakdown (Successful Deposits):")
print(payment_analysis.to_string())

# =============================================================================
# DEPOSIT PATTERN 3: Per Player Deposit Behavior
# =============================================================================
print("\n\n📊 DEPOSIT PATTERN 3: Per Player Deposit Behavior")
print("-"*70)

player_deposits = successful_deposits.groupby('UserID').agg(
    deposit_count=('DepositID', 'count'),
    total_deposited=('Amount', 'sum'),
    avg_deposit=('Amount', 'mean'),
    first_deposit=('ProcessDate', 'min'),
    last_deposit=('ProcessDate', 'max'),
    unique_methods=('PayMethCat', 'nunique')
).reset_index()

player_deposits['deposit_days'] = (player_deposits['last_deposit'] - player_deposits['first_deposit']).dt.days
player_deposits['deposits_per_month'] = np.where(
    player_deposits['deposit_days'] > 0,
    player_deposits['deposit_count'] / (player_deposits['deposit_days'] / 30),
    player_deposits['deposit_count']
)

print(f"\nPlayers who deposited: {len(player_deposits)}")
print(f"\nDeposit Count per Player:")
print(player_deposits['deposit_count'].describe().round(2))

print(f"\nTotal Deposited per Player:")
print(player_deposits['total_deposited'].describe().round(2))

# Deposit segments
def deposit_segment(amount):
    if amount < 100: return '1. Micro (<€100)'
    elif amount < 500: return '2. Low (€100-500)'
    elif amount < 2000: return '3. Medium (€500-2K)'
    elif amount < 10000: return '4. High (€2K-10K)'
    else: return '5. VIP (>€10K)'

player_deposits['segment'] = player_deposits['total_deposited'].apply(deposit_segment)

print("\nPlayer Deposit Segments:")
segment_summary = player_deposits.groupby('segment').agg(
    players=('UserID', 'count'),
    total_deposited=('total_deposited', 'sum'),
    avg_deposits=('deposit_count', 'mean')
).round(2)
segment_summary['pct_players'] = (segment_summary['players'] / segment_summary['players'].sum() * 100).round(1)
segment_summary['pct_revenue'] = (segment_summary['total_deposited'] / segment_summary['total_deposited'].sum() * 100).round(1)
print(segment_summary)

# =============================================================================
# WITHDRAWAL PATTERN 1: Overall Withdrawal Behavior
# =============================================================================
print("\n\n📊 WITHDRAWAL PATTERN 1: Overall Withdrawal Behavior")
print("-"*70)

successful_withdrawals = withdrawals[withdrawals['Status'] == 'S']
reversed_withdrawals = withdrawals[withdrawals['Status'] == 'R']

print(f"\nTotal withdrawal attempts: {len(withdrawals):,}")
print(f"Successful withdrawals: {len(successful_withdrawals):,} ({len(successful_withdrawals)/len(withdrawals)*100:.1f}%)")
print(f"Reversed withdrawals: {len(reversed_withdrawals):,} ({len(reversed_withdrawals)/len(withdrawals)*100:.1f}%)")

print(f"\nTotal withdrawn: €{successful_withdrawals['Amount'].sum():,.2f}")
print(f"Average withdrawal: €{successful_withdrawals['Amount'].mean():,.2f}")
print(f"Median withdrawal: €{successful_withdrawals['Amount'].median():,.2f}")

print("\nWithdrawal Amount Distribution:")
print(f"  Min:    €{successful_withdrawals['Amount'].min():,.2f}")
print(f"  25%:    €{successful_withdrawals['Amount'].quantile(0.25):,.2f}")
print(f"  50%:    €{successful_withdrawals['Amount'].quantile(0.50):,.2f}")
print(f"  75%:    €{successful_withdrawals['Amount'].quantile(0.75):,.2f}")
print(f"  Max:    €{successful_withdrawals['Amount'].max():,.2f}")

# =============================================================================
# WITHDRAWAL PATTERN 2: Who Withdraws?
# =============================================================================
print("\n\n📊 WITHDRAWAL PATTERN 2: Who Withdraws?")
print("-"*70)

depositors = set(successful_deposits['UserID'].unique())
withdrawers = set(successful_withdrawals['UserID'].unique())

only_deposit = depositors - withdrawers
deposit_and_withdraw = depositors & withdrawers

print(f"\nPlayers who deposited: {len(depositors)}")
print(f"Players who withdrew: {len(withdrawers)}")
print(f"Players who deposited but NEVER withdrew: {len(only_deposit)} ({len(only_deposit)/len(depositors)*100:.1f}%)")
print(f"Players who both deposited and withdrew: {len(deposit_and_withdraw)} ({len(deposit_and_withdraw)/len(depositors)*100:.1f}%)")

# =============================================================================
# WITHDRAWAL PATTERN 3: Per Player Withdrawal Behavior
# =============================================================================
print("\n\n📊 WITHDRAWAL PATTERN 3: Per Player Withdrawal Behavior")
print("-"*70)

player_withdrawals = successful_withdrawals.groupby('UserID').agg(
    withdrawal_count=('WithdrawalID', 'count'),
    total_withdrawn=('Amount', 'sum'),
    avg_withdrawal=('Amount', 'mean'),
    first_withdrawal=('ProcessDate', 'min'),
    last_withdrawal=('ProcessDate', 'max')
).reset_index()

print(f"\nPlayers who withdrew: {len(player_withdrawals)}")
print(f"\nWithdrawal Count per Player:")
print(player_withdrawals['withdrawal_count'].describe().round(2))

print(f"\nTotal Withdrawn per Player:")
print(player_withdrawals['total_withdrawn'].describe().round(2))

# =============================================================================
# PATTERN 4: Deposit vs Withdrawal Balance
# =============================================================================
print("\n\n📊 PATTERN 4: Deposit vs Withdrawal Balance per Player")
print("-"*70)

# Merge deposit and withdrawal totals
balance = player_deposits[['UserID', 'total_deposited', 'deposit_count']].merge(
    player_withdrawals[['UserID', 'total_withdrawn', 'withdrawal_count']], 
    on='UserID', 
    how='left'
)
balance = balance.fillna(0)
balance['net_to_platform'] = balance['total_deposited'] - balance['total_withdrawn']
balance['withdrawal_ratio'] = (balance['total_withdrawn'] / balance['total_deposited']).round(2)

print(f"\nNet Player Contribution to Platform:")
print(f"  Total Deposited: €{balance['total_deposited'].sum():,.2f}")
print(f"  Total Withdrawn: €{balance['total_withdrawn'].sum():,.2f}")
print(f"  Net to Platform: €{balance['net_to_platform'].sum():,.2f}")

print(f"\nWithdrawal Ratio (Withdrawn / Deposited):")
print(balance['withdrawal_ratio'].describe().round(2))

# Withdrawal ratio segments
def withdrawal_segment(ratio):
    if ratio == 0: return '1. Never withdrew (0%)'
    elif ratio < 0.25: return '2. Low withdrawal (<25%)'
    elif ratio < 0.50: return '3. Moderate (25-50%)'
    elif ratio < 0.75: return '4. High (50-75%)'
    elif ratio < 1.0: return '5. Very High (75-100%)'
    else: return '6. Net Winner (>100%)'

balance['withdrawal_segment'] = balance['withdrawal_ratio'].apply(withdrawal_segment)

print("\nWithdrawal Ratio Segments:")
wd_segment = balance.groupby('withdrawal_segment').agg(
    players=('UserID', 'count'),
    avg_deposited=('total_deposited', 'mean'),
    avg_withdrawn=('total_withdrawn', 'mean'),
    avg_net=('net_to_platform', 'mean')
).round(2)
print(wd_segment)

# =============================================================================
# PATTERN 5: Time Between Deposit and First Withdrawal
# =============================================================================
print("\n\n📊 PATTERN 5: Time to First Withdrawal")
print("-"*70)

first_deposit_date = successful_deposits.groupby('UserID')['ProcessDate'].min().reset_index()
first_deposit_date.columns = ['UserID', 'first_deposit']

first_withdrawal_date = successful_withdrawals.groupby('UserID')['ProcessDate'].min().reset_index()
first_withdrawal_date.columns = ['UserID', 'first_withdrawal']

time_to_withdraw = first_deposit_date.merge(first_withdrawal_date, on='UserID', how='inner')
time_to_withdraw['days_to_first_withdrawal'] = (time_to_withdraw['first_withdrawal'] - time_to_withdraw['first_deposit']).dt.days

print(f"\nDays from First Deposit to First Withdrawal:")
print(time_to_withdraw['days_to_first_withdrawal'].describe().round(2))

# Time segments
def time_segment(days):
    if days <= 0: return '1. Same day'
    elif days <= 7: return '2. Within a week'
    elif days <= 30: return '3. Within a month'
    elif days <= 90: return '4. Within 3 months'
    elif days <= 365: return '5. Within a year'
    else: return '6. Over a year'

time_to_withdraw['time_segment'] = time_to_withdraw['days_to_first_withdrawal'].apply(time_segment)

print("\nTime to First Withdrawal Segments:")
print(time_to_withdraw['time_segment'].value_counts().sort_index())

# =============================================================================
# PATTERN 6: Deposit Frequency Over Time
# =============================================================================
print("\n\n📊 PATTERN 6: Deposit Trends Over Time")
print("-"*70)

successful_deposits['year_month'] = successful_deposits['ProcessDate'].dt.to_period('M')

monthly_deposits = successful_deposits.groupby('year_month').agg(
    transactions=('DepositID', 'count'),
    unique_players=('UserID', 'nunique'),
    total_amount=('Amount', 'sum')
).reset_index()

print("\nMonthly Deposit Trends (First 12 months):")
print(monthly_deposits.head(12).to_string(index=False))

print("\nMonthly Deposit Trends (Last 12 months):")
print(monthly_deposits.tail(12).to_string(index=False))

# =============================================================================
# SUMMARY
# =============================================================================
print("\n\n" + "="*70)
print("📋 DEPOSIT/WITHDRAWAL SUMMARY")
print("="*70)

print(f"""
KEY FINDINGS:

1. DEPOSIT BEHAVIOR:
   • {len(depositors)} players made successful deposits
   • Average deposit: €{successful_deposits['Amount'].mean():,.2f}
   • Total deposited: €{successful_deposits['Amount'].sum():,.2f}
   • Top payment methods: EEA debit/credit, eWallet, Bank Transfer

2. WITHDRAWAL BEHAVIOR:
   • Only {len(deposit_and_withdraw)} of {len(depositors)} depositors ever withdrew ({len(deposit_and_withdraw)/len(depositors)*100:.1f}%)
   • {len(only_deposit)} players deposited but NEVER cashed out
   • 46.8% of withdrawal attempts get reversed

3. PLAYER VALUE:
   • Net to platform: €{balance['net_to_platform'].sum():,.2f}
   • Average net per player: €{balance['net_to_platform'].mean():,.2f}
   
4. VIP INSIGHT:
   • VIP segment (>€10K deposits): {len(player_deposits[player_deposits['segment']=='5. VIP (>€10K)'])} players
   • They contribute {segment_summary.loc['5. VIP (>€10K)', 'pct_revenue']:.1f}% of deposit revenue

5. WITHDRAWAL TIMING:
   • Median time to first withdrawal: {time_to_withdraw['days_to_first_withdrawal'].median():.0f} days
   • {len(time_to_withdraw[time_to_withdraw['days_to_first_withdrawal']<=0])} players withdrew same day as first deposit
""")

# Save for Power BI
player_deposits.to_csv('/home/claude/player_deposits_analysis.csv', index=False)
balance.to_csv('/home/claude/player_balance_analysis.csv', index=False)
payment_analysis.to_csv('/home/claude/payment_method_analysis.csv', index=False)
print("✅ Deposit/Withdrawal data saved to CSV")
