### Terminals (order): michael, riley, kensho

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from require import require

import pandas as pd
import numpy as np
import sklearn as sk
import pyarrow as pa
#import gdown

print("Code Running:")
sales_df = pd.read_parquet('./HackBRASA/backend/data/hackathon_stone_brasa_sales_data.parquet')
#bank_df = pd.read_parquet('./data/hackathon_stone_brasa_banking_data.parquet')
#mcc_df = pd.read_parquet('./data/mcc.parquet')

sales_df.head()
#bank_df.head()
#mcc_df.head()


#1 See if sales and bank dataframes share any id's

# Check if there are any shared IDs
#shared_ids = sales_df['id'].isin(bank_df['id'])

# Get the actual shared IDs
#shared_ids_list = sales_df[sales_df['id'].isin(bank_df['id'])]['id'].unique()

#print("Shared IDs:", shared_ids_list)

#2 Perform a left join of the MCC dictionary into sales dataframe on shared column 'mcc'
#merged_df = pd.merge(mcc_df, sales_df, on="mcc", how="left")

# Perform a left join of the MCC dictionary (mcc_df) into sales_df on the 'mcc' column
#sales_with_mcc_df = pd.merge(sales_df, mcc_df, on='mcc', how='left')

# Display the resulting DataFrame
#print(sales_with_mcc_df.head())


'''
TO DO:
1. See if sales and bank dataframes share any id's
2. Perform a left join of the MCC dictionary into sales dataframe on shared column 'mcc'
'''

