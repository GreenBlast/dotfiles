import re

# Read the content of the Markdown file
with open("./out.md", "r", encoding="utf-8") as file:
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
with open("cleaned_file.md", "w", encoding="utf-8") as file:
    file.write(cleaned_md_content)
