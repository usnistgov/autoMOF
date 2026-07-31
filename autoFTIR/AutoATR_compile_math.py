# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.

"""

import pandas as pd
import glob

# Get all CSV files in the current directory for designated well
csv_files = glob.glob('*_004_*.csv')

# Create an empty list to store dataframes
df_list = []

# Loop through CSV files, read them into dataframes, and append to the list
def write_csv():
    for file in csv_files:
        df = pd.read_csv(file)
        df_list.append(df)
        


        print(df)

    # Concatenate all dataframes into one
        combined_df = pd.concat(df_list, axis = 1).T.drop_duplicates().T

    # Save the combined dataframe to a new CSV file
        combined_df.to_csv('combined-df_string_004.csv', index=False)

    # Read the CSV file into a pandas dataframe
        df = pd.read_csv('combined-df_string_004.csv')

    # subtract row 1 by row 2 to normalize data to baseline changes
        result = df.loc[238] - df.loc[208]

    # Create a new DataFrame from the result
        result_df = pd.DataFrame([result])

    # Write the result to a new CSV file
        result_df.to_csv('1310cmsub-norm_004-re.csv', index=True)

