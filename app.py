# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template, request, jsonify, make_response
import datetime
import time
import requests
import json
from openai import OpenAI
#import tp_pyqubo as tp
#import tp_tytan as tp
#import tp_amplify_ttn as tp
import tp_amplify_mtmt as tp

OPENAI_KEY = os.environ['OPENAI_KEY']
GOOGLEMAP_KEY = os.environ['GOOGLEMAP_KEY']
DWAVE_KEY = os.environ['DWAVE_KEY']
AMPLIFY_KEY = os.environ['AMPLIFY_KEY']
NAVITIME_KEY = os.environ['NAVITIME_KEY']

app = Flask(__name__)
openai_client = OpenAI(api_key=OPENAI_KEY)
navitime_call_time = time.time()

#
# トラベルプランナー
#
@app.route('/')
def tp_index():
    print("** / " + request.method)
    #tp.tp_init(DWAVE_KEY)
    tp.tp_init(AMPLIFY_KEY)
    #resp = make_response(render_template("index.html", GOOGLEMAP_KEY = GOOGLEMAP_KEY))
    resp = make_response(render_template("navi.html", GOOGLEMAP_KEY = GOOGLEMAP_KEY))
    return resp

@app.route('/realtime')
def tp_realtime():
    print("** /realtime " + request.method)
    #tp.tp_init(DWAVE_KEY)
    tp.tp_init(AMPLIFY_KEY)
    resp = make_response(render_template("realtime.html", GOOGLEMAP_KEY = GOOGLEMAP_KEY))
    return resp

@app.route('/navi')
def tp_navi():
    print("** /navi " + request.method)
    #tp.tp_init(DWAVE_KEY)
    tp.tp_init(AMPLIFY_KEY)
    resp = make_response(render_template("navi.html", GOOGLEMAP_KEY = GOOGLEMAP_KEY))
    return resp

@app.route('/area')
def tp_area():
    print("** /area " + request.method)
    with open("./areas_s.json", "r", encoding="utf-8") as f:
        ret = json.load(f)
        return jsonify(ret)


@app.route('/guida')
def tp_guidance():
    print("** /guida " + request.method)
    name = request.args.get('name', '')
    distance = request.args.get('distance', '')
    lat = request.args.get('lat', '')
    lng = request.args.get('lng', '')

    res = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "京都にある観光地について200文字程度で教えてください。"},  # 役割設定（省略可）
            {"role": "user", "content": name + "について解説をお願いします。その観光地の名称や位置についての情報は不要です。"}               # 最初の質問
            # 位置を指定した場合temperature=0にしないとダメ、また清水寺と金閣寺しか回答しない
            #{"role": "system", "content": "指定の地点から1km以内にある観光地について200文字程度で教えてください。"},  # 役割設定（省略可）
            #{"role": "user", "content": '緯度' + lat + '、緯度' + lng + 'に一番近い観光地の情報を教えてください。緯度と経度は回答しないでください。'}               # 最初の質問
        ],
        temperature=0  # 温度（0-2, デフォルト1）
    )
    print(res.choices[0].message.content)  # 答えが返る
    return jsonify({'text': res.choices[0].message.content})

@app.route("/api", methods=['POST'])
def tp_api():
    print("** /api " + request.method)
    indexs = request.json['indexs']
    print(indexs)
    table = request.json['table']
    print(table)
    ret = tp.tp_api(indexs, table)
    print(ret)
    return jsonify(ret)

@app.route("/tsp", methods=['POST'])
def tp_tsp():
    print("** /tsp " + request.method)
    table = request.json['table']
    print(table)
    tp.tp_init(AMPLIFY_KEY)
    ret = tp.tp_tsp(table)
    print(ret)
    return jsonify(ret)

@app.route("/route")
def tp_route():
    global navitime_call_time
    print("** /route " + request.method)
    req = request.args
    start = req.get("start")
    #startName = req.get("startName")
    goal = req.get("goal")
    #goalName = req.get("goalName")

    path = './route/' + start + '_' + goal + '.json'
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            ret = json.load(f)
            return jsonify(ret)

    ctime = time.time()
    if ctime - navitime_call_time < 0.2:
        time.sleep(0.2)
    navitime_call_time = ctime

    now = datetime.datetime.now()
    querystring = {
      "start": start,
      "goal": goal,
      "start_time": now.strftime('%Y-%m-%dT%H:%M:%S'),
      "limit": '1'
    }
    url = "https://navitime-route-totalnavi.p.rapidapi.com/route_transit"
    headers = {
        "X-RapidAPI-Key": NAVITIME_KEY,
        "X-RapidAPI-Host": "navitime-route-totalnavi.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    res = response.json()
    item = res['items'][0]
    if 'fare' in item['summary']['move']:
        print('所要時間', item['summary']['move']['time'], '料金', item['summary']['move']['fare']['unit_0'])
    else:
        print('所要時間', item['summary']['move']['time'])
    route = ''
    for section in item['sections']:
        if section['type'] == 'point':
            print(section['name'])
            name = section['name']
            #name = startName if name == 'start' else name
            #name = goalName if name == 'goal' else name
            route += name + '\n'
        if section['type'] == 'move':
            print('', section['line_name'], section['distance'], section['time'] )
            route += '　' + section['line_name'] + '（' + str(section['time']) + '分 ' + str(section['distance']) + 'm）\n'
    ret = {
        'time': item['summary']['move']['time'],
        'fare': 0 if not 'fare' in item['summary']['move'] else item['summary']['move']['fare']['unit_0'],
        'route': route,
    }
    with open(path, 'w', encoding="utf-8") as f:
        json.dump(ret, f, indent=2, ensure_ascii=False)
    return jsonify(ret)

if __name__ == '__main__':
  app.run(debug=True)
