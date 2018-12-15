import os
from src.profile_sourcer import scrape_search_results
from src.profile_extractor import scrape_profile_texts
from src.core import config, arguments_setup, authenticate

if __name__ == '__main__':  # For command line usage
    args = arguments_setup('-s')  # Search string

    search_string = args.keywords

    cookies = authenticate()

    cookies['JSESSIONID'] = config['cookie']['Csrf-Token']
    cookies['li_at'] = config['cookie']['li_at']

    headers = {'Csrf-Token': config['cookie']['Csrf-Token'],
               'User-Agent': config['cookie']['User-Agent']}

    print("-------- Scrape search results stage")

    search_results_filename = scrape_search_results(search_string, cookies,
                                                    headers)

    search_file_folder = './data/search_results/'
    full_file_path = os.path.join(search_file_folder, search_results_filename)

    print("-------- Scrape profile contents stage")
    scrape_profile_texts(full_file_path, cookies, headers, save_dicts=False)
