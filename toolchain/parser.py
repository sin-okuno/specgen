#!/usr/bin/env python3
"""Screen Model v0.3: deterministic normalized keys, preserving source lines."""
import argparse
import json
from pathlib import Path
from parser_v02 import parse as parse_v02, ParseError, HEADERS, NAMES

# Canonical names, independent of the Japanese table headers.
COLUMN_KEYS = {
 '項目':'item','内容':'value','領域ID':'area_id','領域名':'area_name','領域種別':'area_type','概要':'description','表示条件':'visibility_condition',
 '表示順':'display_order','配置':'position','項目ID':'field_id','項目名':'label','UI種別':'ui_type','データ型':'data_type','必須':'required',
 '初期値':'default_value','入力制約':'constraints','チェックタイミング':'validation_timing','エラー文言':'error_message',
 'データ取得元':'source','表示形式':'display_format','空値表示':'empty_display','イベントID':'event_id','活性条件':'enabled_condition',
 '読取専用条件':'readonly_condition','ルールID':'rule_id','対象項目':'target_fields','検証条件':'expression','候補ID':'option_id',
 '取得方法':'fetch_method','取得元':'option_source','表示値':'display_value','内部値':'internal_value','処理ID':'init_id',
 '処理種別':'operation','処理内容':'operation_description','実行条件':'condition','依存処理':'depends_on','参照先':'reference',
 '設定先':'destination','設定値':'value','パラメータ名':'parameter','種別':'kind','イベント名':'event_name','起動条件':'trigger',
 '発生元':'origin','処理概要':'description','ステップ':'step','成功時':'on_success','失敗時':'on_failure','ダイアログID':'dialog_id',
 'タイトル':'title','メッセージ':'message','OK時':'on_confirm','キャンセル時':'on_cancel','API ID':'api_id','用途':'purpose',
 'Method':'method','Endpoint':'endpoint','パラメータ':'parameter','設定元':'source','送信形式':'location','フィールド':'field',
 'NULL許可':'nullable','Response項目':'response_field','反映先':'destination','反映方式':'mapping_mode','型名':'type_name',
 '説明':'description','状態パス':'state_path','コード定義ID':'code_id','コード':'code','表示値':'display_value','値':'value',
 '表示':'display','遷移ID':'nav_id','発生イベント':'event_id','遷移先':'target','遷移条件':'condition','戻り先':'target',
 '状態復元':'restore_mode','エラーID':'error_id','発生条件':'condition','表示メッセージ':'message','画面動作':'behavior',
 '要件':'requirement','受入ID':'acceptance_id','対象':'target','前提条件':'precondition','操作':'action','期待結果':'expected',
 'No.':'number','状態':'status'
}
# A field name may have a context-specific meaning, so disambiguate explicitly.
OVERRIDES = {
 '3.2':{'項目ID':'field_id','データ取得元':'source'},
 '3.4':{'項目ID':'field_id'},
 '4.2':{'設定先':'destination','設定値':'value'},
 '4.3':{'設定先':'destination'},
 '6.3':{'フィールド':'field'},
 '6.4':{'Response項目':'response_field'},
 '6.6.2':{'フィールド':'field'},
 '8.1':{'パラメータ':'parameters'},
 '14.0':{'項目':'topic','内容':'description'}
}
NAME_TO_SECTION={v:k for k,v in NAMES.items()}
NAME_TO_SECTION.update({'screen_properties':'1.0','named_type_catalog':'6.6.1','named_type_fields':'6.6.2','state_types':'6.7','non_functional':'12.0','open_items':'14.0'})

def convert_rows(rows, section):
    mapping={h:OVERRIDES.get(section,{}).get(h,COLUMN_KEYS.get(h)) for h in HEADERS[section]}
    if any(v is None for v in mapping.values()):
        raise ValueError(f'Missing column mapping: {section}')
    if len(set(mapping.values()))!=len(mapping):
        raise ValueError(f'Duplicate normalized keys: {section}')
    return [{'line':r['line'],**{mapping[h]:r[h] for h in HEADERS[section]}} for r in rows]

def parse(path):
    legacy=parse_v02(path)
    raw=legacy['model']
    model={}
    for name, section in NAME_TO_SECTION.items():
        model[name]=convert_rows(raw[name],section)
    model['screen_specific']={key:convert_rows(rows,key) for key,rows in raw['screen_specific'].items()}
    model['section_status']=raw['section_status']
    return {'schema_version':'0.3','source':legacy['source'],'metadata':legacy['metadata'],
            'chapters':legacy['chapters'],'model':model}

def main():
    cli=argparse.ArgumentParser();cli.add_argument('input',type=Path);cli.add_argument('-o','--output',type=Path)
    a=cli.parse_args()
    try:
        result=parse(a.input)
        output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if a.output:
            a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(output,encoding='utf-8')
        else:print(output,end='')
    except (ParseError,OSError,ValueError) as e:
        print(json.dumps({'error':str(e)},ensure_ascii=False));raise SystemExit(1)
if __name__=='__main__':main()
