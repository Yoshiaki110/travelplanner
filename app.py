# -*- coding: utf-8 -*-

import os
import time
from flask import Flask, redirect, render_template, request, jsonify, make_response, send_file
import base64
import uuid
import socket
from io import BytesIO
import datetime
import requests
import json
import ftplib
from openai import OpenAI
#import tp_pyqubo as tp
#import tp_tytan as tp
import tp_amplify_ttn as tp

OPENAI_KEY = os.environ['OPENAI_KEY']
GOOGLEMAP_KEY = os.environ['GOOGLEMAP_KEY']
DWAVE_KEY = os.environ['DWAVE_KEY']
AMPLIFY_KEY = os.environ['AMPLIFY_KEY']

app = Flask(__name__)
openai_client = OpenAI(api_key=OPENAI_KEY)

#
# トラベルプランナー
#
@app.route('/')
def tp_iphone():
    print("** / " + request.method)
    #tp.tp_init(DWAVE_KEY)
    tp.tp_init(AMPLIFY_KEY)
    resp = make_response(render_template("index.html", GOOGLEMAP_KEY = GOOGLEMAP_KEY))
    return resp

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

if __name__ == '__main__':
  app.run(debug=True)
