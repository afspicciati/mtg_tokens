# dependencies 
import pandas as pd
from json import loads
from requests import get

def to_card_list(card_names):
    """Returns importable list of cards..

    Keyword arguments:
    card_names;     list of str -- list of cardnames.
    """ 

    if not card_names[0][0].isdigit():
        card_names = ["1 " + card for card in card_names]

    out_str_list = card_names[0]
    for card in card_names[1:]:
        out_str_list += "\n" + card
    
    return out_str_list

def fix_names(card_names, scryfall_names):
    """Helper function for get_card_data.
       Returns scryfall formatted list of card names.
       Mainly to format double-sided card names.
    
    Keyword arguments:
    card_names;     list of str -- list of cardnames.
    scryfall_names; list of str -- list of cardnames from scryfall database.
                                   most commonly use "oracle_cards".
    """
    
    for i in range(len(card_names)):
        card = card_names[i]
        if card not in scryfall_names:
            found_name = next((s for s in scryfall_names if card in s), None)
            card_names[i] = found_name
    return card_names

def get_card_data(scryfall_df, card_list_paste=None,card_list_path=None):
    """Returns dataframe of cards from list of cards
       merged with data from scryfall pertaining to those cards.
       user either card_list_paste or card_list_path but not both.

    scryfall_df;     pandas dataframe -- dataframe of card data from scryfall.
                                    must includes columns: "name".
    card_list_paste; str -- cards listed and seperated by new lines.
                            Example: paste from MTGA and surround with triple quotes.
    card_list_path;  str -- path to .txt file of card names that are line seperated.
                            should be a raw string.
                            works with MTGO and MTGA formatted decklists, as well as 
                            most decklist website formats. 
    """

    if card_list_paste:
        card_list = card_list_paste.split('\n')
    elif card_list_path:
        card_list = open(card_list_path,'r').readlines()
        card_list = [c[:-1] for c in card_list]
    if (len(card_list) == 1 and not card_list[0][0].isdigit()) or (len(card_list) >1 and not card_list[1][0].isdigit()):
            card_list = ["1 " + card for card in card_list]


    else:
        raise Exception("Function input must include a pasted list or list file path.")

    if card_list[0].lower() == 'deck':
        card_list = card_list[1:]
    if "(" in card_list[0]:
        card_list = [card.split(" (")[0] for card in card_list]

    mb_cards = []
    mb_counts = []
    sb_cards = []
    sb_counts = []
    sb_check = False

    for line in card_list:
        if line == '' or line.lower() == "sideboard":
            sb_check = True
            continue

        data = line.split(' ', 1)
        if not sb_check:
            mb_cards.append(data[1])
            mb_counts.append(data[0])
        else:
            sb_cards.append(data[1])
            sb_counts.append(data[0])

    mb_cards = fix_names(mb_cards, list(scryfall_df.name))
    sb_cards = fix_names(sb_cards, list(scryfall_df.name))

    mb = [[mb_cards[i],int(mb_counts[i])] for i in range(len(mb_cards))]
    sb = [[sb_cards[i],int(sb_counts[i])] for i in range(len(sb_cards))]

    mb_df = pd.DataFrame(mb,columns=['name','counts'])
    sb_df = pd.DataFrame(sb,columns=['name','counts'])

    mb_df = mb_df.merge(scryfall_df, on='name')
    sb_df = sb_df.merge(scryfall_df, on='name')

    return((mb_df,sb_df))

### 
## working example case for get_cards_data
# from requests import get
# from json import loads

# oracle_cards = loads(get("https://api.scryfall.com/bulk-data/oracle-cards?format=file").text)
# wanted_cols = ['id', 'oracle_id', 'name', 'scryfall_uri', 'image_uris', 'mana_cost', 'cmc', 'type_line', 'oracle_text', 'card_faces', 'legalities', 'games', 'set_id', 'produced_mana']
# scryfall_df = pd.DataFrame(oracle_cards)[wanted_cols]

## use either path or paste
## path = r'my_file_path.txt'
# paste = """Deck
# 4 Atraxa, Grand Unifier (ONE) 196
# 1 Forest (ZEN) 248
# 1 Swamp (ZEN) 240
# 1 Island (ZEN) 236
# 1 Plains (ZEN) 232
# 3 Mountain (ZEN) 244

# Sideboard
# 1 Fblthp, the Lost (WAR) 50"""

# mb_df,sb_df = get_card_data(scryfall_df,card_list_paste=paste,card_list_path=None)
###

# example usage in tokens.py
def get_tokens(scryfall_df, card_list_paste=None,card_list_path=None):
    """Returns dataframe of aggregated token data and dataframe of parent card data.
       Use None in both card_list_ fields to use scryfall_df.name as the card list.

    scryfall_df;     pandas dataframe -- dataframe of card data from scryfall.
                                    must includes columns: "name","layout", "all_parts"
                                                           "color_identity".
    card_list_paste; str -- cards listed and seperated by new lines.
                            Example: paste from MTGA and surround with triple quotes.
    card_list_path;  str -- path to .txt file of card names that are line seperated.
                            should be a raw string.
                            works with MTGO and MTGA formatted decklists, as well as 
                            most decklist website formats. 
    """

    if card_list_paste or card_list_path:
        cards_dfs = get_card_data(scryfall_df, card_list_paste,card_list_path)
        #combining mainboard and sideboard into one dataframe
        card_pool = pd.concat([cards_dfs[0],cards_dfs[1]])
    else:
        card_pool = scryfall_df
    
    card_pool = card_pool[card_pool['layout'] != 'token']

    tokens = []
    for i in range(len(card_pool)):
        all_parts = card_pool.all_parts.iloc[i]
        parent_card_name = card_pool.name.iloc[i]
        parent_commander_identity = card_pool.color_identity.iloc[i]

        #filter out cards that don't have tokens
        if all_parts == all_parts:
            for part in all_parts:
                if part['component'] == 'token':
                    uri = part['uri']
                    token = loads(get(uri).text)
                    #filtering out double face cards
                    if 'image_uris' in token.keys():
                        token_properties = [parent_card_name,parent_commander_identity,token['name'],token['scryfall_uri'],token['image_uris']['png'],token['colors'],token['type_line']]
                        if 'power' in token.keys():
                            token_properties.append(token['power'])
                            token_properties.append(token['toughness'])
                        else:
                            #using placeholder value instead of None for groupby aggregation 
                            token_properties.append(-1)
                            token_properties.append(-1)
                        if 'oracle_text' in token.keys():
                            token_properties.append(token['oracle_text'])
                        #stupid fix for role tokens oracle text
                        elif 'card_faces' in token.keys():
                            for i, face in enumerate(token['card_faces']):
                                if i == 0:
                                    if 'oracle_text' in face.keys():
                                        oracle_text = face['oracle_text']
                                    else:
                                        oracle_text = "N/A"
                                else:
                                    if 'oracle_text' in face.keys():
                                        oracle_text += " // " + face['oracle_text']
                                    else:
                                        oracle_text += " // " + "N/A"
                            token_properties.append(oracle_text)
                        else:
                            token_properties.append("N/A")
                    #dealing with double faced cards
                    else:
                        for i, face in enumerate(token['card_faces']):
                            if i == 0:

                                if 'image_uris' in token.keys():
                                    img_uri = token['image_uris']['png']
                                else:
                                    img_uri = face['image_uris']['png']
                                colors = set()
                                if 'power' in face.keys():
                                    power = face['power']
                                    toughness = face['toughness']
                                else:
                                    #using placeholder value instead of None for groupby aggregation 
                                    power = -1
                                    toughness = -1

                                if 'oracle_text' in face.keys():
                                    oracle_text = face['oracle_text']
                                else:
                                    oracle_text = "N/A"
                            else:
                                oracle_text += " // " + face['oracle_text']
                            for c in face['colors']:
                                colors.add(c)
                        
                        token_properties = [parent_card_name,parent_commander_identity,token['name'],token['scryfall_uri'],
                                            img_uri,list(colors),token['type_line'],power,toughness,oracle_text]
                    tokens.append(token_properties)         
            
    #putting token parent cards into dataframe
    parents_df = pd.DataFrame(tokens,columns=['Parent_Card','Parent_Color_Identity','name','scryfall_uri','image_url','colors','type_line','power','toughness','oracle_text'])

    #creating unique color string token for groupby later
    colors_unique = []
    for i in range(len(parents_df)):
        colors = parents_df.colors.iloc[i]
        colors = sorted(colors)
        c = ""
        for val in colors:
            c+=val
        colors_unique.append(c)

    parents_df['colors_unique'] = colors_unique

    #aggregating data about all tokens
    tokens_agg = parents_df.groupby(['name','type_line','oracle_text','colors_unique','power','toughness'],group_keys=False).count().reset_index()[['name','type_line','oracle_text','colors_unique','power','toughness','scryfall_uri']]
    tokens_agg.rename(columns={'scryfall_uri':'counts'}, inplace=True)

    #REWRITE this section later lol
    W_Parent = []
    U_Parent = []
    B_Parent = []
    R_Parent = []
    G_Parent = []
    C_Parent = []
    for i in range(len(tokens_agg)):
        token = tokens_agg.iloc[i]
        #this should be a merge
        mask = [(parents_df['name'] == token['name']) & (parents_df['type_line'] == token['type_line']) & 
                (parents_df['oracle_text'] == token['oracle_text']) & (parents_df['colors_unique'] == token['colors_unique']) &
                (parents_df['power'] == token['power']) & (parents_df['toughness'] == token['toughness'])]
        parent_cards = parents_df[mask[0]].reset_index()
        color_counts_dict = {'W':0,'U':0,'B':0,'R':0,'G':0,'C':0}
        for j in range(len(parent_cards)):
            parent_colors = parent_cards.Parent_Color_Identity.iloc[j]
            if len(parent_colors) > 0:
                for c in parent_colors:
                    color_counts_dict[c] = color_counts_dict.get(c) + 1
            else:
                color_counts_dict['C'] = color_counts_dict.get('C') + 1

        W_Parent.append(color_counts_dict.get('W'))
        U_Parent.append(color_counts_dict.get('U'))
        B_Parent.append(color_counts_dict.get('B'))
        R_Parent.append(color_counts_dict.get('R'))
        G_Parent.append(color_counts_dict.get('G'))
        C_Parent.append(color_counts_dict.get('C'))

    tokens_agg['W_Parent_Counts'] = W_Parent
    tokens_agg['U_Parent_Counts'] = U_Parent
    tokens_agg['B_Parent_Counts'] = B_Parent
    tokens_agg['R_Parent_Counts'] = R_Parent
    tokens_agg['G_Parent_Counts'] = G_Parent
    tokens_agg['C_Parent_Counts'] = C_Parent

    return((tokens_agg,parents_df))


