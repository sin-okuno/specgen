#!/usr/bin/env python3
"""Deterministic Markdown -> structured Screen Model v0.1."""
import argparse
import json
import re
from pathlib import Path

SECTION_HEADERS = {
    '6.6.1': ['型名', '説明'],
    '6.6.2': ['型名', 'フィールド', 'データ型', '必須', 'NULL許可'],
    '6.7': ['状態パス', 'データ型', 'NULL許可'],
}
CHAPTERS = ['画面基本情報','画面構成','画面項目定義','初期表示仕様','イベント・操作仕様',
            'API連携仕様','データ表示・変換仕様','画面遷移仕様','権限制御',
            'エラーハンドリング','画面固有仕様','非機能要件','受入条件','補足・未決事項']

class ParseError(ValueError):
    def __init__(self, code, line, message):
        super().__init__(f'{code} line {line}: {message}')
        self.code, self.line, self.message = code, line, message

def cells_of(line, lineno):
    if not line.startswith('|') or not line.rstrip().endswith('|'):
        raise ParseError('MD_TABLE', lineno, '表は両端に | が必要です')
    content = line.strip()[1:-1]
    # Markdown pipe escapes: \\| is a literal pipe; retain other backslashes.
    return [s.strip().replace('\\|', '|') for s in re.split(r'(?<!\\)\|', content)]

def parse(path):
    path = Path(path)
    text = path.read_text(encoding='utf-8-sig')
    chapters = []
    sections = {}
    section = None
    subheading = None
    active_table = None
    metadata = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        m = re.match(r'^## (\d+)\. (.+?)\s*$', line)
        if m:
            number, title = int(m.group(1)), m.group(2)
            if number < 1 or number > 14 or title != CHAPTERS[number - 1]:
                raise ParseError('MD_CHAPTER', lineno, f'章名が不正: {line}')
            chapters.append(number)
            section, active_table, subheading = f'{number}.0', None, None
            sections[section] = {'title': title, 'status': 'present', 'tables': [], 'notes': []}
            continue
        m = re.match(r'^### (\d+\.\d+) (.+?)\s*$', line)
        if m:
            section = m.group(1)
            if section in sections:
                raise ParseError('MD_DUPLICATE', lineno, f'節の重複: {section}')
            sections[section] = {'title': m.group(2), 'status': 'present', 'tables': [], 'notes': []}
            active_table, subheading = None, None
            continue
        m = re.match(r'^#### (\d+\.\d+\.\d+) (.+?)\s*$', line)
        if m:
            if not section or not m.group(1).startswith(section + '.'):
                raise ParseError('MD_SUBSECTION', lineno, '小節が親節と一致しません')
            subheading, active_table = m.group(1), None
            continue
        if line.startswith('**仕様書バージョン：**'):
            metadata['version'] = line.split('**', 2)[-1].strip()
        if line.startswith('**画面種別：**'):
            metadata['declared_screen_type'] = line.split('**', 2)[-1].strip()
        if not section:
            continue
        obj = sections[section]
        if line.strip() == '対象外':
            obj['status'] = 'not_applicable'
            continue
        if line.startswith('|'):
            cells = cells_of(line, lineno)
            if all(re.fullmatch(r':?-{3,}:?', c) for c in cells):
                if active_table is None or active_table['separator_seen']:
                    raise ParseError('MD_TABLE', lineno, '表の区切り行が不正')
                active_table['separator_seen'] = True
                continue
            if active_table is None:
                active_table = {'subsection': subheading, 'headers': cells, 'rows': [], 'line': lineno, 'separator_seen': False}
                obj['tables'].append(active_table)
                expected = SECTION_HEADERS.get(subheading or section)
                if expected and cells != expected:
                    raise ParseError('MD_HEADER', lineno, f'{subheading or section} の列名が不正')
            else:
                if not active_table['separator_seen']:
                    raise ParseError('MD_TABLE', lineno, '表ヘッダーの次に区切り行が必要')
                if len(cells) != len(active_table['headers']):
                    raise ParseError('MD_COLUMNS', lineno, '列数が一致しません')
                active_table['rows'].append({'values': dict(zip(active_table['headers'], cells)), 'line': lineno})
        elif line.strip():
            active_table = None
            obj['notes'].append({'text': line.strip(), 'line': lineno, 'subsection': subheading})
        else:
            active_table = None
    if chapters != list(range(1, 15)):
        raise ParseError('MD_CHAPTER', 0, '14章の存在・順序が不正')
    for key, sec in sections.items():
        for table in sec['tables']:
            if not table['separator_seen']:
                raise ParseError('MD_TABLE', table['line'], '区切り行がありません')
    info = {}
    for t in sections.get('1.0', {}).get('tables', []):
        info.update({r['values']['項目']: r['values']['内容'] for r in t['rows']})
    # Chapter 1 is a direct table, outside numbered subsections. Extract explicitly.
    in_chapter1 = False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('## 1. '): in_chapter1 = True; continue
        if line.startswith('## 2. '): break
        if in_chapter1 and line.startswith('|'):
            vals = cells_of(line, i + 1)
            if len(vals) == 2 and vals[0] not in ('項目', '---') and not vals[0].startswith('---'):
                info[vals[0]] = vals[1]
    required = ['画面ID', '画面名', '画面種別', 'URL']
    for field in required:
        if not info.get(field):
            raise ParseError('MD_METADATA', 0, f'画面基本情報に{field}がありません')
    if info['画面種別'] not in ('LIST','CREATE','EDIT','DETAIL'):
        raise ParseError('MD_METADATA', 0, '画面種別が不正')
    if metadata.get('declared_screen_type') != info['画面種別']:
        raise ParseError('MD_METADATA', 0, '冒頭と1章の画面種別が不一致')
    def rows(section, sub=None):
        return [r['values'] for t in sections.get(section, {}).get('tables', [])
                if t['subsection'] == sub for r in t['rows']]
    types = {}
    for row in rows('6.6', '6.6.1'):
        name = row['型名']
        if name in types: raise ParseError('MD_TYPE', 0, f'型の重複: {name}')
        types[name] = {'description': row['説明'], 'fields': []}
    for row in rows('6.6', '6.6.2'):
        name = row['型名']
        if name not in types: raise ParseError('MD_TYPE', 0, f'型未宣言: {name}')
        types[name]['fields'].append({'name': row['フィールド'], 'type': row['データ型'],
                                      'required': row['必須'] == 'Yes', 'nullable': row['NULL許可'] == 'Yes'})
    states = [{'path': r['状態パス'], 'type': r['データ型'], 'nullable': r['NULL許可'] == 'Yes'} for r in rows('6.7')]
    return {'schema_version': '0.1', 'source': path.name, 'metadata': {'version': metadata.get('version', ''),
            'screen_id': info['画面ID'], 'screen_name': info['画面名'], 'screen_type': info['画面種別'], 'url': info['URL']},
            'chapters': chapters, 'sections': sections, 'named_types': types, 'state_types': states}

def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('input', type=Path)
    cli.add_argument('-o', '--output', type=Path)
    args = cli.parse_args()
    try:
        result = parse(args.input)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + '\n', encoding='utf-8')
        else: print(output)
    except (ParseError, OSError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
if __name__ == '__main__': main()
