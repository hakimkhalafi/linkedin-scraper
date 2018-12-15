#!/usr/bin/python
import os
import sys
import json
import urllib
from bs4 import BeautifulSoup
import urllib.request as urllib2
import http.cookiejar as cookielib

with open('../config.json') as config_file:
    config = json.load(config_file)


def linkedin():
        global opener
        cookie_filename = "cookies.txt"

        # Simulate browser with cookies enabled
        cj = cookielib.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            cj.load()

        # Load Proxy settings
        if len(config['proxylist']) > 0:
            proxy_handler = urllib2.ProxyHandler(
                {'https': config['proxylist'][0]})

            opener = urllib2.build_opener(
                proxy_handler,
                urllib2.HTTPRedirectHandler(),
                urllib2.HTTPHandler(debuglevel=0),
                urllib2.HTTPSHandler(debuglevel=0),
                urllib2.HTTPCookieProcessor(cj)
            )
        else:
            opener = urllib2.build_opener(
                urllib2.HTTPRedirectHandler(),
                urllib2.HTTPHandler(debuglevel=0),
                urllib2.HTTPSHandler(debuglevel=0),
                urllib2.HTTPCookieProcessor(cj)
            )

        user_agent = config['cookie']['User-Agent']

        opener.addheaders = [('User-Agent', user_agent)]

        # Get CSRF Token
        html = load_page("https://www.linkedin.com/")
        soup = BeautifulSoup(html, "html.parser")
        csrf = soup.find(id="loginCsrfParam-login")['value']

        # Authenticate
        login_data = urllib.urlencode({
            'session_key': config['username'],
            'session_password': config['password'],
            'loginCsrfParam': csrf,
        })

        html = load_page("https://www.linkedin.com/uas/login-submit", login_data)
        soup = BeautifulSoup(html, "html.parser")

        try:
            print(cj._cookies['.www.linkedin.com']['/']['li_at'].value)

        except Exception:
            print("error")

        cj.save()
        os.remove(cookie_filename)


def load_page(url, data=None):
        try:
            response = opener.open(url)
        except Exception:
            print("\n[Fatal] Your IP may have been temporarily blocked")

        try:
            if data is not None:
                response = opener.open(url, data)
            else:
                response = opener.open(url)

            return ''.join(response.readlines())

        except Exception:
            # If URL doesn't load for ANY reason, try again...
            # Quick n dirty solution for 404 returns because of network problems
            # However, this could infinite loop if there's an actual problem
            print("Scraping search results")
            sys.exit(0)


linkedin()
