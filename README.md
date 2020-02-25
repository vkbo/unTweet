# unTweet

Simple Python script to delete tweets over a certain age.
Due to limitations in the Twitter API, it is not possible to delete tweets older than 3200 tweets back in time.

The script will keep a snapshot of your Twitter timeline in a `timeLineSnapshot.json` file.
This file is replaced every time the script is run.
Deleted tweets are copied to a file named `archivedTweets_[date].json` where `[date]` is the current date and time.

To configure the script, copy `settings_sample.json` to `settings.json`, and provide your Twitter screen name, the maximum allowed age of tweets in days, and the path where you want the logfile and archives of old tweets to be written.

You must also provide Twitter API keys.
The script depends on the Python `twitter` package, which has a description of how to get these keys in their [documentation](https://python-twitter.readthedocs.io/en/latest/getting_started.html).

The script is run by typing
```
python3 unTweet.py
```
This will run the script in test mode, and no tweets are actually deleted, but all tweets scheduled for deletion will be listed.

To delete the tweets, run the script again with the `--delete` option:
```
python3 unTweet.py --delete
```

## Disclaimer

This script permanently deletes content from your Twitter timeline.
This cannot be undone.
Use this script at your own risk.

If you want to be extra careful, always run it without `--delete` first before running it with delete mode to ensure tweets are not accidentally deleted.
