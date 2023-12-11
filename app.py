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
import tp_tytan as tp

app = Flask(__name__)
openai_client = OpenAI(api_key='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')

#
# トラベルプランナー
#
@app.route('/')
def tp_iphone():
    print("** / " + request.method)
    resp = make_response(render_template("index.html"))
    return resp

@app.route('/guida')
def tp_guidance():
    print("** /guida " + request.method)
    name = request.args.get('name', '')
    distance = request.args.get('distance', '')

    res = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "京都にある観光地について200文字程度で教えてください。"},  # 役割設定（省略可）
            {"role": "user", "content": name + "について解説をお願いします。その観光地の名称や位置についての情報は不要です。"}               # 最初の質問
        ],
        temperature=1  # 温度（0-2, デフォルト1）
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
