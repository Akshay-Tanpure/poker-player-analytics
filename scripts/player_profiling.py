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

print(f"Loaded: {len(demo)} players")
print("="*70)

# =============================================================================
# PROFILE 1: Age Distribution
# =============================================================================
print("\n📊 PROFILE 1: Age Distribution")
print("-"*70)

print(f"\nAge Statistics:")
print(f"  Min: {demo['SystemAgeAsOfReg'].min()}")
print(f"  Max: {demo['SystemAgeAsOfReg'].max()}")
print(f"  Mean: {demo['SystemAgeAsOfReg'].mean():.1f}")
print(f"  Median: {demo['SystemAgeAsOfReg'].median():.1f}")

# Age groups
demo['age_group'] = pd.cut(demo['SystemAgeAsOfReg'], 
                           bins=[0, 21, 25, 30, 35, 40, 45, 50, 55, 60, 100], 
                           labels=['<21', '21-25', '26-30', '31-35', '36-40', 
                                   '41-45', '46-50', '51-55', '56-60', '60+'])

print("\nAge Group Distribution:")
age_dist = demo['age_group'].value_counts().sort_index()
for age, count in age_dist.items():
    pct = count / len(demo) * 100
    bar = '█' * int(pct / 2)
    print(f"  {age:>6}: {count:>4} ({pct:>5.1f}%) {bar}")

# =============================================================================
# PROFILE 2: Gender Distribution
# =============================================================================
print("\n\n📊 PROFILE 2: Gender Distribution")
print("-"*70)

gender_dist = demo['Gender'].value_counts()
print(f"\nGender Split:")
print(f"  Male:   {gender_dist['M']:,} ({gender_dist['M']/len(demo)*100:.1f}%)")
print(f"  Female: {gender_dist['F']:,} ({gender_dist['F']/len(demo)*100:.1f}%)")
print(f"\nMale to Female Ratio: {gender_dist['M']/gender_dist['F']:.1f}:1")

# =============================================================================
# PROFILE 3: Country Distribution
# =============================================================================
print("\n\n📊 PROFILE 3: Country Distribution")
print("-"*70)

# Country code mapping (ISO 3166-1 numeric)
country_map = {
    276: 'Germany',
    250: 'France', 
    724: 'Spain',
    56: 'Belgium',
    826: 'United Kingdom',
    40: 'Austria',
    756: 'Switzerland',
    528: 'Netherlands',
    620: 'Portugal',
    372: 'Ireland',
    246: 'Finland',
    208: 'Denmark',
    578: 'Norway',
    752: 'Sweden',
    380: 'Italy',
    616: 'Poland',
    203: 'Czech Republic',
    348: 'Hungary',
    642: 'Romania',
    300: 'Greece'
}

demo['country'] = demo['CountryID'].map(country_map).fillna('Other')

print("\nTop 15 Countries:")
country_dist = demo['country'].value_counts().head(15)
for country, count in country_dist.items():
    pct = count / len(demo) * 100
    bar = '█' * int(pct / 2)
    print(f"  {country:>15}: {count:>4} ({pct:>5.1f}%) {bar}")

# =============================================================================
# PROFILE 4: Age by Gender
# =============================================================================
print("\n\n📊 PROFILE 4: Age by Gender")
print("-"*70)

age_gender = demo.groupby(['age_group', 'Gender']).size().unstack(fill_value=0)
age_gender['total'] = age_gender.sum(axis=1)
age_gender['pct_female'] = (age_gender['F'] / age_gender['total'] * 100).round(1)

print("\nAge Groups by Gender:")
print(age_gender.to_string())

print(f"\nAverage Age by Gender:")
print(f"  Male:   {demo[demo['Gender']=='M']['SystemAgeAsOfReg'].mean():.1f} years")
print(f"  Female: {demo[demo['Gender']=='F']['SystemAgeAsOfReg'].mean():.1f} years")

# =============================================================================
# PROFILE 5: Demographics vs Gameplay
# =============================================================================
print("\n\n📊 PROFILE 5: Demographics vs Gameplay Behavior")
print("-"*70)

# Calculate player activity
cash_activity = cash.groupby('UserID').agg(
    cash_days=('Date', 'nunique'),
    cash_stakes=('StakesC', 'sum')
).reset_index()

tourney_activity = tourney.groupby('UserID').agg(
    tourney_days=('Date', 'nunique'),
    tourney_stakes=('StakesT', 'sum')
).reset_index()

deposit_activity = deposits[deposits['Status']=='S'].groupby('UserID').agg(
    total_deposited=('Amount', 'sum')
).reset_index()

# Merge with demographics
player_profile = demo.merge(cash_activity, on='UserID', how='left')
player_profile = player_profile.merge(tourney_activity, on='UserID', how='left')
player_profile = player_profile.merge(deposit_activity, on='UserID', how='left')

# Fill numeric columns only
numeric_cols = ['cash_days', 'cash_stakes', 'tourney_days', 'tourney_stakes', 'total_deposited']
player_profile[numeric_cols] = player_profile[numeric_cols].fillna(0)

player_profile['total_stakes'] = player_profile['cash_stakes'] + player_profile['tourney_stakes']
player_profile['total_days'] = player_profile['cash_days'] + player_profile['tourney_days']

# Activity by Age Group
print("\nActivity by Age Group:")
age_activity = player_profile.groupby('age_group').agg(
    players=('UserID', 'count'),
    avg_deposits=('total_deposited', 'mean'),
    avg_stakes=('total_stakes', 'mean'),
    avg_days_played=('total_days', 'mean'),
    pct_active=('total_stakes', lambda x: (x > 0).sum() / len(x) * 100)
).round(2)
print(age_activity.to_string())

# Activity by Gender
print("\nActivity by Gender:")
gender_activity = player_profile.groupby('Gender').agg(
    players=('UserID', 'count'),
    avg_deposits=('total_deposited', 'mean'),
    avg_stakes=('total_stakes', 'mean'),
    avg_days_played=('total_days', 'mean'),
    pct_active=('total_stakes', lambda x: (x > 0).sum() / len(x) * 100)
).round(2)
print(gender_activity.to_string())

# Activity by Country (Top 10)
print("\nActivity by Country (Top 10):")
country_activity = player_profile.groupby('country').agg(
    players=('UserID', 'count'),
    avg_deposits=('total_deposited', 'mean'),
    avg_stakes=('total_stakes', 'mean'),
    pct_active=('total_stakes', lambda x: (x > 0).sum() / len(x) * 100)
).round(2)
country_activity = country_activity[country_activity['players'] >= 50].sort_values('avg_deposits', ascending=False).head(10)
print(country_activity.to_string())

# =============================================================================
# PROFILE 6: Player Segments
# =============================================================================
print("\n\n📊 PROFILE 6: Player Segments")
print("-"*70)

# Define player type
def get_player_type(row):
    if row['cash_stakes'] > 0 and row['tourney_stakes'] > 0:
        return 'Hybrid'
    elif row['cash_stakes'] > 0:
        return 'Cash Only'
    elif row['tourney_stakes'] > 0:
        return 'Tournament Only'
    else:
        return 'Inactive'

player_profile['player_type'] = player_profile.apply(get_player_type, axis=1)

# Define value segment
def get_value_segment(deposits):
    if deposits == 0: return '1. No Deposit'
    elif deposits < 100: return '2. Micro'
    elif deposits < 500: return '3. Low'
    elif deposits < 2000: return '4. Medium'
    elif deposits < 10000: return '5. High'
    else: return '6. VIP'

player_profile['value_segment'] = player_profile['total_deposited'].apply(get_value_segment)

print("\nPlayer Type Distribution:")
type_dist = player_profile['player_type'].value_counts()
for ptype, count in type_dist.items():
    pct = count / len(player_profile) * 100
    print(f"  {ptype:>15}: {count:>4} ({pct:>5.1f}%)")

print("\nValue Segment Distribution:")
value_dist = player_profile['value_segment'].value_counts().sort_index()
for seg, count in value_dist.items():
    pct = count / len(player_profile) * 100
    print(f"  {seg:>15}: {count:>4} ({pct:>5.1f}%)")

# Cross-tab: Player Type vs Value Segment
print("\nPlayer Type vs Value Segment:")
cross_tab = pd.crosstab(player_profile['player_type'], player_profile['value_segment'])
print(cross_tab.to_string())

# =============================================================================
# PROFILE 7: Demographics of VIPs
# =============================================================================
print("\n\n📊 PROFILE 7: VIP Player Profile")
print("-"*70)

vips = player_profile[player_profile['value_segment'] == '6. VIP']

print(f"\nVIP Count: {len(vips)}")

print(f"\nVIP Age Distribution:")
print(vips['age_group'].value_counts().sort_index())

print(f"\nVIP Gender Split:")
vip_gender = vips['Gender'].value_counts()
print(f"  Male:   {vip_gender.get('M', 0)} ({vip_gender.get('M', 0)/len(vips)*100:.1f}%)")
print(f"  Female: {vip_gender.get('F', 0)} ({vip_gender.get('F', 0)/len(vips)*100:.1f}%)")

print(f"\nVIP Top Countries:")
print(vips['country'].value_counts().head(5))

print(f"\nVIP Player Type:")
print(vips['player_type'].value_counts())

print(f"\nVIP Average Stats:")
print(f"  Avg Age: {vips['SystemAgeAsOfReg'].mean():.1f}")
print(f"  Avg Deposits: €{vips['total_deposited'].mean():,.2f}")
print(f"  Avg Stakes: €{vips['total_stakes'].mean():,.2f}")
print(f"  Avg Days Played: {vips['total_days'].mean():.1f}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n\n" + "="*70)
print("📋 PLAYER PROFILING SUMMARY")
print("="*70)

print(f"""
KEY FINDINGS:

1. AGE PROFILE:
   • Average age: {demo['SystemAgeAsOfReg'].mean():.1f} years
   • Peak age group: 21-25 ({age_dist['21-25']} players, {age_dist['21-25']/len(demo)*100:.1f}%)
   • Young skew: {(demo['SystemAgeAsOfReg'] <= 30).sum()/len(demo)*100:.1f}% are under 30

2. GENDER PROFILE:
   • {gender_dist['M']/len(demo)*100:.1f}% Male, {gender_dist['F']/len(demo)*100:.1f}% Female
   • Ratio: {gender_dist['M']/gender_dist['F']:.1f}:1 (typical for poker)

3. GEOGRAPHY:
   • Top 3 markets: Germany, France, Spain
   • {demo['country'].value_counts().head(3).sum()/len(demo)*100:.1f}% from top 3 countries

4. PLAYER TYPES:
   • {type_dist.get('Hybrid', 0)} play both formats (most engaged)
   • {type_dist.get('Cash Only', 0)} cash-only players
   • {type_dist.get('Tournament Only', 0)} tournament-only players

5. VIP PROFILE (Top {len(vips)} players):
   • Avg age: {vips['SystemAgeAsOfReg'].mean():.1f} (slightly older)
   • {vip_gender.get('M', 0)/len(vips)*100:.1f}% Male
   • Most are Hybrid players ({vips['player_type'].value_counts().get('Hybrid', 0)})
   • Avg deposits: €{vips['total_deposited'].mean():,.2f}

MARKETING INSIGHTS:
• Target demographic: Males, 21-35, Germany/France/Spain
• VIPs skew older and play both formats
• Female players are underrepresented (opportunity?)
""")

# Save for Power BI
player_profile.to_csv('/home/claude/player_profile_complete.csv', index=False)
print("✅ Player profile data saved to CSV")
