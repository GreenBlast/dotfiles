#!/usr/bin/env python

# This is a WIP, got to download the lessons, but I still need to rename them so that they will be in the correct order
import sys
import urllib.request
import re
import subprocess

url = 'https://egghead.io/lessons/javascript-introduction-to-mock-rest-and-graphql-apis-with-mock-service-worker'
lesson_prefix = 'https://egghead.io'

def download_matches(matches):

    for item in matches:
        url_input = f'{lesson_prefix}{item}'
        process = subprocess.run([f'/usr/local/bin/yt-dlp', url_input], env={'LANG': 'en_US.UTF-8'},)


def get_url_data(url):

    try:
        # Send a GET request to the about page using urllib
        with urllib.request.urlopen(url) as response:
            # Check if the request was successful
            if response.getcode() == 200:
                # Read and decode the HTML content
                html_content = response.read().decode('utf-8')

                # print(html_content)

                # Use regex to find all links that match the pattern href="/lessson/..."
                pattern = r'"path":"(\/lessons\/[^"]+)",'
                matches = re.findall(pattern, html_content)

                return matches

            else:
                print(f"Failed to fetch the page. Status code: {response.status}")
    except Exception as e:
        return "An error occurred: " + str(e)


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: script.py video_url")
    # else:
        # channel_url = sys.argv[1]
        matches = get_url_data(url)
        download_matches(matches)
        # print(rss_url)

