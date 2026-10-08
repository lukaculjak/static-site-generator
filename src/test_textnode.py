import unittest
from textnode import TextNode, TextType
from helpers import markdown_to_blocks, split_nodes_delimiter, split_nodes_image, split_nodes_link, text_to_textnodes, block_to_block_type, BlockType

class TestTextNode(unittest.TestCase):
    def test_eq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_neq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a different text node", TextType.BOLD)
        self.assertNotEqual(node, node2)

    def test_url(self):
        node = TextNode("This is some anchor text", TextType.LINK, "https://www.boot.dev")
        node2 = TextNode("This is some anchor text", TextType.LINK, "https://www.boot.dev")
        self.assertEqual(node, node2)

    def test_text(self):
        node = TextNode("This is a text node", TextType.PLAIN)
        html_node = TextNode.text_node_to_html_node(node)
        self.assertIsNone(html_node.tag)
        self.assertEqual(html_node.value, "This is a text node")

    def test_bold_text(self):
        node = TextNode("This is bold text", TextType.BOLD)
        html_node = TextNode.text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "This is bold text")

    def test_italic_text(self):
        node = TextNode("This is italic text", TextType.ITALIC)
        html_node = TextNode.text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "i")
        self.assertEqual(html_node.value, "This is italic text")

    def test_code_text(self):
        node = TextNode("This is code text", TextType.CODE)
        html_node = TextNode.text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.value, "This is code text")

    def test_split_nodes_delimiter(self):
        nodes = [TextNode("This is **bold** text", TextType.PLAIN)]
        new_nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
        self.assertEqual(new_nodes, [
            TextNode("This is ", TextType.PLAIN),
            TextNode("bold", TextType.BOLD),
            TextNode(" text", TextType.PLAIN),
        ])

    def test_split_nodes_delimiter_empty(self):
        nodes = [TextNode("", TextType.PLAIN)]
        self.assertEqual(split_nodes_delimiter(nodes, "**", TextType.BOLD), [])

    def test_split_nodes_delimiter_empty_delimiter(self):
        nodes = [TextNode("text", TextType.PLAIN)]
        with self.assertRaisesRegex(ValueError, "empty string"):
            split_nodes_delimiter(nodes, "", TextType.BOLD)

    def test_split_nodes_delimiter_preserves_non_plain_nodes(self):
        nodes = [TextNode("This is bold text", TextType.BOLD)]
        self.assertEqual(split_nodes_delimiter(nodes, "**", TextType.BOLD), nodes)

    def test_split_nodes_delimiter_preserves_mixed_nodes(self):
        italic_node = TextNode("italic", TextType.ITALIC)
        nodes = [
            TextNode("This is ", TextType.PLAIN),
            italic_node,
            TextNode(" and **bold** text", TextType.PLAIN),
        ]
        self.assertEqual(split_nodes_delimiter(nodes, "**", TextType.BOLD), [
            nodes[0],
            italic_node,
            TextNode(" and ", TextType.PLAIN),
            TextNode("bold", TextType.BOLD),
            TextNode(" text", TextType.PLAIN),
        ])

    def test_split_nodes_delimiter_unmatched(self):
        nodes = [TextNode("This is **bold", TextType.PLAIN)]
        with self.assertRaisesRegex(ValueError, "unmatched delimiter"):
            split_nodes_delimiter(nodes, "**", TextType.BOLD)

    def test_split_images_1(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.PLAIN,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.PLAIN),
                TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
                TextNode(" and another ", TextType.PLAIN),
                TextNode("second image", TextType.IMAGE, "https://i.imgur.com/3elNhQu.png"),
            ],
            new_nodes,
        )

    def test_split_nodes_image(self):
        old_nodes = [TextNode("This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)", TextType.PLAIN)]
        new_nodes = split_nodes_image(old_nodes)
        self.assertEqual(new_nodes, [
            TextNode("This is text with an ", TextType.PLAIN),
            TextNode("image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"),
        ])

    def test_split_nodes_link(self):
        old_nodes = [TextNode("This is text with a [link](https://example.com)", TextType.PLAIN)]
        new_nodes = split_nodes_link(old_nodes)
        self.assertEqual(new_nodes, [
            TextNode("This is text with a ", TextType.PLAIN),
            TextNode("link", TextType.LINK, "https://example.com"),
        ])

    def test_split_nodes_image_preserves_non_plain_nodes(self):
        node = TextNode("![image](https://example.com/image.png)", TextType.BOLD)
        self.assertEqual(split_nodes_image([node]), [node])

    def test_split_nodes_link_preserves_non_plain_nodes(self):
        node = TextNode("[link](https://example.com)", TextType.ITALIC)
        self.assertEqual(split_nodes_link([node]), [node])

    def test_text_to_textnodes(self):
        text = "This is plain text"
        nodes = text_to_textnodes(text)
        self.assertEqual(nodes, [TextNode(text, TextType.PLAIN)])

    def test_text_to_textnodes_complex(self):
        text = "This is **bold** and *italic* text"
        nodes = text_to_textnodes(text)
        self.assertEqual(nodes, [
            TextNode("This is ", TextType.PLAIN),
            TextNode("bold", TextType.BOLD),
            TextNode(" and ", TextType.PLAIN),
            TextNode("italic", TextType.ITALIC),
            TextNode(" text", TextType.PLAIN),
        ])

    def test_markdown_to_blocks(self):
        md = """
This is **bolded** paragraph

This is another paragraph with _italic_ text and `code` here
This is the same paragraph on a new line

- This is a list
- with items
"""
        self.assertEqual(
            markdown_to_blocks(md),
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\nThis is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )

    def test_markdown_to_blocks_removes_empty_blocks(self):
        self.assertEqual(
            markdown_to_blocks("\n\nFirst block\n\n\n\nSecond block\n\n"),
            ["First block", "Second block"],
        )
        self.assertEqual(markdown_to_blocks(" \n\n  \n\n"), [])

    def test_block_to_block_type(self):
        self.assertEqual(block_to_block_type("# Header"), BlockType.HEADER)
        self.assertEqual(block_to_block_type("```code```"), BlockType.CODE)
        self.assertEqual(block_to_block_type("> Quote"), BlockType.QUOTE)
        self.assertEqual(block_to_block_type("- Unordered list item"), BlockType.U_LIST)
        self.assertEqual(block_to_block_type("1. Ordered list item"), BlockType.O_LIST)
        self.assertEqual(block_to_block_type("This is a paragraph"), BlockType.PARAGRAPH)

if __name__ == "__main__":
    unittest.main()