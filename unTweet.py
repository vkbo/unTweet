#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import twitter
import logging

from os import path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def getTweets(twAPI=None, screenName=None):
    """Retrieve all tweets on timeline up to the maximum allowed number
    of tweets, 3200. The function is slightly modified from the
    python-twitter example script.
    """

    timeLine = twAPI.GetUserTimeline(screen_name=screenName, count=200)
    oldestTweet = min(timeLine, key=lambda x: x.id).id
    logger.info("Retrieved tweets up to ID %d (%d tweets)" % (oldestTweet, len(timeLine)))

    while True:
        moreTweets = twAPI.GetUserTimeline(screen_name=screenName, max_id=oldestTweet, count=200)
        newOldest = min(moreTweets, key=lambda x: x.id).id

        if not moreTweets or newOldest == oldestTweet:
            break
        else:
            oldestTweet = newOldest
            logger.info("Retrieved tweets up to ID %d (%d tweets)" % (oldestTweet, len(moreTweets)))
            timeLine += moreTweets

    logger.info("Retrieved %d tweets from Twitter API" % len(timeLine))

    returnData = {}
    for aTweet in timeLine:
        twData = aTweet._json
        if "id" in twData:
            returnData[twData["id"]] = twData

    return returnData

if __name__ == "__main__":

    # Options
    doDelete = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--delete":
            doDelete = True
        else:
            logger.error("Unknown option provided")
            sys.exit(1)

    # Load Settings
    rootPath = path.dirname(path.abspath(__file__))
    jsonFile = path.join(rootPath, "settings.json")
    with open(jsonFile, mode="r") as inFile:
        apiKeys = json.load(inFile)

    archPath = path.abspath(apiKeys["settings"]["archive_path"])

    # Set Up Logging
    logFmt = logging.Formatter(
        fmt="[{asctime:}]  {levelname:8}  {message:}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )
    fHandle = logging.FileHandler(path.join(archPath, "unTweet.log"))
    fHandle.setLevel(logging.DEBUG)
    fHandle.setFormatter(logFmt)
    logger.addHandler(fHandle)

    cHandle = logging.StreamHandler()
    cHandle.setLevel(logging.DEBUG)
    cHandle.setFormatter(logFmt)
    logger.addHandler(cHandle)

    logger.setLevel(logging.DEBUG)

    # Connect to API
    logger.info("Connecting to Twitter API")
    twAPI = twitter.Api(
        consumer_key        = apiKeys["api"]["api_key"],
        consumer_secret     = apiKeys["api"]["api_secret_key"],
        access_token_key    = apiKeys["api"]["access_token"],
        access_token_secret = apiKeys["api"]["access_token_secret"]
    )

    timeLine = getTweets(twAPI, apiKeys["settings"]["screen_name"])
    with open(path.join(archPath, "timeLineSnapshot.json"), mode="w+") as outFile:
        outFile.write(json.dumps(timeLine, indent=2))

    toDelete = []
    for twID in timeLine:
        theTweet = timeLine[twID]
        createdAt = theTweet["created_at"]
        timeStamp = datetime.strptime(createdAt, "%a %b %d %H:%M:%S %z %Y").replace(tzinfo=None)
        tweetAge = datetime.utcnow() - timeStamp
        if tweetAge.days > apiKeys["settings"]["max_age"]:
            toDelete.append(twID)
            logger.info("Will delete tweet %s from %s (%d days old)" % (twID, createdAt, tweetAge.days))

    logger.info("%d tweets scheduled for deletion" % len(toDelete))
    archFile = "archivedTweets_%s.json" % datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archData = {}
    for delID in toDelete:
        archData[delID] = timeLine[delID]
    if archData:
        if doDelete:
            try:
                with open(path.join(archPath, archFile), mode="w+") as outFile:
                    outFile.write(json.dumps(archData, indent=2))
            except Exception as e:
                logger.critical("Could not write archive file. Aborting.")
                logger.critical(str(e))
                sys.exit(1)
    else:
        logger.info("Nothing to delete.")
        sys.exit(0)

    if doDelete:
        for delID in toDelete:
            theTweet = timeLine[delID]
            createdAt = theTweet["created_at"]
            logger.info("Deleting tweet %s from %s" % (delID, createdAt))
            try:
                twAPI.DestroyStatus(delID, True)
            except Exception as e:
                logger.error("Failed to delete tweet")
                logger.error(str(e))

        logger.info("Deleted %d tweets" % len(toDelete))

    else:
        logger.info("No delete option provided. Skipping deleting.")

    sys.exit(0)
