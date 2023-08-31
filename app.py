from flask import Flask, render_template, request, jsonify
import os, sys, json, time

app = Flask(__name__)

def createContainerCmd(port, userId, pwd) : # port, pwd로 컨테이너 생성
    return "docker create -p "+port+":6901 -e VNC_PW="+pwd+" registry.p2kcloud.com/base/"+userId+":"+port

def startContainerCmd(containerId) : # containerid로 컨테이너 실행
    return "docker start "+containerId

def stopContainerCmd(containerId) : # containerid로 컨테이너 중지
    return "docker stop "+containerId

def deleteContainerCmd(containerId) :
    return "docker rm "+containerId

def findImgIdCmd(userId, port) :
    return "docker images registry.p2kcloud.com/base/"+userId+":"+port+" -q"

def saveImgCmd(containerId, userId, port) : # 새로운 이미지 저장 
    return "docker commit "+containerId+" registry.p2kcloud.com/base/"+userId+":"+port
    
def pushImgCmd(userId, port) :
    return "docker push registry.p2kcloud.com/base/"+userId+":"+port

def deleteImgCmd(userId, port) :
    return "docker rmi -f registry.p2kcloud.com/base/"+userId+":"+port



# 웹 페이지에서 컨테이너 생성 요청이 왔을 때, 컨테이터 run하고 이미지 저장
@app.route('/create', methods=['POST'])
def create():
    requestDTO = request.get_json()  # spring에서 온 요청 데이터
    print("[create requestDTO] ", requestDTO)
    port, pwd = str(requestDTO['port']), str(requestDTO['password'])
    
    cmd1 = "docker pull registry.p2kcloud.com/base/vncdesktop"  # harbor에서 kasm 이미지 pull
    os.popen(cmd1)
    time.sleep(8)
    
    cmd2 = "docker images registry.p2kcloud.com/base/vncdesktop -q"  # 이미지 id 추출
    stream2 = os.popen(cmd2)
    imageId = stream2.read()[:12]
    
    cmd = "docker create -p "+port+":6901 -e VNC_PW="+pwd+" registry.p2kcloud.com/base/vncdesktop" # 컨테이너 생성
    stream = os.popen(cmd)
    containerId = stream.read()[:12]

    response = {
            'port': port,
            'containerId' : containerId,
            'imageId' : imageId
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 실행 요청이 왔을 때, 컨테이너 실행
@app.route('/start', methods=['POST'])
def start():    
    requestDTO = request.get_json()
    print("[start requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    # 컨테이너 실행 cmd
    os.popen(startContainerCmd(containerId))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 중지 요청이 왔을 때, 컨테이너 중지
@app.route('/stop', methods=['POST'])
def stop():    
    requestDTO = request.get_json()
    print("[stop requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    # 컨테이너 중지 cmd
    os.popen(stopContainerCmd(containerId))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200


# 웹 페이지에서 컨테이너 저장 요청이 왔을 때, 기존 컨테이너, 이미지 삭제하고 새로운 이미지 생성 후 업로드 
@app.route('/save', methods=['POST'])
def save() :    
    requestDTO = request.get_json()
    print("[save requestDTO] ", requestDTO)
    userId, port, pwd = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['pwd'])
    containerId, imageId = str(requestDTO['containerId']), str(requestDTO['imageId'])
    
    cmd1 = "docker commit "+containerId+" registry.p2kcloud.com/base/"+userId+":"+port   # 새로운 이미지 생성
    cmd2 = "docker rm "+containerId                                                     # 기존 컨테이너 삭제
    cmd3 = "docker rmi -f registry.p2kcloud.com/base/"+userId+":"+port                                                   # 기존 이미지 삭제 
    cmd4 = "docker create -p "+port+":6901 -e VNC_PW="+pwd+" registry.p2kcloud.com/base/"+userId+":"+port    # 새로운 컨테이너 실행
    cmd5 = "docker push registry.p2kcloud.com/base/"+userId+":"+port             # 하버에 이미지 올리기
    cmd6 = "docker images registry.p2kcloud.com/base/"+userId+":"+port+" -q"     # 새로운 이미지 id 추출 
    
    
    stream1 = os.popen(saveImgCmd(containerId, userId, port))
    print("1 : ", stream1.read())
    
    stream2 = os.popen(deleteContainerCmd(containerId))
    print("2 : ", stream2.read())
    
    time.sleep(1)
    stream4 = os.popen(createContainerCmd(port, userId, pwd))
    newContainerId = stream4.read()[:12]
    print("4 : ", stream4.read())
    
    stream5 = os.popen(pushImgCmd(userId, port))
    print("5 : ", stream5.read())
    
    time.sleep(3)
    stream6 = os.popen(findImgIdCmd(userId, port))
    newImageId = stream6.read()[:12]
    print("6 : ", stream6.read())
    
    time.sleep(3)
    
    print("newContainerId : ", newContainerId)
    print("newImageId : ", newImageId)
    
    response = {
            'containerId' : newContainerId,
            'imageId' : newImageId
        }
    
    return jsonify(response), 200



# 웹 페이지에서 컨테이너 삭제 요청이 왔을 때, 컨테이너 삭제하고 이미지 삭제 
@app.route('/delete', methods=['POST'])
def delete():    
    requestDTO = request.get_json()
    print("[delete requestDTO] ", requestDTO)
    userId, port = str(requestDTO['id']), str(requestDTO['port'])
    containerId, imageId = str(requestDTO['containerId']), str(requestDTO['imageId'])
    
    os.popen(deleteContainerCmd(containerId))
    os.popen(deleteImgCmd(userId, port))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)