import pandas as pd

file_name = "raw_data.csv"
df = pd.read_csv(f'../data/raw/{file_name}')
df = df.drop('order', axis=1)

# remove sensitive data
df = df.drop(df.loc[df['entry'].str.startswith('Your hand is')].index)



# PREPROCESS DATA
# ---------------------------------------------------------------------------------------
# reverse file because original log file is latest first
df = df.reset_index().drop('index', axis=1)
df['at'] = pd.to_datetime(df['at'])


# find player names
df['num_@'] = df['entry'].str.count('@')
df['player_name'] = df.loc[df['num_@']==1]['entry'].str.extract('(".*")')
df['player_name'] = df['player_name'].fillna('""').str[1:].str[:-1]

# TODO: clean up player names
df['player_id'] = df['player_name'].str[-10:]
df['player_name'] = df['player_id']
df = df.drop('player_id', axis=1)




# find hand number
df['hand_num'] = None
df['hand_num'] = df['entry'].str.extract('-- starting hand #(\d{1,3})')
df['hand_num'] = df['hand_num'].ffill()

df['hand_id'] = df['session_date'] + '(' + df['hand_num'].astype(str) + ')'
# df['hand_id'] = df['hand_id'].ffill()

# identify event
df['phase'] = None
df.loc[df['entry'].str.startswith('-- starting hand'), 'phase'] = 'Pre-flop'
df.loc[df['entry'].str.startswith('Flop:'), 'phase'] = 'Flop'
df.loc[df['entry'].str.startswith('Turn:'), 'phase'] = 'Turn'
df.loc[df['entry'].str.startswith('River:'), 'phase'] = 'River'
df['phase'] = df['phase'].ffill()


# find action
df['action'] = None
for action in ['small blind', 'big blind', 'folds',  'checks', 'bets',  'raises',  'calls']:
    df.loc[(df['player_name'].notnull()) & (df['entry'].str.contains(action)), 'action'] = action.capitalize()

df.loc[df['action'].isin(['Bets', 'Raises']), 'action'] = 'Bets/Raises'

df.loc[df['entry'].str.contains('dealer:'), 'action'] = 'Dealer'
df.loc[df['entry'].str.contains('collected'), 'action'] = 'Won'


# CONT NUMBER OF PLAYERS
df['num_players'] = None
df['num_players'] = df.loc[df['entry'].str.startswith('Player stacks')]['entry'].str.count('@ [A-Za-z0-9\-]{10}"')
df.loc[df['action']=='Folds', 'num_players'] = -1
df['num_players'] = df.groupby('hand_id')['num_players'].cumsum()
df['num_players'] = df.groupby('hand_id')['num_players'].ffill()


# RANK ACTION TO CALCULATE METRICS
# find first raiser
df.loc[df['action']=='Small blind', 'at'] = df['at'] + pd.Timedelta(.01, 'sec')
df.loc[df['action']=='Big blind', 'at'] = df['at'] + pd.Timedelta(.02, 'sec')


cond = (df['player_name'].notnull()) & (df['action'].notnull())
# all ranking are grouped by hand and phase
# rank-R1: ranking for that hand's actions (all players)
# (A) rank among all players
df['rank-A1'] = df.loc[cond].groupby(['hand_id', 'phase'])['at'].rank()
df['rank-A2'] = df.loc[cond].groupby(['hand_id', 'phase', 'action'])['at'].rank()

# rank within each individual
df['rank-P0'] = df.loc[cond].groupby(['hand_id', 'phase','player_name'])['at'].rank() # to find position
df['rank-P1'] = df.loc[cond].groupby(['hand_id', 'phase','player_name', 'action'])['at'].rank() # to find their first action
df['rank-P2'] = df.loc[cond & (~df['action'].isin(['Dealer', 'big blind', 'small blind']))].groupby(['hand_id', 'phase','player_name', 'action'])['at'].rank() # to find their 1st action, exld involuntary


# DETERMINE POSITION
df['position'] = None
df['position'] = (df.loc[(df['phase']=='Pre-flop') & (df['rank-P0']==1)]['rank-A1']-1) / df.loc[(df['phase']=='Pre-flop') & (df['rank-P0']==1)]['num_players']
df['position_tag'] = None
df.loc[df['action']=='Dealer', 'position_tag'] = 'Dealer'
df.loc[df['position']<1/3, 'position_tag'] = 'EP'
df.loc[(1/3 <= df['position']) & (df['position']<2/3), 'position_tag'] = 'MP'
df.loc[2/3 <= df['position'], 'position_tag'] = 'LP'
df['position_tag'] = df.groupby(['hand_id', 'player_name'])['position_tag'].ffill()
df = df.drop('position', axis=1)

# CALCULATE TIME LAG TO DETERMINE LONG ACTIONS
df['time_elapsed'] = None
df.loc[df['action']=='Dealer', 'time_elapsed'] = 0
df.loc[df['action']!='Dealer', 'time_elapsed'] = df['at'].diff(1) / pd.Timedelta(1, 's')


# Calculate pot value
# extract numerical values from entry
df['_amount'] = None
df['_amount'] = df.loc[df['hand_id'].notnull()]['entry'].str.extract('(\d{1,3}\.\d{2})')
df['_amount'] = pd.to_numeric(df['_amount'])

# deduce the amount of money put in by each
df['put_in'] = None
df['put_in'] = df.loc[(df['action']!='Won') & (df['action'].notnull())].groupby(['hand_id', 'phase', 'player_name'])['_amount'].diff(1)
df.loc[df['entry'].str.startswith('Uncalled bet of'), 'put_in'] = -df['_amount']
df.loc[(df['hand_id'].notnull()) & (df['phase'].notnull()) & (df['player_name'].notnull()) & (df['put_in'].isnull() & (df['action'].notnull()) & (df['action']!='Won')), 'put_in'] = df['_amount']
df['pot_size'] = df.groupby(['hand_id'])['put_in'].cumsum()

if __name__ == '__main__':
    df.drop('entry', axis=1).to_csv(f'../data/processed/processed-{file_name}', index=False)
    print(f'Exported file to ../data/processed/processed-{file_name}')