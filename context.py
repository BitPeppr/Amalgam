import json
from pathlib import Path

IGNORE = ['.venv', 'venv', 'env', '.env', 'node_modules', 'dist', 'build', '__pycache__', '.git', '.github', '.vscode', '.idea', '.pytest_cache', '.mypy_cache', '.tox', '.eggs', 'site-packages', 'target', '.notes', '.cache', '.local', '.config', '.cargo', '.rustup', '.nvm', '.npm', '.yarn', '.pnpm', 'vendor', 'third_party', '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes', '.editorconfig', '.prettierignore', '.eslintignore', '.dockerignore', '.npmignore', '.pyc']
EXTENSIONS = {
    '.py', '.ts', '.js', '.tsx', '.jsx',
    '.rs', '.go', '.rb', '.java', '.kt',
    '.md', '.rst', '.txt',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.css', '.html', '.scss', '.less',
    '.sh', '.bash', '.zsh', '.fish',
    '.sql', '.graphql',
    '.c', '.h', '.cpp', '.hpp',
    '.swift',
}

def _is_ignored(path):
    return any(part in IGNORE for part in path.parts)

def tree(root='.'):
    root = Path(root)
    tree = {}
    for path in sorted(root.rglob('*')):
        if _is_ignored(path.relative_to(root)):
            continue
        parts = path.relative_to(root).parts
        d = tree
        for part in parts[:-1]:
            d = d.setdefault(part, {})
        d[parts[-1]] = {} if path.is_dir() else None
    return tree
def format_tree(tree, prefix=""):
    items = list(tree.items())
    lines = []
    for i, (name, subtree) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{name}/" if subtree is not None else f"{prefix}{connector}{name}")
        if subtree is not None:
            extension = "    " if is_last else "│   "
            lines.extend(format_tree(subtree, prefix + extension))
    return lines

def collect_files(root='.'):
    files = []
    for path in Path(root).rglob('*'):
        if not path.is_file():
            continue
        if _is_ignored(path.relative_to(root)):
            continue
        if path.suffix not in EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)



def build_json(root):
    files = collect_files(root)
    data = {str(f.relative_to(root)): f.read_text() for f in files}
    return json.dumps(data, indent=2)


def find_context():
    tree_data = format_tree(tree())
    tree_str = "\n".join(tree_data)

    files = collect_files()
    parts = []
    for f in files:
        content = f.read_text()
        chunk = f"<file path='{f.relative_to('.')}' size='{len(content)}'>\n{content}\n</file>\n"
        parts.append(chunk)
    header = f"<files count='{len(files)}'>\n"
    return tree_str + "\n\n" + header + "".join(parts) + "</files>"       
