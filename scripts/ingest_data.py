#!/usr/bin/env python3
"""
Data ingestion script for Decision Intelligence Assistant.
Ingests tweets from CSV into the vector database via the API.
"""

import sys
import argparse
from pathlib import Path
import requests
from tqdm import tqdm
import pandas as pd


API_URL = "http://localhost:8000"
BATCH_SIZE = 100


def ingest_batch(api_url: str, tickets: list) -> bool:
    """Send a batch of tickets to the API."""
    resp = requests.post(
        f"{api_url}/tickets/ingest-batch",
        json={"tickets": tickets}   # ✅ wrap in dict
    )
    if resp.status_code != 200:
        print(f"Batch failed: {resp.status_code} {resp.text}")
        return False
    return True



def main():
    parser = argparse.ArgumentParser(description="Ingest customer support tweets into the vector database.")
    parser.add_argument("csv_path", help="Path to customer_support_tweets.csv")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for ingestion")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to ingest")
    parser.add_argument("--api-url", default=API_URL, help="Backend API URL")
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)

    # Load data
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)

    if args.limit:
        df = df.head(args.limit)

    total = len(df)
    print(f"Total tweets to ingest: {total}")

    # Verify backend is reachable
    try:
        health = requests.get(f"{args.api_url}/health", timeout=5)
        if health.status_code != 200:
            raise ConnectionError
    except Exception:
        print(f"Error: Backend at {args.api_url} is not reachable.")
        print("Make sure Docker Compose is up: docker compose up -d")
        sys.exit(1)

    # Ingest in batches
    success_count = 0
    for i in tqdm(range(0, total, args.batch_size), desc="Ingesting"):
        batch_df = df.iloc[i:i+args.batch_size]
        tickets = []
        for idx, row in batch_df.iterrows():
            # Determine tweet_id column
            tweet_id = str(row.get('tweet_id', idx))
            text = str(row['text'])
            author_id = str(row.get('author_id', ''))
            created_at = str(row.get('created_at', ''))
            inbound = bool(row.get('inbound', True))

            tickets.append({
                "tweet_id": tweet_id,
                "text": text,
                "author_id": author_id,
                "created_at": created_at,
                "inbound": inbound
            })

        if ingest_batch(args.api_url, tickets):
            success_count += len(tickets)

    print(f"\n✓ Successfully ingested {success_count}/{total} tweets")
    print(f"  You can now query at http://localhost:3000")

    # Show ticket count
    try:
        count_resp = requests.get(f"{args.api_url}/tickets/count")
        print(f"  Total tickets in vector DB: {count_resp.json().get('count', 'unknown')}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
