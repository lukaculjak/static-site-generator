class HTMLNode:
    def __init__(self, tag=None, value=None, children=None, props=None):
        self.tag = tag
        self.value = value
        self.children = children if children is not None else []
        self.props = props if props is not None else {}

    def to_html(self):
        raise NotImplementedError("to_html method must be implemented by subclasses")

    def props_to_html(self):
        return " ".join(f'{key}="{value}"' for key, value in self.props.items())

    def __repr__(self):
        return f"HTMLNode(tag={self.tag!r}, value={self.value!r}, children={self.children!r}, props={self.props!r})"

    def render(self):
        inner_html = "".join(child.render() if isinstance(child, HTMLNode) else str(child) for child in self.children)
        props_str = self.props_to_html()
        if props_str:
            props_str = " " + props_str
        return f"<{self.tag}{props_str}>{self.value}{inner_html}</{self.tag}>"

class LeafNode(HTMLNode):
    def __init__(self, tag, value, props=None):
        super().__init__(tag=tag, value=value, children=[], props=props)

    def to_html(self):
        if self.tag is None:
            return self.value
        if self.tag == "img":
            return f"<img{' ' + self.props_to_html() if self.props else ''}>"
        return f"<{self.tag}{' ' + self.props_to_html() if self.props else ''}>{self.value}</{self.tag}>".strip()

    def __repr__(self):
        return f"LeafNode(tag={self.tag!r}, value={self.value!r}, props={self.props!r})"

class ParentNode(HTMLNode):
    def __init__(self, tag, children, props=None):
        super().__init__(tag=tag, children=children, props=props)

    def to_html(self):
        if not self.tag:
            raise ValueError("ParentNode must have a tag")
        if not self.children:
            raise ValueError("ParentNode must have children")
        inner_html = "".join(child.to_html() if isinstance(child, HTMLNode) else str(child) for child in self.children)
        props_str = self.props_to_html()
        if props_str:
            props_str = " " + props_str
        return f"<{self.tag}{props_str}>{inner_html}</{self.tag}>"

    def __repr__(self):
        return f"ParentNode(tag={self.tag!r}, value={self.value!r}, children={self.children!r}, props={self.props!r})"