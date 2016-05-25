# A quick Python module to obtain stock quotes.
#
# Copyright 1999 Eklektix, Inc.  This sofware is freely distributable under
# the terms of the GNU Library General Public Licence (LGPL).
#
# Written by Jonathan Corbet, corbet@eklektix.com.  Current version is available
# at ftp.eklektix.com/pub/Quote.
#
# $Id: Quote.py,v 1.1.1.1 2014/03/21 04:06:34 jkeezel Exp $
#
# Basic usage is:
#
#       quote = Quote.Lookup (symbol)
#
# where 'symbol' is the stock symbol.  The return value is an instance of the
# Quote class, which has the following attributes:
#
#	symbol		The stock symbol for which the quote applies
#	name		The name of the company
#	time		Time of last trade (internal unix format)
#	value		The current value of the stock
#	change		Change in value since market opening
#	open		Opening value of the stock
#	previous_close	Previous day's closing value
#	percent_change	Percentage change in value of the stock
#	high		Today's high value
#	low		Today's low value
#	volume		Trading volume in shares
#	market_cap	Market capitalization, in millions of dollars
#	year_high	Highest value in last year
#	year_low	Lowest value in last year
#	eps		Earnings per share
#	pe_ratio	Price to earnings ratio (-1 if no earnings)
#
# In case of errors (which happens, web server doesn't always respond) None is
# returned. 
#
# Currently this module only works with quote.yahoo.com.  Future plans involve
# making it work with other web quote services as well...
#
import urllib
import string
import time

#
# Here is the Quote class that we return.  Pretty boring...
#
class Quote:
    pass

#
# The function that actually does quote lookups.
#
def Lookup (symbol):
    (qurl, decoder) = MakeUrl (symbol)
    response = urllib.urlopen (qurl)
    q = Quote ()
    if decoder (q, response):
	return q
    return None

#
# Internal stuff below.
#

#
# Yahoo: create a URL to look up a stock quote.
#
def MakeYahooURL (symbol):
    #qurl = 'http://quote.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgvj1pp2owern&e=.csv' \
    qurl = 'http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgvj1pp2owern&e=.csv' \
	   % (symbol)
    return (qurl, DecYahooUrl)

#
# Yahoo: Decode a response to a Yahoo stock lookup.
#
def DecYahooUrl (q, response):
    #
    # Pull the info from the server, split it, and make sure it makes sense.
    #
    info = response.readline ().strip() # Get rid of CRLF
    sinfo = string.split (info, ',')
    if len (sinfo) < 15:
	return 0
    #
    # Start decoding.
    #
    #print sinfo
    q.symbol = sinfo[0][1:-1]
    q.value = float(sinfo[1])
    q.time = YahooDate (sinfo[2], sinfo[3])
    q.change = float(sinfo[4])
    try:
	q.open = float(sinfo[5])
    except ValueError:
	q.open = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.high = float(sinfo[6])
    except ValueError:
	q.high = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.low = float(sinfo[7])
    except ValueError:
	q.low = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.volume = int(sinfo[8])
    except ValueError:
	q.volume = -1 # Yahoo returns "N/A" for Mutual Fund
    #
    # Get the market cap into millions
    #
    try:
	q.market_cap = float(sinfo[9][:-1])
    except ValueError:
	q.market_cap = 0.0  # Weirdness happens
    if sinfo[9][-1] == 'B':
	q.market_cap = q.market_cap*1000
    q.previous_close = float(sinfo[10])
    q.percent_change = float(sinfo[11][1:-2])  # Zap training %
    try:
	q.open = float(sinfo[12])
    except ValueError:
	q.open = -1 # Yahoo returns "N/A" for Mutual Fund
    #
    # Pull apart the range.
    #
    range = string.split (sinfo[13][1:-1], '-')
    try:
	q.year_low = float(range[0])
    except ValueError:
	q.year_low = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.year_high = float(range[1])
    except ValueError:
	q.year_high = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.eps = float(sinfo[14])
    except ValueError:
	q.eps = -1 # Yahoo returns "N/A" for Mutual Fund
    try:
	q.pe_ratio = float(sinfo[15])
    except ValueError:
	q.pe_ratio = -1  # Yahoo returns "N/A" for no earnings.
    q.name = sinfo[16][1:-1]
    #
    # We made it.
    #
    return 1

#
# Convert date/times in Yahoo's format into an internal time.
#
def YahooDate (date, tod):
    #
    # Date part is easy.
    #
    sdate = string.split (date[1:-1], '/')
    month = int(sdate[0])
    day = int(sdate[1])
    year = int(sdate[2])
    #
    # Pick apart the time.
    #
    stime = string.split (tod[1:-1], ':')
    hour = int(stime[0])
    minute = int(stime[1][0:2])
    if stime[1][-2:] == 'PM':
	hour = hour + 12
    #
    # Time to assemble everything.
    #
    ttuple = (year, month, day, hour, minute, 0, 0, 0, -1)
    return time.mktime (ttuple)


#
# Create a URL to look somebody up.  Returns a tuple with the URL and
# a function to decode the result.  Someday this will handle multiple
# sources, but currently it only knows yahoo.
#
def MakeUrl (symbol):
    return MakeYahooURL (symbol)


