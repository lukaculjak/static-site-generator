import os
import shutil
from helpers import extract_title, markdown_to_html_node

def copy_directory(source, destination):
    source = os.path.realpath(source)
    destination = os.path.realpath(destination)
    if not os.path.isdir(source):
        raise FileNotFoundError(f"Source directory does not exist: {source}")
    if os.path.commonpath([source, destination]) in (source, destination):
        raise ValueError("Source and destination directories must not overlap")

    if os.path.exists(destination):
        shutil.rmtree(destination)
    os.makedirs(destination)

    for name in os.listdir(source):
        source_path = os.path.join(source, name)
        destination_path = os.path.join(destination, name)
        if os.path.isfile(source_path):
            print(f"Copying {source_path} -> {destination_path}")
            shutil.copy(source_path, destination_path)
        else:
            copy_directory(source_path, destination_path)

def generate_page(from_path, template_path, dest_path):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    with open(from_path, encoding="utf-8") as markdown_file:
        markdown = markdown_file.read()
    with open(template_path, encoding="utf-8") as template_file:
        template = template_file.read()

    html = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)
    page = template.replace("{{ Title }}", title).replace("{{ Content }}", html)
    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as output_file:
        output_file.write(page)

def generate_pages_recursive(dir_path_content, template_path, dest_dir_path):
    os.makedirs(dest_dir_path, exist_ok=True)
    for name in os.listdir(dir_path_content):
        source_path = os.path.join(dir_path_content, name)
        destination_path = os.path.join(dest_dir_path, name)
        if os.path.isdir(source_path):
            generate_pages_recursive(source_path, template_path, destination_path)
        elif os.path.isfile(source_path) and name.lower().endswith(".md"):
            destination_path = os.path.join(dest_dir_path, os.path.splitext(name)[0] + ".html")
            generate_page(source_path, template_path, destination_path)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    copy_directory(
        os.path.join(project_root, "static"),
        os.path.join(project_root, "public"),
    )
    generate_pages_recursive(
        os.path.join(project_root, "content"),
        os.path.join(project_root, "template.html"),
        os.path.join(project_root, "public"),
    )

if __name__ == "__main__":
    main()