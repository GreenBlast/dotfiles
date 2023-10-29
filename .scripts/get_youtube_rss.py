#!/usr/bin/env python
import sys
import urllib.request
import re
import subprocess

# Note: This script assumes that the structure of the YouTube page HTML remains consistent.

def copy_to_clipboard(text):
    text_to_copy = text

    # Copy the text to the clipboard using pbcopy on macOS
    process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(input=text_to_copy.encode('utf-8'))



def get_rss_url(channel_url):
    about_url = channel_url + "/about"

    try:
        # Send a GET request to the about page using urllib
        with urllib.request.urlopen(about_url) as response:
            # Check if the request was successful
            if response.getcode() == 200:
                # Read and decode the HTML content
                html_content = response.read().decode('utf-8')

                # Use regular expressions to find the rssUrl and extract the URL
                rss_url_match = re.search(r'rssUrl":"(https://[^"]+)', html_content)

                if rss_url_match:
                    rss_url = rss_url_match.group(1)
                    return rss_url
                else:
                    return "RSS URL not found on the page."
            else:
                return f"Failed to retrieve the about page. Status code: {response.getcode()}"
    except Exception as e:
        return "An error occurred: " + str(e)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py video_url")
    else:
        channel_url = sys.argv[1]
        rss_url = get_rss_url(channel_url)
        copy_to_clipboard(rss_url)
        print(rss_url)

