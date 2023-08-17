from flask import Flask, render_template, request, jsonify
import os, sys, json

app = Flask(__name__)

# 웹 페이지에서 컨테이너 생성 요청이 왔을 때
# data : port, 비밀번호
# 완료됐다고 응답 (컨테이너 상태)
@app.route('/create', methods=['POST'])
def create():
    print(request.headers)
    data = request.get_json()
    port = str(data['port'])
    pwd = str(data['password'])
    print(data)
    cmd = "docker run -d -p "+port+":6901 --rm -e VNC_PW="+pwd+" test1:latest"
    #res = os.system(cmd)
    #print("res : ", res)
    
    stream = os.popen(cmd)
    containerId = stream.read()[:12]
    print("containerId : ", containerId)
    
    response = {
            'port': port,
            'containerId' : containerId,
        }
    
    return jsonify(response), 200


@app.route('/delete', methods=['POST'])
def delete():
    print(request.headers)
    data = request.get_json()
    port = str(data['port'])
    containerId = str(data['containerId'])
    print(data)
    cmd = "docker stop "+containerId;
    
    stream = os.popen(cmd)
    
    response = {
            'containerId' : containerId
        }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run()