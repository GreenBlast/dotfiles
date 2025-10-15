#!/usr/bin/env python

# This is a WIP, got to download the lessons, but I still need to rename them so that they will be in the correct order
import sys
import urllib.request
import re
import subprocess
import os

# url = 'https://egghead.io/lessons/astro-intro-build-a-full-stack-blog-with-astro'
lesson_prefix = "https://egghead.io"

filepath = "."


def download_item(item):
    url_input = f"{lesson_prefix}{item}"
    # process = subprocess.run([f'/usr/local/bin/yt-dlp', url_input], env={'LANG': 'en_US.UTF-8'},)

    # if process.returncode == 0:
    #     # The download was successful
    #     # Parse the filename from the standard output
    #     lines = stdout.decode('utf-8').split('\n')
    #     for line in lines:
    #         if line.startswith('[download] Destination: '):
    #             downloaded_file = line.replace('[download] Destination: ', '').strip()
    #             downloaded_files.append(downloaded_file)
    # else:
    #     # Handle download error
    #     print(f"Error downloading {url_input}: {stderr.decode('utf-8')}")

    # print(downloaded_files)
    process = subprocess.Popen(
        [f"/run/current-system/sw/bin/yt-dlp", "--print", "filename", url_input],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"LANG": "en_US.UTF-8"},
    )
    stdout, stderr = process.communicate()

    downloaded_file = None
    if process.returncode == 0:
        # The download was successful
        # Parse the filename from the standard output
        lines = stdout.decode("utf-8").split("\n")
        downloaded_file = "".join(lines).strip()
        print(f"Downloaded: {downloaded_file}")
    else:
        # Handle download error
        print(f"Error downloading {url}: {stderr.decode('utf-8')}")

    process = subprocess.run(
        [f"/run/current-system/sw/bin/yt-dlp", url_input],
        env={"LANG": "en_US.UTF-8"},
    )

    print(f"downloaded_file={downloaded_file}")
    return downloaded_file


def rename_item(filepath_to_dir, filename, i):
    new_name = f"{i:05} - {filename}"
    old_file = os.path.join(filepath_to_dir, filename)
    new_file = os.path.join(filepath_to_dir, new_name)
    os.rename(old_file, new_file)
    print(f'[+] - New file name: "{new_name}"')


def download_matches_and_rename(matches, filepath_to_dir):
    items_to_rename = []
    for item in matches:
        downloaded_file = download_item(item)
        items_to_rename.append(downloaded_file)

    for i, item in enumerate(items_to_rename):
        rename_item(filepath_to_dir, item, i + 1)


def get_url_data(url):
    try:
        # Send a GET request to the about page using urllib
        with urllib.request.urlopen(url) as response:
            # Check if the request was successful
            if response.getcode() == 200:
                # Read and decode the HTML content
                html_content = response.read().decode("utf-8")

                # print(html_content)

                # Use regex to find all links that match the pattern href="/lessson/..."
                pattern = r'"path":"(\/lessons\/[^"]+)",'
                matches = re.findall(pattern, html_content)

                return matches

            else:
                print(f"Failed to fetch the page. Status code: {
                      response.status}")
    except Exception as e:
        return "An error occurred: " + str(e)


def rename_files_in_dir(filepath_to_dir):
    files = os.listdir(filepath_to_dir)
    regex = r"\[\d+\].mp4$"
    numbered_files = [f for f in files if re.search(regex, f)]
    sorted_files = sorted(
        numbered_files, key=lambda x: int(re.search(r"\[(\d+)\]", x).group(1))
    )

    for i, filename in enumerate(sorted_files, start=1):
        new_name = f"{i:05} - {filename}"
        old_file = os.path.join(filepath_to_dir, filename)
        new_file = os.path.join(filepath_to_dir, new_name)
        os.rename(old_file, new_file)
        print(f'[+] - New file name: "{new_name}"')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py video_url")
    else:
        url = sys.argv[1]
        matches = get_url_data(url)
        # matches = ['/lessons/astro-intro-build-a-full-stack-blog-with-astro']
        # download_matches_and_rename(matches, filepath)
        # Last link is video link itself
        download_matches_and_rename(matches[:-1], filepath)
        # rename_files_in_dir(filepath)
