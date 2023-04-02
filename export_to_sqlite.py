#!/usr/bin/env python3
import pandas as pd
import numpy as np

import argparse
import sqlite3
import json

def export_to_sqlite(json_file, output_file, if_exists='replace'):
    df = pd.json_normalize(json.loads(open(json_file).read()))
    df = df.astype(str)
    df[['id', 'author_id', 'conversation_id']] = df[['id', 'author_id', 'conversation_id']].astype(int)
    df['created_at'] = pd.to_datetime(df['created_at'])

    conn = sqlite3.connect(output_file)
    df.to_sql('tweets', conn, if_exists=if_exists)
    conn.close()

def export_usernames_to_sqlite(usernames, output_file, if_exists='replace'):
    username_rows = []
    for k, v in usernames.items():
        username_rows.append({"id": k, "username": v})
    df = pd.json_normalize(username_rows)

    conn = sqlite3.connect(output_file)
    df.to_sql('users', conn, if_exists=if_exists)
    conn.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Converts a JSON file containing twitter likes into a sqlite3 database")
    ap.add_argument('--json-input-file', default='tweets.json')
    ap.add_argument('--sqlite-output-file', default='tweets.sqlite3')
    ap.add_argument('--if-exists', default='replace')
    args = ap.parse_args()

    export_to_sqlite(args.json_input_file, args.sqlite_output_file, if_exists=args.if_exists)
