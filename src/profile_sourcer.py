#!/usr/bin/python
import os
import json
import time
import requests
import traceback
import pandas as pd
from src.core import config


def scrape_search_results(search_string, cookies, headers):
    # Fetch the initial page to get results/page counts

    # search_url / page_url not in config: not expected to be changed by user
    search_url = "https://www.linkedin.com/voyager/api/search/cluster?" \
                   "count=%i&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear" \
                   "%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=0"

    page_url = "https://www.linkedin.com/voyager/api/search/cluster?" \
               "count=%i&guides=List(v-%%3EPEOPLE,facetGeoRegion-%%3Ear" \
               "%%3A0)&keywords=%s&origin=FACETED_SEARCH&q=guided&start=%i"

    url = search_url % (config['search_results']['results_per_page'],
                        search_string)

    try:
        r = requests.get(url, cookies=cookies, headers=headers)
    except Exception:
        print(traceback.format_exc())
        exit()

    content = json.loads(r.text)
    data_total = content['paging']['total']
    
    # Calculate pages of final results at X results/page
    pages = data_total / config['search_results']['results_per_page']
    if data_total % config['search_results']['results_per_page'] == 0:
        # Including 0, subtract a page if no leftover results on last page
        pages = pages - 1 
    if pages == 0: 
        pages = 1
    
    print("Found %i results for search query \"%s\"" %
          (data_total, search_string))

    if data_total > 1000:
        pages = config['search_results']['pages_to_scrape']
        # FYI: LinkedIn only allows 1000 results

    print("Fetching first %i pages" % pages)

    search_results = pd.DataFrame()

    for p in range(pages):
        # Request results for each page using the start offset

        url = page_url % (config['search_results']
                          ['results_per_page'],
                          search_string,
                          p*config['search_results']
                          ['results_per_page'])

        r = requests.get(url, cookies=cookies, headers=headers)

        content = r.text.encode('UTF-8')
        content = json.loads(content.decode("utf-8"))

        print("Fetching page %i (contains %i results)" %
              (p+1, len(content['elements'][0]['elements'])))

        profiles_skipped = False
        for c in content['elements'][0]['elements']:
            try:
                # Using these lookup strings to shorten query lines below
                lookup = 'com.linkedin.voyager.search.SearchProfile'
                h = 'hitInfo'
                m = 'miniProfile'

                # Doesn't work anymore
                # pic_url = "https://media.licdn.com/mpr/mpr/shrinknp_400_400%s"
                # pic_query = "com.linkedin.voyager.common.MediaProcessorImage"

                if not c[h][lookup]['headless']:
                    try:
                        data_industry = c[h][lookup]['industry']
                    except Exception:
                        data_industry = ""

                    data_firstname = c[h][lookup][m]['firstName']

                    data_lastname = c[h][lookup][m]['lastName']

                    data_url = "https://www.linkedin.com/in/%s" % \
                               c[h][lookup][m]['publicIdentifier']

                    data_occupation = c[h][lookup][m]['occupation']

                    data_location = c[h][lookup]['location']

                    '''
                    # This section doesn't work
                    try:
                        extract_id = c[h][lookup][m]['picture'][pic_query]['id']
                        data_picture = pic_url % extract_id

                    except Exception:
                        # No pic found for (data_firstn, data_lastn, d_occ)
                        data_picture = ""
                    '''

                    data_dict = {
                        "name": data_firstname + " " + data_lastname,
                        "occupation": data_occupation,
                        "location": data_location,
                        "industry": data_industry,
                        "url": data_url
                        # "pic": data_picture  # Doesn't work
                    }

                    search_results = search_results.append([data_dict])

                else:
                    print("[Notice] Headless profile found. Skipping")
            except Exception:
                profiles_skipped = True
                print("Skipped profile.. ", end='')
                continue
        if profiles_skipped:  # Just for prettyness of printing..
            print()

    timestamp = str(int(time.time()))

    filename = timestamp + '.csv'

    outdir = './data/search_results'
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    full_file_path = os.path.join(outdir, filename)

    amount_results = len(search_results)

    if amount_results > 0:
        print("Stored total of " + str(amount_results)
              + " search results in file "
              + str(full_file_path))

        search_results.to_csv(full_file_path,
                              index=False,
                              columns=["name", "occupation",
                                       "location", "industry", "url"])
    else:
        print("Zero valid search results! Increase amount to scrape in config")
        exit(0)

    return filename

