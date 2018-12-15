#!/usr/bin/python

import os
import json
import requests
import traceback
import pandas as pd
from src.core import config
from bs4 import BeautifulSoup


def scrape_profile_texts(source_csv, cookies, headers, save_dicts=False):

    source_filename = os.path.basename(source_csv)

    amount_profiles = config['profile_extractor']['amount_profiles']

    print("Config set to scrape first " + str(amount_profiles)
          + " search results")

    in_df = pd.read_csv(source_csv, encoding='utf-8', nrows=amount_profiles)

    url_list = in_df['url'].tolist()

    fields_to_scrape = scraping_dict().keys()

    empty_dict = dict.fromkeys(fields_to_scrape, None)

    out_df = pd.DataFrame(columns=['person_id'] + list(fields_to_scrape))

    for profile_url in url_list:
        data_dict = {}
        try:
            r = requests.get(profile_url, cookies=cookies, headers=headers)
        except Exception:
            print(traceback.format_exc())
            exit()

        person_id = profile_url.rsplit('/', 1)[-1]

        outdir = './data/profile_pages'
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        profile_filename = person_id

        html_file = os.path.join(outdir, profile_filename + '.html')
        json_file = os.path.join(outdir, profile_filename + '.json')

        with open(html_file, 'w') as the_file:
            the_file.write(r.text)

        soup = BeautifulSoup(open(html_file), "html.parser")

        # Locate part of the page that contains the data-json we want to scrape
        found = soup.find(
            lambda tag: tag.name == "code" and "*profile" in tag.text)

        extract = found.contents[0].strip()

        # Print the content of data to see all scraping possibilities
        # or optionally use below json file
        data = json.loads(extract)

        if save_dicts:  # Option to save the raw loaded dictionary to json file
            with open(json_file, 'w') as fp:
                json.dump(data, fp, indent=4)

        # This is where the scraping action happens
        for entity in data['included']:
            col_name = entity['entityUrn'].rsplit(':')[2]
            fill_data(data_dict, col_name, entity)

        # This creates {item: None}'s when a field is left empty
        # Which is required by the .loc operation below.
        # Order of summation matters!
        filled_dict = dict(list(empty_dict.items()) + list(data_dict.items()))

        filled_dict['person_id'] = person_id

        # Sample (filled_dict) as a row into df operation
        out_df.loc[len(out_df)] = filled_dict

    # Remove newlines and other whitespaces
    out_df.replace(r'\s', ' ', regex=True, inplace=True)

    datadir = './data/profile_data'
    if not os.path.exists(datadir):
        os.mkdir(datadir)

    csv_outfile = os.path.join(datadir, source_filename)

    out_df.to_csv(csv_outfile, index=False)

    print("Managed to fully scrape "
          + str(len(out_df)) +
          " profiles into " +
          str(csv_outfile))


def scraping_dict():
    # Below dict is organized as follows:
    # part_to_scrape: list_of_subfields_to_get
    items = {
        "fs_course": ["name"],

        "fs_education":
            ['schoolName', 'description', 'degreeName', 'activities', 'grade',
             'fieldOfStudy', 'projects', 'entityLocale', 'recommendations'],

        "fs_honor": ['title', 'description', 'issuer'],

        "fs_language": ['name'],

        "fs_position":
            ['companyName', 'description', 'title', {"company": "industries"},
             'courses', 'locationName', 'projects', 'entityLocale',
             'organizations', 'region', 'recommendations', 'honors',
             'promotion'],

        "fs_profile": ["headline", "summary", "industryName", "locationName"],

        "fs_project": ['title', 'occupation', 'description'],

        "fs_publication": ['name', 'publisher', 'description'],

        "fs_skill": ["name"]
    }

    # Extendable. See "..json.loads(extract)" for more scraping possibilities
    return items


def fill_data(data_dict, col_name, entity):
    if col_name in scraping_dict():
        subfields = scraping_dict()[col_name]
    else:
        return  # Don't scrape if not in scraping dictionary

    text = []

    for subfield in subfields:

        if isinstance(subfield, str):
            if subfield in entity:
                text.append(str(entity[subfield]))

        elif isinstance(subfield, dict):  # Nested value!
            for key, value in subfield.items():
                if key in entity and value in entity[key]:
                    text.append(str(entity[key][value]))

    # This concatenates all subfield texts into a single sentence in "col_name"
    # Also merges includes all entities of the same time
    # For ex. job1 job2 job3 will all be incl. in fs_position as one long string
    if col_name in data_dict:
        data_dict[col_name] += " " + " ".join(text)
    else:
        data_dict[col_name] = " ".join(text)
