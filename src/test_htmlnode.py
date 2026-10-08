import unittest
import contextlib
import io
import tempfile
from pathlib import Path
from htmlnode import HTMLNode, LeafNode, ParentNode
from helpers import extract_markdown_images, extract_markdown_links, extract_title, markdown_to_html_node
from main import generate_page, generate_pages_recursive

class TestHTMLNode(unittest.TestCase):
    def test_render(self):
        node = HTMLNode(tag="div", value="Hello", props={"class": "greeting"})
        self.assertEqual(node.render(), '<div class="greeting">Hello</div>')

    def test_render_with_children(self):
        child = HTMLNode(tag="span", value="World")
        node = HTMLNode(tag="div", value="Hello ", children=[child], props={"class": "greeting"})
        self.assertEqual(node.render(), '<div class="greeting">Hello <span>World</span></div>')

    def test_repr(self):
        node = HTMLNode(tag="div", value="Hello", props={"class": "greeting"})
        self.assertEqual(repr(node), "HTMLNode(tag='div', value='Hello', children=[], props={'class': 'greeting'})")

    def test_props_to_html(self):
        node = HTMLNode(tag="div", value="Hello", props={"class": "greeting", "id": "main"})
        self.assertEqual(node.props_to_html(), 'class="greeting" id="main"')

    def test_to_html_not_implemented(self):
        node = HTMLNode(tag="div", value="Hello")
        with self.assertRaises(NotImplementedError):
            node.to_html()

    def test_leaf_node(self):
        node = LeafNode(tag="div", value="Hello", props={"class": "greeting"})
        self.assertEqual(node.render(), '<div class="greeting">Hello</div>')
        self.assertEqual(node.to_html(), '<div class="greeting">Hello</div>')
        self.assertEqual(repr(node), "LeafNode(tag='div', value='Hello', props={'class': 'greeting'})")

    def test_leaf_to_html_p(self):
        node = LeafNode("p", "Hello, world!")
        self.assertEqual(node.to_html(), "<p>Hello, world!</p>")

    def test_to_html_with_children(self):
        child_node = LeafNode("span", "child")
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(parent_node.to_html(), "<div><span>child</span></div>")


    def test_to_html_with_grandchildren(self):
        grandchild_node = LeafNode("b", "grandchild")
        child_node = ParentNode("span", [grandchild_node])
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(
            parent_node.to_html(),
            "<div><span><b>grandchild</b></span></div>",
        )

    def test_extract_markdown_images_1(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual([("image", "https://i.imgur.com/zjjcJKZ.png")], matches)

    def test_extract_markdown_images(self):
        text = "This is text with a ![rick roll](https://i.imgur.com/aKaOqIh.gif) and ![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        self.assertEqual(extract_markdown_images(text), [
            ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
            ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg"),
        ])

    def test_extract_markdown_links(self):
        text = "This is text with a link [to boot dev](https://www.boot.dev), an image ![logo](https://example.com/logo.png), and [to youtube](https://www.youtube.com/@bootdotdev)"
        self.assertEqual(extract_markdown_links(text), [
            ("to boot dev", "https://www.boot.dev"),
            ("to youtube", "https://www.youtube.com/@bootdotdev"),
        ])

class TestMarkdownToHTMLNode(unittest.TestCase):
    def test_paragraphs(self):
        md = """
This is **bolded** paragraph
text in a p
tag here

This is another paragraph with _italic_ text and `code` here

"""
        node = markdown_to_html_node(md)
        self.assertIsInstance(node, ParentNode)
        self.assertEqual(node.tag, "div")
        self.assertEqual(len(node.children), 2)
        self.assertEqual(
            node.to_html(),
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p>"
            "<p>This is another paragraph with <i>italic</i> text and <code>code</code> here</p></div>",
        )

    def test_codeblock(self):
        md = """
```
This is text that _should_ remain
the **same** even with inline stuff
```
"""
        self.assertEqual(
            markdown_to_html_node(md).to_html(),
            "<div><pre><code>This is text that _should_ remain\n"
            "the **same** even with inline stuff\n</code></pre></div>",
        )

    def test_codeblock_with_blank_lines(self):
        self.assertEqual(
            markdown_to_html_node("Before\n\n```\nfirst\n\n  **second**\n```\n\nAfter").to_html(),
            "<div><p>Before</p><pre><code>first\n\n  **second**\n</code></pre><p>After</p></div>",
        )

    def test_heading_levels(self):
        for level in range(1, 7):
            with self.subTest(level=level):
                self.assertEqual(
                    markdown_to_html_node("#" * level + " A **heading**").to_html(),
                    f"<div><h{level}>A <b>heading</b></h{level}></div>",
                )

    def test_quote(self):
        self.assertEqual(
            markdown_to_html_node("> A **quote**\n> with _emphasis_").to_html(),
            "<div><blockquote>A <b>quote</b> with <i>emphasis</i></blockquote></div>",
        )

    def test_lists(self):
        self.assertEqual(
            markdown_to_html_node("- **first**\n- second\n\n1. _one_\n2. `two`").to_html(),
            "<div><ul><li><b>first</b></li><li>second</li></ul>"
            "<ol><li><i>one</i></li><li><code>two</code></li></ol></div>",
        )

    def test_links_and_images(self):
        self.assertEqual(
            markdown_to_html_node("A [link](https://example.com) and ![photo](photo.png)").to_html(),
            '<div><p>A <a href="https://example.com">link</a> and '
            '<img src="photo.png" alt="photo"></p></div>',
        )

    def test_inline_code_is_literal(self):
        self.assertEqual(
            markdown_to_html_node("Keep `**bold** _italic_ [link](url)` literal").to_html(),
            "<div><p>Keep <code>**bold** _italic_ [link](url)</code> literal</p></div>",
        )

    def test_mixed_document(self):
        node = markdown_to_html_node("# Title\n\nParagraph\n\n> Quote\n\n- item\n\n1. item\n\n```\ncode\n```")
        self.assertEqual([child.tag for child in node.children], ["h1", "p", "blockquote", "ul", "ol", "pre"])
        self.assertTrue(all(isinstance(child, HTMLNode) for child in node.children))

    def test_empty_document(self):
        self.assertEqual(markdown_to_html_node(" \n\n ").to_html(), "<div></div>")

class TestExtractTitle(unittest.TestCase):
    def test_title(self):
        self.assertEqual(extract_title("# Hello"), "Hello")

    def test_strip_whitespace(self):
        self.assertEqual(extract_title("  #   Hello world  \n"), "Hello world")

    def test_find_first_h1(self):
        self.assertEqual(extract_title("## Subtitle\n\nParagraph\n\n# Title\n\n# Other"), "Title")

    def test_missing_h1(self):
        for markdown in ["", "Paragraph", "## Subtitle\n### Smaller", "#Not a heading"]:
            with self.subTest(markdown=markdown):
                with self.assertRaisesRegex(ValueError, "h1"):
                    extract_title(markdown)

    def test_ignore_code(self):
        self.assertEqual(extract_title("```\n# Not a title\n```\n\n# Actual title"), "Actual title")
        with self.assertRaises(ValueError):
            extract_title("```\n# Not a title\n```")

class TestGeneratePage(unittest.TestCase):
    def test_generate_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "index.md"
            template = root / "template.html"
            destination = root / "nested" / "public" / "index.html"
            source.write_text("# Hello\n\nA **bold** paragraph.", encoding="utf-8")
            template.write_text(
                "<html><title>{{ Title }}</title><article>{{ Content }}</article></html>",
                encoding="utf-8",
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                generate_page(source, template, destination)
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                "<html><title>Hello</title><article><div><h1>Hello</h1>"
                "<p>A <b>bold</b> paragraph.</p></div></article></html>",
            )
            self.assertIn(f"Generating page from {source} to {destination} using {template}", output.getvalue())

    def test_missing_title_does_not_write_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "index.md"
            template = root / "template.html"
            destination = root / "index.html"
            source.write_text("## Subtitle", encoding="utf-8")
            template.write_text("{{ Title }}{{ Content }}", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    generate_page(source, template, destination)
            self.assertFalse(destination.exists())

class TestGeneratePagesRecursive(unittest.TestCase):
    def test_nested_pages_and_existing_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = root / "content"
            destination = root / "public"
            template = root / "template.html"
            pages = {
                "index.md": "Home",
                "blog/post/index.md": "Post",
                "blog/post/notes.md.md": "Notes",
                "contact/index.MD": "Contact",
            }
            for relative, title in pages.items():
                source = content / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"# {title}\n\n[Home](/)", encoding="utf-8")
            (content / "ignore.txt").write_text("Not Markdown", encoding="utf-8")
            (content / "empty").mkdir()
            destination.mkdir()
            asset = destination / "index.css"
            asset.write_text("body { color: black; }", encoding="utf-8")
            template.write_text("<title>{{ Title }}</title>{{ Content }}", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                generate_pages_recursive(content, template, destination)

            expected_paths = {Path(relative).with_suffix(".html") for relative in pages}
            actual_paths = {path.relative_to(destination) for path in destination.rglob("*.html")}
            self.assertEqual(actual_paths, expected_paths)
            for relative, title in pages.items():
                html = (destination / Path(relative).with_suffix(".html")).read_text(encoding="utf-8")
                self.assertEqual(
                    html,
                    f'<title>{title}</title><div><h1>{title}</h1><p><a href="/">Home</a></p></div>',
                )
            self.assertFalse((destination / "ignore.txt").exists())
            self.assertTrue((destination / "empty").is_dir())
            self.assertEqual(asset.read_text(encoding="utf-8"), "body { color: black; }")

    def test_empty_content_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            content = root / "content"
            destination = root / "public"
            content.mkdir()
            generate_pages_recursive(content, root / "template.html", destination)
            self.assertTrue(destination.is_dir())
            self.assertEqual(list(destination.iterdir()), [])

if __name__ == "__main__":
    unittest.main()