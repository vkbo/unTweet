#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import twitter
import logging

from os import path
from datetime import datetime

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
            logger.info(
                "Retrieved tweets up to ID %d (%d tweets)" % (oldestTweet, len(moreTweets))
            )
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

    try:
        apiKey = apiKeys["api"]["api_key"]
        apiSecretKey = apiKeys["api"]["api_secret_key"]
        apiAccessToken = apiKeys["api"]["access_token"]
        apiSecretAccessToken = apiKeys["api"]["access_token_secret"]
    except Exception as e:
        logger.error("Could not read API keys from settings.json")
        logger.error(str(e))
        sys.exit(1)

    try:
        screenName = apiKeys["settings"]["screen_name"]
        archPath = path.abspath(apiKeys["settings"]["archive_path"])
        maxAge = apiKeys["settings"]["max_age"]
        minCount = apiKeys["settings"]["min_count"]
    except Exception as e:
        logger.error("Could not read user settings from settings.json")
        logger.error(str(e))
        sys.exit(1)

    # Set Up Logging
    logFmt = logging.Formatter(
        fmt="[{asctime:}]  {levelname:8}  {message:}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )
    cHandle = logging.StreamHandler()
    cHandle.setLevel(logging.DEBUG)
    cHandle.setFormatter(logFmt)
    logger.addHandler(cHandle)

    if doDelete:
        # Only write to log file when deleting
        fHandle = logging.FileHandler(path.join(archPath, "unTweet.log"))
        fHandle.setLevel(logging.DEBUG)
        fHandle.setFormatter(logFmt)
        logger.addHandler(fHandle)

    logger.setLevel(logging.DEBUG)

    # Connect to API
    logger.info("Connecting to Twitter API")
    twAPI = twitter.Api(
        consumer_key = apiKey,
        consumer_secret = apiSecretKey,
        access_token_key = apiAccessToken,
        access_token_secret = apiSecretAccessToken
    )

    timeLine = getTweets(twAPI, screenName)
    with open(path.join(archPath, "timeLineSnapshot.json"), mode="w+") as outFile:
        outFile.write(json.dumps(timeLine, indent=2))

    toDelete = []
    for twNum, twID in enumerate(timeLine):
        theTweet = timeLine[twID]
        createdAt = theTweet["created_at"]
        timeStamp = datetime.strptime(createdAt, "%a %b %d %H:%M:%S %z %Y").replace(tzinfo=None)
        tweetAge = datetime.utcnow() - timeStamp
        if tweetAge.days > maxAge and twNum >= minCount:
            toDelete.append(twID)
            logger.info(
                "Will delete tweet #%d (%s) from %s (%d days old)" % (
                    twNum+1, twID, createdAt, tweetAge.days
                )
            )

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
