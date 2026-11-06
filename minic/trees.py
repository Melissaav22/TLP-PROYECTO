"""Serialización iterativa y visualización SVG sin dependencias adicionales."""
from html import escape
from pathlib import Path
from nltk import Tree


def bracketed(tree):
    parts = []
    pending = [tree]
    while pending:
        item = pending.pop()
        if isinstance(item, Tree):
            parts.append('(' + item.label())
            pending.append(')')
            for child in reversed(item):
                pending.extend([child, ' '])
        else:
            parts.append(str(item))
    return ''.join(parts)


def leaves(tree):
    result = []
    pending = [tree]
    while pending:
        item = pending.pop()
        if isinstance(item, Tree):
            pending.extend(reversed(item))
        else:
            result.append(str(item))
    return result


def tree_data(tree):
    root = {'label': tree.label(), 'children': []}
    pending = [(tree, root)]
    while pending:
        node, target = pending.pop()
        for child in node:
            if isinstance(child, Tree):
                nested = {'label': child.label(), 'children': []}
                target['children'].append(nested)
                pending.append((child, nested))
            else:
                target['children'].append(str(child))
    return root


def print_tree(tree):
    pending = [(tree, 0)]
    visited = 0
    while pending:
        node, depth = pending.pop()
        visited += 1
        if depth > 60 or visited > 500:
            print(bracketed(tree))
            return
        if isinstance(node, Tree):
            pending.extend((child, depth + 1) for child in node)
    tree.pretty_print()


def write_svg(tree, path, max_nodes=2000):
    nodes = []
    pending = [(tree, None, 0)]
    while pending:
        item, parent, depth = pending.pop()
        index = len(nodes)
        if index >= max_nodes:
            raise ValueError(f'La vista SVG admite hasta {max_nodes} nodos')
        label = item.label() if isinstance(item, Tree) else str(item)
        nodes.append(dict(label=label, parent=parent, depth=depth, children=[]))
        if parent is not None:
            nodes[parent]['children'].append(index)
        if isinstance(item, Tree):
            pending.extend((child, index, depth + 1) for child in reversed(item))
    next_leaf = 0
    for node in nodes:
        if not node['children']:
            node['x'] = 65 + next_leaf * 110
            next_leaf += 1
        node['y'] = 35 + node['depth'] * 65
    for node in reversed(nodes):
        if node['children']:
            node['x'] = sum(nodes[i]['x'] for i in node['children']) / len(node['children'])
    width = max(250, next_leaf * 110 + 30)
    height = max(node['y'] for node in nodes) + 50
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="white"/>']
    for node in nodes:
        if node['parent'] is not None:
            parent = nodes[node['parent']]
            body.append(f'<line x1="{parent["x"]}" y1="{parent["y"] + 7}" x2="{node["x"]}" y2="{node["y"] - 18}" stroke="#93a5ba"/>')
        body.append(f'<text x="{node["x"]}" y="{node["y"]}" text-anchor="middle" font-family="Arial" font-size="13" fill="#172a45"><title>{escape(node["label"])}</title>{escape(node["label"][:32])}</text>')
    body.append('</svg>')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(body), encoding='utf-8')
