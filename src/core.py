import os
import sys
import json
import argparse
import traceback
import subprocess

with open(os.getcwd() + '/config.json') as config_file:
    config = json.load(config_file)


def arguments_setup(option):
    """ Setup Argument Parameters """
    parser = argparse.ArgumentParser()
    parser.add_argument(option, '--keywords')
    return parser.parse_args()


def authenticate():
    try:
        subproc = subprocess.Popen(['python', 'login.py'],
                                   stdout=subprocess.PIPE,
                                   cwd='src')

        sess = subproc.communicate()[0].decode('utf-8').replace("\n", "")

        if len(sess) == 0:
            sys.exit("[Error] Unable to login to LinkedIn.com")

        session_cookies = dict(li_at=sess)

    except Exception:
        print(traceback.format_exc())
        sys.exit("[Fatal] Could not authenticate to linkedin.")

    return session_cookies
