from flask import Flask, render_template, request, jsonify
import os, sys, json

app = Flask(__name__)


# 웹 페이지에서 컨테이너 생성 요청이 왔을 때
@app.route('/create', methods=['POST'])
def create():
    print("create request - ", request.headers)
    
    requestDTO = request.get_json()  # spring에서 온 요청 데이터
    print("requestDTO - ", requestDTO)
    port, pwd = str(requestDTO['port']), str(requestDTO['password'])
    
    cmd = "docker run -d -p "+port+":6901 -e VNC_PW="+pwd+" test1:latest"  # 지정된 port로 가상환경 실행 
    stream = os.popen(cmd)
    containerId = stream.read()[:12]
    
    response = {
            'port': port,
            'containerId' : containerId,
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 중지 요청이 왔을 때 
@app.route('/start', methods=['POST'])
def start():
    print("start request - ", request.headers)
    
    requestDTO = request.get_json()
    print("requestDTO - ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    cmd = "docker start "+containerId;
    os.popen(cmd)
    
    response = {
            'containerId' : containerId
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 중지 요청이 왔을 때 
@app.route('/stop', methods=['POST'])
def stop():
    print("stop request - ", request.headers)
    
    requestDTO = request.get_json()
    print("requestDTO - ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    cmd = "docker stop "+containerId;
    os.popen(cmd)
    
    response = {
            'containerId' : containerId
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 삭제 요청이 왔을 때
@app.route('/delete', methods=['POST'])
def delete():
    print("delete request - ", request.headers)
    
    requestDTO = request.get_json()
    print("requestDTO - ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    cmd = "docker rm "+containerId;
    os.popen(cmd)
    
    response = {
            'containerId' : containerId
        }
    
    return jsonify(response), 200

if __name__ == '__main__':
    app.run()