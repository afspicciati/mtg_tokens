import pandas as pd
from requests import get
from json import loads
## needed for pasting in from clipboard
# from functions import get_card_data
from functions import get_tokens

#using full scryfall database as our source for aggregate token statistics
oracle_cards = loads(get("https://api.scryfall.com/bulk-data/oracle-cards?format=file").text)
scryfall_df_ = pd.DataFrame(oracle_cards)

#takes ~10 minutes to run
#all_tokens = get_tokens(scryfall_df=scryfall_df_,card_list_paste=None,card_list_path=None)
#all_tokens[0].to_csv('csv_out/all_tokens.csv')

token_cube_tokens = get_tokens(scryfall_df=scryfall_df_,card_list_paste=None,card_list_path=r'Tokens\TokenCube.txt')
token_cube_tokens[0].to_csv(r'Tokens\csv_out\token_cube.csv')
