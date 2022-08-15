from collections import Counter
import pandas as pd
import glob
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import chisquare

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


# plot
fig, axes = plt.subplots(1, 4, figsize=(12, 4), sharey=True)

# init blank plot to align y-axis label
axes[0].barh(
    y=cc.iloc[:13]['rank'],
    width=0,
)
suit_names = ['spade', 'diamond', 'club', 'heart']
suits = ['♠', '♦', '♣', '♥']
# colors = ['#8b8b8b', '#8b8b8b', '#8b8b8b', '#8b8b8b']
colors = ['#8b8b8b', '#0f8ed3', '#6e9052', '#fb553b']

for ax, suit, suit_name, color in zip(axes, suits, suit_names, colors):
    ax.barh(
        y=cc[cc['suit']==suit]['rank'],
        width=cc[cc['suit']==suit]['freq %'],
        height=1,
        ec='white',
        # fc='#8b8b8b',
        fc=color
        # alpha=.75
    )
    ax.set_title(suit_name, size=10, loc='left')
    ax.set_xlim(0, .025)
    ax.set_ylim(-.5, 12.5)
    labels = ax.get_xticks().tolist()
    labels = [0] + [100*_ for _ in labels[1:]]
    ax.set_xticklabels(labels)
    ax.text(.008, 5, suit, size=99, color='white', ha='center', va='center', alpha=.35)
    avg_line = ax.axvline(x=1/52, ls=':', c='k', lw=2)

fig.suptitle('Observed frequency for flopped cards (unit: %)', y=1.05)

legend_elements = [Line2D([0], [0], color='k', ls=':', lw=2, label='Expected frequency')]
axes[0].legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(2.5, -0.1))


# fig.savefig('../resources/flop-dist.png', bbox_inches='tight')


# chi-squared goodness of fit test
cc['expected_freq'] = 1/52 * cc['freq'].sum()

# individual card (52 categories)
statistics, p_value = chisquare(cc['freq'], cc['expected_freq'])
statistics, p_value

# >>>statistics, p_value
# >>>(64.20818955601564, 0.10130584321971552)

# rank (13 categories)
rank_freq = cc.groupby('rank')['freq'].sum()
statistics, p_value = chisquare(rank_freq)
statistics, p_value

# suit (4 categories)
suit_freq = cc.groupby('suit')['freq'].sum()
statistics, p_value =chisquare(suit_freq)
statistics, p_value