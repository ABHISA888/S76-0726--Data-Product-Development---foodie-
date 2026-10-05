"""
PeakPulse — Food Delivery SLA Insights
SQL Query Runner

Executes analytical queries from sql/queries.sql against the SQLite database
(data/peakpulse.db) and displays readable tabular results.
"""

import sqlite3
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.config import DB_PATH, SQL_QUERIES_PATH


def ensure_database():
    """Ensure SQLite database exists with deliveries table."""
    if not DB_PATH.exists():
        print(f"[INFO] Database not found at {DB_PATH}. Generating from cleaned data...")
        from config.config import PROCESSED_DATA_PATH
        if not PROCESSED_DATA_PATH.exists():
            from src.data_cleaning import main as run_cleaning
            run_cleaning()
        
        df = pd.read_csv(PROCESSED_DATA_PATH)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("deliveries", conn, if_exists="replace", index=False)
        conn.close()
        print(f"[INFO] Initialized {DB_PATH} with {len(df):,} rows.")


def execute_queries():
    """Parse and execute all numbered queries in sql/queries.sql."""
    ensure_database()
    
    with open(SQL_QUERIES_PATH, "r") as f:
        content = f.read()
    
    # Split queries by double dashes numbering
    raw_queries = content.split(";\n")
    conn = sqlite3.connect(DB_PATH)
    
    print("=" * 70)
    print("           PEAKPULSE SQL ANALYTICS QUERY EXECUTION")
    print("=" * 70)
    
    query_num = 1
    for raw in raw_queries:
        clean_q = raw.strip()
        if not clean_q or not any(kw in clean_q.upper() for kw in ["SELECT"]):
            continue
            
        # Extract title from comments if available
        title = f"Query {query_num}"
        for line in clean_q.splitlines():
            if line.startswith("-- ") and not line.startswith("-- ==") and not line.startswith("-- --"):
                title = line.replace("--", "").strip()
                break
                
        print(f"\n>>> [{query_num}] {title}")
        print("-" * 70)
        try:
            result_df = pd.read_sql_query(clean_q, conn)
            print(result_df.to_string(index=False))
            query_num += 1
        except Exception as e:
            print(f"[ERROR] Failed executing query: {e}")
            
    conn.close()
    print("\n" + "=" * 70)
    print("               SQL EXECUTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    execute_queries()
