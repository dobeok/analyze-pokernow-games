from collections import Counter
import pandas as pd
import glob
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

def card_sorter(card_str, by='rank'):
    """
    assign a numerical value to card string for easier sorting
    by == rank
    >>> 2♠, 2♣, 2♦, 2♥, 3♠, 3♣, ..
    
    by != rank
    >>> 2♠, 3♠, 4♠, .., A♠, 2♣, 3♣, ..
    """
    value = 0
    
    rank = card_str[:-1]
    suit = card_str[-1]

    table = {
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6,
        '7': 7,
        '8': 8,
        '9': 9,
        '10':10,
        'J': 11,
        'Q': 12,
        'K': 13,
        'A': 14,
        '♠': 1,
        '♦': 2,
        '♣': 3,
        '♥': 4,
    }

    if by == 'rank':
        value = table[rank] * 10 + table[suit]
    else:
        value = table[rank] + table[suit] * 100
    
    return value


file_names = glob.glob('../data/processed/flop/*.csv')
dataframes = (pd.read_csv(file, header=None, names=['flop', 'time', 'order', 'session_date']) for file in file_names)

df = pd.concat(dataframes)
df = df.reset_index(drop=True)

df['flop'] = df['flop'].str[8:-1]
df['flop'] = df['flop'].str.split(',')


df[['card_1', 'card_2', 'card_3']] = pd.DataFrame(df['flop'].tolist(), index= df.index)
for col in df.columns:
    if col.startswith('card_'):
        df[col] = df[col].str.strip()


all_flops = df['card_1'].to_list() + df['card_2'].to_list() + df['card_3'].to_list()


# using collections.Counter in case the input file doesn't contain all cards
# want to be flexible here, and not making assumptions about dataset
card_count = Counter(all_flops)
cc = pd.DataFrame.from_dict(dict(card_count), orient='index')
cc = cc.reset_index()
cc = cc.rename(columns={'index': 'card', 0: 'freq'})

cc['rank'] = cc['card'].str[:-1]
cc['suit'] = cc['card'].str[-1]
cc['_value'] = cc['card'].apply(card_sorter, by='suit')

cc = cc.sort_values(by='_value', ascending=False)
cc['freq %'] = (cc['freq'] / cc['freq'].sum()).round(5)


cc.head()

# plot
fig, axes = plt.subplots(1, 4, figsize=(12, 4), sharey=True)

axes[0].barh(
    y=cc.iloc[:13]['rank'],
    width=0,
)


for ax, suit, color in zip(axes, ['♠', '♦', '♣', '♥'], ['#8b8b8b', '#0f8ed3', '#6e9052', '#fb553b']):
    ax.barh(
        y=cc[cc['suit']==suit]['rank'],
        width=cc[cc['suit']==suit]['freq %'],
        height=1,
        ec='white',
        fc=color,
    )
    ax.set_title(suit)
    avg_line = ax.axvline(x=1/52, ls='--', c='k', lw=2)

fig.suptitle('Observed frequency for flopped cards')


# avg_label = ax.annotate(
#     text='Expected\nfrequency',
#     xy=(1/52, 18),
#     xytext=(1/52*1.05, 20),
#     arrowprops=dict(arrowstyle= '->', color='k', lw=2),
#     ha='left', va='center'
#     )
# avg_label.remove()

fig.savefig('../resources/flop-dist.png', bbox_inches='tight')

# let's do a chi-squared test
cc['expected_freq'] = 1/52 * cc['freq'].sum()
cc['O - E'] = cc['freq'] - cc['expected_freq']
cc['(O - E)^2'] = cc['O - E'] * cc['O - E']
cc['(O - E)^2 / E'] = cc['(O - E)^2'] / cc['expected_freq']
chi_squared = cc['(O - E)^2 / E'].sum()

"""
null hypothesis: cards are dealt randomly
alternative hypothesis: cards are not dealt randomly

>>> chi_squared = cc['(O - E)^2 / E'].sum()
>>> chi_squared
>>> 64.20818955601564

>>> alpha = 0.05
>>> d_o_f = len(cc) - 1
>>> d_o_f
>>> 51

critical value at alpha = 0.05 and 51 degress of freedom = 68.66929391
our chi_squared statistics = 64.20818955601564

chi_squared < critical value
we do not reject our null hypothesis
the discrepancies are still due to random fluctuation!
"""