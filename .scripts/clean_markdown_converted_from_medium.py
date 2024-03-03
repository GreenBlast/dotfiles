import re
import os
import sys


def main(input_file_path, output_file_path):

    # Get the absolute path of the input file
    input_file_path = os.path.abspath(input_file_path)

    # Get the absolute path of the output file
    output_file_path = os.path.abspath(output_file_path)

    # Read the content of the Markdown file
    with open(input_file_path, "r", encoding="utf-8") as file:
        md_content = file.read()

    # Define a regular expression pattern to match HTML tags
    html_tags_pattern = re.compile(r'<.*?>')

    # Remove HTML tags from the Markdown content
    cleaned_md_content = re.sub(html_tags_pattern, '', md_content)

    # Define a regular expression pattern to match HTML tags and other constructs
    pattern = re.compile(r':::.*?}|\[\[·\].*?\]{.*?}|{.*?}')

    # Remove matched constructs from the Markdown content
    cleaned_md_content = re.sub(pattern, '', cleaned_md_content)

    # Define a regular expression pattern to match HTML tags and other constructs
    pattern = re.compile(r':::.*?}|\[\[·\].*?\]{.*?}|{.*?}|\[\]\[\]\[\]|:::')

    # Remove matched constructs from the Markdown content
    cleaned_md_content = re.sub(pattern, '', cleaned_md_content)

    # Limit consecutive line breaks to a maximum of three
    cleaned_md_content = re.sub(r'\n{4,}', '\n\n\n', cleaned_md_content)

    # Save the cleaned content back to the file
    with open(output_file_path, "w", encoding="utf-8") as file:
        file.write(cleaned_md_content)


if __name__ == "__main__":
    # Check if there are enough command line arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file_path> <output_file_path>")
        sys.exit(1)

    # Get input and output file paths from command line arguments
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    # Call the main function with the provided file paths
    main(input_file_path, output_file_path)
