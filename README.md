# twitter-likes-archiver

A Docker image which allows exporting twitter likes in json and sqlite format.
Automatically picks-up where it left off with tweets that were previously saved,
so can be run as a cron.

## Example
```bash
docker run --rm -it \
    -v $(pwd):/output \
    ghcr.io/jwoglom/twitter-likes-archiver/twitter-likes-archiver \
    --consumer-key=xxx \
    --consumer-secret=xxx \
    --bearer-token=xxx \
    --user-id=1234 \
    --json-output-file=/output/tweets.json
```

## License
MIT