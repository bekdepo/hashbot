#!/usr/bin/env python

from __future__ import print_function

import requests
import json
import time
import re

from oauth_hook import OAuthHook


try:
    import config
    credentials = config.oauth_credentials
    r_config = config.r_config
except:
    print("Can't find a config.py file. Consider creating one !")
    credentials = { 'access_token' : "", 'access_token_secret': "",
            'consumer_key' : "", 'consumer_secret' : "", }
    r_config = {}


oauth_hook = OAuthHook(credentials['access_token'], credentials['access_token_secret'],
        credentials['consumer_key'], credentials['consumer_secret'], True)

def filter_tweet(tweet_text):
    matcher = re.compile(r"""
            \b # Beginning of word
            (
                ([a-f0-9]{32})| # md5
                ([a-f0-9]{40})| # sha1
                ([a-f0-9]{64}) # sha256
            )
            \b(?!:) # end of word except ':'
            """, re.VERBOSE|re.UNICODE|re.IGNORECASE)
    if matcher.search(tweet_text):
        return True
    else:
        return False

def retweet(tweet_id):
    r = requests.post("https://api.twitter.com/1/statuses/retweet/"+tweet_id+".json",
            config=r_config,
            hooks={'pre_request': oauth_hook })
    if r.status_code != 200:
        print("Attempted to retweet tweet %s"%tweet_id)
        print("Response status: %s"%r.status_code)
        print("Response error: %s"%r.error)
        print("Response text: %s"%json.dumps(json.loads(r.text), indent=4))
    else:
        print("Successfully retweeted tweet %s."%tweet_id)

class RateCounter:
    def __init__(self):
        self._interval=1000.
        self._i=0
        self._t=time.clock()
    def increment(self):
        self._i+=1
        #print(".", end="")
        if (self._i%self._interval== 0):
            self._t1=time.clock()
            print("%d tweets per second"%(self._interval/(self._t1-self._t),))
            self._t=self._t1

twitter_sample_parameters = {
        'stall_warnings': 'true',
        }

def bot_main():
    # Twitter stream API on the "sample" feed
    # twitter pretends it gives ~1% of the tweet at a given time, I think it's much lower
    # they must adapt its verbosity/rate level to load.
    r = requests.post('https://stream.twitter.com/1/statuses/sample.json',
            data=twitter_sample_parameters,
            config=r_config,
            hooks={'pre_request': oauth_hook })

    c = RateCounter()

    for line in r.iter_lines():
        if line: # filter out keep-alive new lines
            text = str(line)
            tweet = json.loads(text)
            if 'user' in tweet and 'screen_name' in tweet['user'] and 'text' in tweet:
                #print(tweet['user']['screen_name'] +": " + tweet['text'])
                if filter_tweet(tweet['text']): # we could be (much?) faster by filtering before loading json
                    print("Matched tweet!")
                    print(tweet['text'])
                    #print(json.dumps(tweet, indent=4))
                    retweet(tweet['id_str'])
                pass
            else:
                #print(json.dumps(tweet, indent=4))
                pass
            if 'warning' in tweet:
                print("==== WARNING !!! ====")
                print(json.dumps(tweet, indent=4))
                print("==== WARNING !!! ====")

            c.increment()

if  __name__ == '__main__':
    bot_main()
