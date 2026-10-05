import pandas as pd

pd.set_option("display.max_columns", None)

# Location of our raw dataset
file_path = "data/raw/Zomato Dataset.csv"

# Load the CSV
df = pd.read_csv(file_path)

print("========== BASIC INFORMATION ==========")
print("Number of rows:", df.shape[0])
print("Number of columns:", df.shape[1])

print("\n========== FIRST 5 ROWS ==========")
print(df.head())

print("\n========== DATA TYPES ==========")
print(df.dtypes)

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

print("\n========== DUPLICATE ROWS ==========")
print("Number of duplicate rows:", df.duplicated().sum())

print("\n========== NUMERICAL SUMMARY ==========")
print(df.describe())