from textnode import TextNode, TextType
from htmlnode import HTMLNode, LeafNode, ParentNode
import re
from enum import Enum

IMAGE_RE = re.compile(r"!\[([^\[\]]*)\]\(([^()]*)\)")
LINK_RE = re.compile(r"(?<!!)\[([^\[\]]*)\]\(([^()]*)\)")

def split_nodes_delimiter(old_nodes: list[TextNode], delimiter: str, text_type: TextType) -> list[TextNode]:
    if delimiter == "":
        raise ValueError("Delimiter cannot be an empty string")

    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.PLAIN:
            new_nodes.append(node)
            continue

        parts = node.text.split(delimiter)
        if len(parts) % 2 == 0:
            raise ValueError(f"Invalid Markdown: unmatched delimiter {delimiter!r} in {node.text!r}")

        new_nodes.extend(
            TextNode(part, node.text_type if index % 2 == 0 else text_type, node.url)
            for index, part in enumerate(parts)
            if part
        )
    return new_nodes

def extract_markdown_images(text: str) -> list[tuple[str, str]]:
    return IMAGE_RE.findall(text)

def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    return LINK_RE.findall(text)

def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.PLAIN:
            new_nodes.append(node)
            continue

        last_index = 0
        matches = list(IMAGE_RE.finditer(node.text))
        if not matches:
            new_nodes.append(node)
            continue

        for match in matches:
            start, end = match.span()
            if start > last_index:
                new_nodes.append(TextNode(node.text[last_index:start], TextType.PLAIN, node.url))
            new_nodes.append(TextNode(match.group(1), TextType.IMAGE, match.group(2)))
            last_index = end

        if last_index < len(node.text):
            new_nodes.append(TextNode(node.text[last_index:], TextType.PLAIN, node.url))

    return new_nodes

def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:
    new_nodes = []
    for node in old_nodes:
        if node.text_type != TextType.PLAIN:
            new_nodes.append(node)
            continue

        last_index = 0
        matches = list(LINK_RE.finditer(node.text))
        if not matches:
            new_nodes.append(node)
            continue

        for match in matches:
            start, end = match.span()
            if start > last_index:
                new_nodes.append(TextNode(node.text[last_index:start], TextType.PLAIN, node.url))
            new_nodes.append(TextNode(match.group(1), TextType.LINK, match.group(2)))
            last_index = end

        if last_index < len(node.text):
            new_nodes.append(TextNode(node.text[last_index:], TextType.PLAIN, node.url))

    return new_nodes

def text_to_textnodes(text: str) -> list[TextNode]:
    nodes = [TextNode(text, TextType.PLAIN)]
    for delimiter, text_type in [
        ("`", TextType.CODE),
        ("**", TextType.BOLD),
        ("_", TextType.ITALIC),
        ("*", TextType.ITALIC),
    ]:
        nodes = split_nodes_delimiter(nodes, delimiter, text_type)
    nodes = split_nodes_image(nodes)
    return split_nodes_link(nodes)

def markdown_to_blocks(markdown: str) -> list[str]:
    blocks = []
    lines = []
    in_code = False
    for line in markdown.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
        if not line.strip() and not in_code:
            if lines:
                blocks.append("\n".join(lines).strip())
                lines = []
        else:
            lines.append(line)
    if lines:
        blocks.append("\n".join(lines).strip())
    return blocks

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADER = "header"
    CODE = "code"
    QUOTE = "quote"
    U_LIST = "unordered_list"
    O_LIST = "ordered_list"

def block_to_block_type(block: str) -> BlockType:
    if block.startswith("#"):
        return BlockType.HEADER
    elif block.startswith("```"):
        return BlockType.CODE
    elif block.startswith(">"):
        return BlockType.QUOTE
    elif block.startswith("- "):
        return BlockType.U_LIST
    elif block[0].isdigit() and block[1:3] == ". ":
        return BlockType.O_LIST
    else:
        return BlockType.PARAGRAPH

def text_to_children(text: str) -> list[HTMLNode]:
    return [TextNode.text_node_to_html_node(node) for node in text_to_textnodes(text)]

def block_to_html_node(block: str) -> HTMLNode:
    block_type = block_to_block_type(block)
    if block_type == BlockType.CODE:
        text = block[block.index("\n") + 1:-3]
        code_node = TextNode.text_node_to_html_node(TextNode(text, TextType.CODE))
        return ParentNode("pre", [code_node])
    if block_type == BlockType.HEADER:
        heading, text = block.split(" ", 1)
        return ParentNode(f"h{len(heading)}", text_to_children(text))
    if block_type == BlockType.QUOTE:
        text = " ".join(line[1:].strip() for line in block.split("\n"))
        return ParentNode("blockquote", text_to_children(text))
    if block_type in (BlockType.U_LIST, BlockType.O_LIST):
        items = []
        for line in block.split("\n"):
            text = line[2:] if block_type == BlockType.U_LIST else line.split(". ", 1)[1]
            items.append(ParentNode("li", text_to_children(text.strip())))
        tag = "ul" if block_type == BlockType.U_LIST else "ol"
        return ParentNode(tag, items)
    text = " ".join(block.split("\n"))
    return ParentNode("p", text_to_children(text))

def markdown_to_html_node(markdown: str) -> HTMLNode:
    children = [block_to_html_node(block) for block in markdown_to_blocks(markdown)]
    return ParentNode("div", children or [LeafNode(None, "")])

def extract_title(markdown):
    in_code = False
    for line in markdown.splitlines():
        line = line.strip()
        if line.startswith("```"):
            in_code = not in_code
        if not in_code:
            match = re.match(r"^#(?:[ \t]+|$)(.*)$", line)
            if match:
                return match.group(1).strip()
    raise ValueError("Markdown document must contain an h1 header")