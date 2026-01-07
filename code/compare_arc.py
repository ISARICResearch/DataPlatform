# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:02:16 2025

@author: sduquevallejo
"""

import pandas as pd

# Define versions
old_version = '1.1.5'
new_version = '1.1.6'

# Load the two files
file_old = f"C:/Users/sduquevallejo/OneDrive - Nexus365/Documents/GitHub/DataPlatform/ARCH/ARCH{old_version}/ARCH.csv"  # OLD file
file_new = f"C:/Users/sduquevallejo/OneDrive - Nexus365/Documents/GitHub/DataPlatform/ARCH/ARCH{new_version}/ARCH.csv"  # NEW file

df_old = pd.read_csv(file_old)
df_new = pd.read_csv(file_new)

# Remove rows where Form == "pregnancy" or "neonate"
#df_old = df_old[(df_old['Form'] != 'pregnancy') & (df_old['Form'] != 'neonate')]
#df_new = df_new[(df_new['Form'] != 'pregnancy') & (df_new['Form'] != 'neonate')]

# Focus on important columns including Form and Section
cols_of_interest = ['Variable', 'Form', 'Section', 'Question', 'Answer Options']
df_old_sub = df_old[cols_of_interest]
df_new_sub = df_new[cols_of_interest]

# Set index on Variable for easier comparison
df_old_indexed = df_old_sub.set_index('Variable')
df_new_indexed = df_new_sub.set_index('Variable')

# Function to normalize Answer Options by sorting them
def normalize_answer_options(text):
    """Normalize Answer Options: split, strip, sort, and rejoin."""
    if pd.isna(text):
        return ''
    options = [opt.strip() for opt in text.split('|')]
    options.sort()
    return ' | '.join(options)

# 1. Find Deleted and Added Variables
deleted_variables = set(df_old_indexed.index) - set(df_new_indexed.index)
added_variables = set(df_new_indexed.index) - set(df_old_indexed.index)

# 2. Find Variables with the same Variable name but different Question or Answer Options
common_variables = set(df_old_indexed.index) & set(df_new_indexed.index)

changed_variables = []
for var in common_variables:
    old_question = df_old_indexed.loc[var, 'Question']
    new_question = df_new_indexed.loc[var, 'Question']
    old_answer_options = normalize_answer_options(df_old_indexed.loc[var, 'Answer Options'])
    new_answer_options = normalize_answer_options(df_new_indexed.loc[var, 'Answer Options'])
    
    if  (old_question != new_question and old_answer_options != new_answer_options) or (old_answer_options != new_answer_options):
        changed_variables.append(var)

# 3. Find Variables with same Form, Section, Question and Answer Options but different Variable name (Renamed)
merged_df = pd.merge(
    df_old_sub, df_new_sub,
    on=['Form', 'Section', 'Question', 'Answer Options'],
    how='inner',
    suffixes=('_old', '_new')
)

variable_renamed = merged_df[merged_df['Variable_old'] != merged_df['Variable_new']]

# Separate real content changes from renamed variables
renamed_old_variables = variable_renamed['Variable_old'].tolist()
renamed_new_variables = variable_renamed['Variable_new'].tolist()

# Real content changes are those not involved in a rename
real_content_changes = list(set(changed_variables) - set(renamed_old_variables))

# Create a detailed Content Changes DataFrame
content_changes_records = []

for var in real_content_changes:
    record = {
        "Variable": var,
        "Old Question": df_old_indexed.loc[var, 'Question'],
        "New Question": df_new_indexed.loc[var, 'Question'],
        "Old Answer Options": df_old_indexed.loc[var, 'Answer Options'],
        "New Answer Options": df_new_indexed.loc[var, 'Answer Options']
    }
    content_changes_records.append(record)

content_changes_df = pd.DataFrame(content_changes_records)

# 4. Correct Deleted and Added Variables (remove replaced variables)
deleted_variables_corrected = deleted_variables - set(renamed_old_variables)
added_variables_corrected = added_variables - set(renamed_new_variables)

# 5. Prepare all DataFrames for Excel export

# For added variables: include Form, Section, Question, Answer Options
added_records = df_new_sub[df_new_sub['Variable'].isin(added_variables_corrected)].copy()
added_variables_df = added_records.rename(columns={
    'Variable': 'Variable (New)',
    'Form': 'Form (New)',
    'Section': 'Section (New)',
    'Question': 'Question (New)',
    'Answer Options': 'Answer Options (New)'
})

# For deleted variables: include Form, Section, Question, Answer Options
deleted_records = df_old_sub[df_old_sub['Variable'].isin(deleted_variables_corrected)].copy()
deleted_variables_df = deleted_records.rename(columns={
    'Variable': 'Variable (Old)',
    'Form': 'Form (Old)',
    'Section': 'Section (Old)',
    'Question': 'Question (Old)',
    'Answer Options': 'Answer Options (Old)'
})

# For variable replacements
variable_replacements_df = pd.DataFrame({
    f"Old Variable ({old_version})": renamed_old_variables,
    f"New Variable ({new_version})": renamed_new_variables
})

# 6. Create the final Excel
final_corrected_output_path = f"C:/Users/sduquevallejo/OneDrive - Nexus365/Documents/GitHub/DataPlatform/ARCH/ARCH{new_version}/ARCH{new_version}_ChangesLOG.xlsx"

with pd.ExcelWriter(final_corrected_output_path) as writer:
    added_variables_df.to_excel(writer, index=False, sheet_name='Added Variables')
    deleted_variables_df.to_excel(writer, index=False, sheet_name='Deleted Variables')
    content_changes_df.to_excel(writer, index=False, sheet_name='Content Changes')
    variable_replacements_df.to_excel(writer, index=False, sheet_name='Variable Replacements')

print(f"Excel file generated at: {final_corrected_output_path}")
