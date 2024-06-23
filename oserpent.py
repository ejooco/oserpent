# Author: Eamon O'Connor
# Twitter: @eventloghorizon
# Snitches Get Stitches
# Initial Release: 23 June 2024
# Description:  This script is a CLI tool for searching using SerpApi with Google Dorks support.
#               It allows searches on general queries, GitHub, YouTube, and ExploitDB
#               Relevant themes are extracted and displayed. 
#
# License:
#    This script is open-source and can be used freely. I don't care about attribution it's not dangerous on it's own.

banner = """
 ▒█████    ██████ ▓█████  ██▀███   ██▓███  ▓█████  ███▄    █ ▄▄▄█████▓
▒██▒  ██▒▒██    ▒ ▓█   ▀ ▓██ ▒ ██▒▓██░  ██▒▓█   ▀  ██ ▀█   █ ▓  ██▒ ▓▒
▒██░  ██▒░ ▓██▄   ▒███   ▓██ ░▄█ ▒▓██░ ██▓▒▒███   ▓██  ▀█ ██▒▒ ▓██░ ▒░
▒██   ██░  ▒   ██▒▒▓█  ▄ ▒██▀▀█▄  ▒██▄█▓▒ ▒▒▓█  ▄ ▓██▒  ▐▌██▒░ ▓██▓ ░ 
░ ████▓▒░▒██████▒▒░▒████▒░██▓ ▒██▒▒██▒ ░  ░░▒████▒▒██░   ▓██░  ▒██▒ ░ 
░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░░░ ▒░ ░░ ▒▓ ░▒▓░▒▓▒░ ░  ░░░ ▒░ ░░ ▒░   ▒ ▒   ▒ ░░   
  ░ ▒ ▒░ ░ ░▒  ░ ░ ░ ░  ░  ░▒ ░ ▒░░▒ ░      ░ ░  ░░ ░░   ░ ▒░    ░    
░ ░ ░ ▒  ░  ░  ░     ░     ░░   ░ ░░          ░      ░   ░ ░   ░      
    ░ ░        ░     ░  ░   ░                 ░  ░         ░          
"""

import os
import sys
import requests
import json
import argparse
import pandas as pd
from colorama import init, Fore
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# Initialize colorama and spaCy
init(autoreset=True)
nlp = spacy.load("en_core_web_sm")

def fetch_results(query, api_key):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def extract_relevant_theme(texts, top_n=5):
    # Combine texts into a single string for processing
    combined_text = " ".join(texts)
    
    # Process the combined text with spaCy to extract entities
    doc = nlp(combined_text)
    
    # Extract named entities and nouns
    entities = [ent.text.lower() for ent in doc.ents if ent.label_ in ['ORG', 'PRODUCT', 'EVENT']]
    nouns = [chunk.text.lower() for chunk in doc.noun_chunks]

    # Combine entities and nouns for frequency analysis
    all_terms = entities + nouns

    # Compute term frequency
    counter = Counter(all_terms)
    most_common = counter.most_common(top_n)

    return most_common

def format_results(data):
    if len(data['organic']) == 0:
        print('No results found.')
        return pd.DataFrame(), []
    else:
        organic = pd.DataFrame(data['organic'])
        snippets = []
        for index, row in organic.iterrows():
            print(f"{Fore.BLUE}{row['link']} | {Fore.GREEN}{row['title']} | {Fore.YELLOW}{row['snippet']}")
            snippets.append(row['snippet'])
        
        return organic, snippets

def main():
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        print("Error: SERPAPI_API_KEY environment variable not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Search using SerpApi with Google Dorks support")
    
    # Store original help function
    original_help = parser.print_help

    def custom_help():
        print(banner)
        original_help()
    
    parser.print_help = custom_help

    parser.add_argument("query", help="Search query")
    parser.add_argument("--github", action="store_true", help="Search on GitHub")
    parser.add_argument("--youtube", action="store_true", help="Search on YouTube")
    parser.add_argument("--exploitdb", action="store_true", help="Search on ExploitDB")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        custom_help()
        sys.exit(1)

    query = args.query
    results_df = pd.DataFrame()
    all_snippets = []

    if args.github:
        github_query = query + " site:github.com"
        data = fetch_results(github_query, api_key)
        if data:
            organic, snippets = format_results(data)
            results_df = pd.concat([results_df, organic], ignore_index=True)
            all_snippets.extend(snippets)

    if args.youtube:
        youtube_query = query + " site:youtube.com"
        data = fetch_results(youtube_query, api_key)
        if data:
            organic, snippets = format_results(data)
            results_df = pd.concat([results_df, organic], ignore_index=True)
            all_snippets.extend(snippets)

    if args.exploitdb:
        exploitdb_query = query + " site:exploit-db.com"
        data = fetch_results(exploitdb_query, api_key)
        if data:
            organic, snippets = format_results(data)
            results_df = pd.concat([results_df, organic], ignore_index=True)
            all_snippets.extend(snippets)

    if results_df.empty:
        print("No results found for any of the queries.")
    else:
        most_relevant_themes = extract_relevant_theme(all_snippets)
        if most_relevant_themes:
            print(f"\n{Fore.CYAN}Most Relevant Themes:")
            for theme, freq in most_relevant_themes:
                print(f"{theme}: {freq}")

if __name__ == "__main__":
    main()