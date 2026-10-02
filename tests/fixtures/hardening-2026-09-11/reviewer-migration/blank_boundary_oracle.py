"""Development-only independent Markdown oracle for HTML blank-line boundary."""
import importlib.metadata
import json
from markdown_it import MarkdownIt

assert importlib.metadata.version('markdown-it-py') == '4.0.0'
parser = MarkdownIt('commonmark').enable('table')
observations = []
for opener in ('<br>', '<div></div>', '<div/>'):
    for separated in (False, True):
        source = opener + '\n' + ('\n' if separated else '') + '| Item | Notes |\n|---|---|\n| Example parser | demo |\n\n- Actual finding.\n'
        tokens = parser.parse(source)
        tables = [token for token in tokens if token.type == 'table_open']
        assert bool(tables) == separated
        observations.append({'source': source, 'blank_after_opener': separated,
                             'pipe_table_is_live': bool(tables),
                             'boundary_tokens': [{'type': token.type, 'lines': token.map, 'content': token.content}
                                                 for token in tokens if token.type in {'html_block', 'table_open'}]})
print(json.dumps({'parser': 'markdown-it-py 4.0.0; commonmark preset plus table extension', 'observations': observations}, indent=2))
