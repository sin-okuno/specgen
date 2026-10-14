#!/usr/bin/env python3
"""Strict Markdown v1.5 -> normalized Screen Model v0.2 (no inference)."""
import argparse
import json
import re
from pathlib import Path
from parser_v01 import parse as parse_legacy, ParseError, CHAPTERS

TABLE_HEADERS = {
 '1.0':'項目|内容','2.1':'領域ID|領域名|領域種別|概要|表示条件','2.2':'表示順|領域ID|配置',
 '3.1':'項目ID|領域ID|項目名|UI種別|データ型|必須|初期値|入力制約|チェックタイミング|エラー文言',
 '3.2':'項目ID|領域ID|項目名|データ型|データ取得元|表示形式|空値表示',
 '3.3':'項目ID|領域ID|項目名|UI種別|イベントID|表示条件|活性条件',
 '3.4':'項目ID|表示条件|活性条件|読取専用条件',
 '3.5':'ルールID|対象項目|検証条件|チェックタイミング|エラー文言',
 '3.6':'候補ID|取得方法|取得元|表示値|内部値',
 '4.1':'処理ID|処理種別|処理内容|実行条件|依存処理|参照先',
 '4.2':'設定先|設定値','4.3':'パラメータ名|種別|データ型|必須|設定先',
 '5.1':'イベントID|イベント名|起動条件|発生元|処理概要',
 '5.2':'イベントID|ステップ|処理種別|処理内容|実行条件|参照先|成功時|失敗時',
 '5.3':'ダイアログID|イベントID|タイトル|メッセージ|OK時|キャンセル時',
 '6.1':'API ID|用途|Method|Endpoint','6.2':'API ID|パラメータ|データ型|必須|設定元|送信形式',
 '6.3':'API ID|フィールド|データ型|必須|NULL許可',
 '6.4':'API ID|Response項目|反映先|反映方式','6.5':'項目|内容',
 '6.6.1':'型名|説明','6.6.2':'型名|フィールド|データ型|必須|NULL許可',
 '6.7':'状態パス|データ型|NULL許可',
 '7.1':'コード定義ID|コード|表示値','7.2':'表示形式|内容','7.3':'値|表示',
 '8.1':'遷移ID|発生イベント|遷移先|遷移条件|パラメータ',
 '8.2':'発生イベント|戻り先|状態復元',
 '8.3':'項目|内容','10.2':'エラーID|発生条件|表示メッセージ|画面動作',
 '11.1':'項目|内容','11.2':'項目|内容','11.3':'項目|内容','11.4':'項目|内容',
 '12.0':'項目|要件','13.0':'受入ID|対象|前提条件|操作|期待結果',
 '14.0':'No.|項目|内容|状態',
}
HEADERS = {k:v.split('|') for k,v in TABLE_HEADERS.items()}
SUBSECTIONS = {1:[],2:[1,2],3:list(range(1,7)),4:[1,2,3],5:[1,2,3],6:list(range(1,8)),7:[1,2,3],8:[1,2,3],9:[1,2],10:[1,2],11:[1,2,3,4],12:[],13:[],14:[]}
NAMES = {'2.1':'areas','2.2':'layout','3.1':'inputs','3.2':'displays','3.3':'actions','3.4':'controls','3.5':'cross_validations','3.6':'options','4.1':'initialization','4.2':'defaults','4.3':'route_parameters','5.1':'events','5.2':'event_steps','5.3':'dialogs','6.1':'apis','6.2':'requests','6.3':'responses','6.4':'response_mappings','6.5':'api_policies','7.1':'codes','7.2':'formats','7.3':'empty_values','8.1':'navigation','8.2':'back_navigation','8.3':'unsaved_changes','10.2':'screen_errors','13.0':'acceptance_criteria'}


def preflight(text):
    chapter = None
    seen_chapters = set()
    seen_sections = set()
    in_fence = False
    for n,line in enumerate(text.splitlines(),1):
        if re.match(r'^\s*```',line):
            in_fence = not in_fence
            continue
        if in_fence:
            raise ParseError('MD_FENCE',n,'コードフェンスはv1.5仕様書で未対応です')
        if line.startswith('## 変更履歴'):
            chapter = None
            continue
        m = re.match(r'^## (\d+)\. (.*)$',line)
        if m:
            k=int(m[1]); chapter=k
            if k in seen_chapters: raise ParseError('MD_DUPLICATE',n,'章が重複しています')
            seen_chapters.add(k)
        m = re.match(r'^### (\d+)\.(\d+) (.*)$',line)
        if m:
            k=int(m[1]); i=int(m[2]); key=f'{k}.{i}'
            if chapter != k or i not in SUBSECTIONS.get(k,[]):
                raise ParseError('MD_SECTION',n,f'節の位置または番号が不正: {key}')
            if key in seen_sections: raise ParseError('MD_DUPLICATE',n,f'節が重複: {key}')
            seen_sections.add(key)
        if line.startswith('|') and '\n' in line:
            raise ParseError('MD_TABLE',n,'複数行セルは禁止')
    if in_fence: raise ParseError('MD_FENCE',0,'コードフェンスが閉じていません')
    required={f'{k}.{i}' for k,nums in SUBSECTIONS.items() for i in nums}
    missing=sorted(required-seen_sections,key=lambda s:tuple(map(int,s.split('.'))))
    if missing: raise ParseError('MD_REQUIRED',0,'必須節がありません: '+','.join(missing))


def parse(path):
    path=Path(path)
    text=path.read_text(encoding='utf-8-sig')
    preflight(text)
    # The v0.1 reader accidentally attaches the unnumbered change-history table to chapter 14.
    # Strip history only from the input passed to the legacy reader; source stays unchanged.
    source=text.split('## 変更履歴',1)[0]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)/path.name
        tmp.write_text(source,encoding='utf-8')
        raw=parse_legacy(tmp)
    for key,sec in raw['sections'].items():
        if key=='6.6':
            for t in sec['tables']:
                k=t['subsection']
                if k not in HEADERS or t['headers'] != HEADERS[k]:
                    raise ParseError('MD_HEADER',t['line'],f'{k}の表ヘッダーが不正')
        else:
            for t in sec['tables']:
                if key not in HEADERS or t['headers'] != HEADERS[key]:
                    raise ParseError('MD_HEADER',t['line'],f'{key}の表ヘッダーが不正')
        if sec['status']=='not_applicable' and any(t['rows'] for t in sec['tables']):
            raise ParseError('MD_STATUS',0,f'{key}: 対象外とデータ行は同時に記述できません')
    def rows(key,sub=None):
        return [{'line':r['line'],**r['values']} for t in raw['sections'].get(key,{}).get('tables',[])
                if t['subsection']==sub for r in t['rows']]
    normalized={name:rows(key) for key,name in NAMES.items()}
    normalized['screen_properties']=rows('1.0')
    normalized['named_type_catalog']=rows('6.6','6.6.1')
    normalized['named_type_fields']=rows('6.6','6.6.2')
    normalized['state_types']=rows('6.7')
    normalized['screen_specific']={k:rows(k) for k in ('11.1','11.2','11.3','11.4')}
    normalized['non_functional']=rows('12.0')
    normalized['open_items']=rows('14.0')
    normalized['section_status']={k:s['status'] for k,s in raw['sections'].items()}
    return {'schema_version':'0.2','source':path.name,'metadata':raw['metadata'],
            'chapters':raw['chapters'],'named_types':raw['named_types'],
            'state_types':raw['state_types'],'model':normalized}


def main():
    ap=argparse.ArgumentParser(description='Strict Markdown v1.5 -> Screen Model v0.2')
    ap.add_argument('input',type=Path)
    ap.add_argument('-o','--output',type=Path)
    args=ap.parse_args()
    try:
        result=parse(args.input)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        else: print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ParseError,OSError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False))
        raise SystemExit(1)
if __name__=='__main__': main()
