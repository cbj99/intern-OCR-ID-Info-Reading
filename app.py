from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import json
import os
import requests
import time
import csv

# key
subscription_key = ""
# endpoint
endpoint = ""

dirname = os.path.dirname(__file__)
app = Flask(__name__)
# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])
# For a given file, return whether it's an allowed type or not


def allowed_file(filename):
  return '.' in filename and \
      filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def saveAsCSV(table):
    with open("output.csv", 'w', newline='', encoding='utf-8-sig') as file:
        # 表头
        fieldnames = ["姓名", "性别", "民族", "出生日期", "住址", "公民身份号码"]
        writer = csv.DictWriter(file, fieldnames)
        # 写入第一行表头
        writer.writeheader()
        writer.writerows(table)


def getJSON(image_data):

    text_recognition_url = endpoint + "/vision/v3.2/read/analyze"
    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
        'Content-Type': 'application/octet-stream'}
    response = requests.post(text_recognition_url,
                             headers=headers, data=image_data)
    response.raise_for_status()
    operation_url = response.headers["Operation-Location"]
    analysis = {}
    poll = True
    while (poll):
        response_final = requests.get(
            response.headers["Operation-Location"], headers=headers)
        analysis = response_final.json()
        if ("analyzeResult" in analysis):
            poll = False
        if ("status" in analysis and analysis['status'] == 'failed'):
            poll = False
    response.close()
    # print(analysis)
    return analysis


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(dirname, filename)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/uploader', methods=['POST'])
def upload_file():

    if 'file[]' not in request.files:
        return redirect(request.url)
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")

    table=[]
    for file in uploaded_files:
    
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            analysis = getJSON(file)
            
            row = {}
            all_info=''

            # 每页一张身份证, 假设可以同时读取多张
            for page in analysis['analyzeResult']['readResults']:
                for word in page['lines']:

                    all_info+=word['text']

                # 每页一张身份证
                # all_info.replace(' ','')
                # replace() 无法去除中文之间的空格
                all_info=''.join(all_info.split())
                # 姓名 index
                index_1 = all_info.find('姓名')
                # 性别 index
                index_2 = all_info.find('性别')
                # 民族 index
                index_3 = all_info.find('民族')
                # 出生 index
                index_4 = all_info.find('出生')
                # 住址 index
                index_5 = all_info.find('住址')
                # 公民身份证号码 index
                index_6 = all_info.find('公民身份号码')

                row['姓名'] = all_info[index_1+2: index_2]
                row['性别'] = all_info[index_2+2: index_3]
                row['民族'] = all_info[index_3+2: index_4]
                row['出生日期'] = all_info[index_4+2: index_5]
                row['住址'] = all_info[index_5+2: index_6]
                row['公民身份号码'] = all_info[index_6+6:]
                table.append(row)
                row = {}
                all_info=''

    # saveAsCSV(table)
    return render_template('home.html', data=table)
    # return redirect('/uploads/'+'output.csv') 
        

if __name__ == '__main__':
    app.run(debug=True)
