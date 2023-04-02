#!/usr/bin/env python3
import tweepy
import requests
import json
import time
import argparse
import os

def main(args):
    if not args.user_id:
        print("No --user-id specified")
        exit(1)

    if not args.consumer_key or not args.consumer_secret:
        print("No --consumer-key or --consumer-secret")
        exit(1)

    if not args.bearer_token:
        print("No --bearer-token")
        exit(1)

    apiv2=tweepy.Client(
        consumer_key=args.consumer_key,
        consumer_secret=args.consumer_secret,
        bearer_token=args.bearer_token
    )

    def get_tweets(apiv2, **kwargs):
        return apiv2.get_liked_tweets(int(args.user_id), 
            media_fields=['media_key','url','type','duration_ms','preview_image_url','alt_text','variants'], 
            place_fields=['full_name','id','contained_within','country','country_code','geo','name','place_type'], 
            poll_fields=['id','options','duration_minutes','end_datetime','voting_status'], 
            tweet_fields=['id','text','edit_history_tweet_ids','attachments','author_id','context_annotations','conversation_id','created_at','edit_controls','entities','in_reply_to_user_id','lang','public_metrics','referenced_tweets','reply_settings','source','withheld'],
            user_fields=['id','name','username','created_at','description','entities','location','pinned_tweet_id','profile_image_url','protected','public_metrics','url','verified','withheld'],
            **kwargs)

    if args.pagination_token:
        print("Using pagination token", args.pagination_token)
        l = get_tweets(apiv2, pagination_token=args.pagination_token)
    else:
        l = get_tweets(apiv2)

    items = []
    if os.path.exists(args.json_output_file):
        items = json.loads(open(args.json_output_file, "r").read())
    seen_ids = set(map(lambda x: x['id'], items))

    total_added = 0
    exceptions = 0
    while l and l.data:
        added_cycle = 0
        for item in l.data:
            if item.data['id'] not in seen_ids:
                items.append(item.data)
                seen_ids.add(item.data['id'])
                added_cycle += 1

        if added_cycle == 0:
            print("Nothing more to download")
            post_fetch(args, items)
            exit(0)

        total_added += added_cycle
        print('Found %d new tweets (%d so far, %d total)' % (added_cycle, total_added, len(items)))

        open(args.json_output_file, "w").write(json.dumps(items, default=str))

        print(l.meta, len(items))
        if 'next_token' not in l.meta:
            break
        next_token = l.meta['next_token']
        old_l = l
        while True:
            try:
                print('getting tweets')
                l = get_tweets(apiv2, pagination_token=next_token)
                break
            except tweepy.errors.TooManyRequests as e:
                print(e)
                print('ratelimit: sleeping for %d sec' % args.ratelimit_sleep_time)
                time.sleep(args.ratelimit_sleep_time)
            except Exception as e:
                print(e)
                print('other error: sleeping for %d sec' % args.sleep_time)
                time.sleep(args.sleep_time)
                l = old_l
                exceptions += 1
                if exceptions > 3:
                    print('too many errors -- quitting')
                    exit(1)

        if not l:
            print('no l!', l)
        if not l.data:
            print('no l.data!', l.data, l.meta, l)

        print('loop: sleeping %d sec' % args.sleep_time)
        time.sleep(args.sleep_time)
        
    post_fetch(args, items)

def get_username_from_id(id):
    r = requests.post('https://tweeterid.com/ajax.php', data={'input': str(id)})
    if r.status_code == 200:
        username = r.text.strip()
        if username.startswith('@'):
            return username[1:]
    return None


def post_fetch(args, items):
    if args.json_usernames_output_file:
        print("Getting usernames")
        id_to_username = {}
        if os.path.exists(args.json_usernames_output_file):
            id_to_username = json.loads(open(args.json_usernames_output_file, 'r').read())
        item_author_ids = set(map(lambda x: x['author_id'], items))
        fetched_usernames = 0
        for id in item_author_ids:
            if not id in id_to_username:
                fetched_usernames += 1
                username = get_username_from_id(id)
                if username:
                    id_to_username[id] = username
                print("  fetched %s" % username)
        
        open(args.json_usernames_output_file, "w").write(json.dumps(id_to_username))
        
        print("Fetched %d usernames" % fetched_usernames)

    if args.sqlite_output_file:
        print("Converting to sqlite")
        from export_to_sqlite import export_to_sqlite, export_usernames_to_sqlite
        export_to_sqlite(args.json_output_file, args.sqlite_output_file, args.sqlite_if_exists)
        if args.json_usernames_output_file:
            id_to_username = json.loads(open(args.json_usernames_output_file, 'r').read())
            export_usernames_to_sqlite(id_to_username, args.sqlite_output_file, args.sqlite_if_exists)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Downloads twitter likes for the given user into a JSON file")
    ap.add_argument('-t', '--pagination-token', type=str)
    ap.add_argument('--consumer-key', default=os.getenv('CONSUMER_KEY'))
    ap.add_argument('--consumer-secret', default=os.getenv('CONSUMER_SECRET'))
    ap.add_argument('--bearer-token', default=os.getenv('BEARER_TOKEN'))
    ap.add_argument('--user-id', default=os.getenv('USER_ID'))
    ap.add_argument('--json-output-file', default='tweets.json')
    ap.add_argument('--json-usernames-output-file', default=None)
    ap.add_argument('--sqlite-output-file', default=None)
    ap.add_argument('--sqlite-if-exists', default='replace')
    ap.add_argument('--sleep-time', type=int, default=10)
    ap.add_argument('--ratelimit-sleep-time', type=int, default=60)
    args = ap.parse_args()

    main(args)
