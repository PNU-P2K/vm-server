from flask import Flask, render_template, request, jsonify
import os, time

app = Flask(__name__)

# 컨테이너 관련 명령어 
def createContainerCmd(port, pwd, imageId) : # vm+port 이름의 컨테이너 생성 
    return "docker create -p "+port+":6901 -e VNC_PW="+pwd+" --name vm"+port+" "+imageId

def startContainerCmd(containerId) :    # containerid로 컨테이너 실행
    return "docker start "+containerId

def stopContainerCmd(containerId) :     # containerid로 컨테이너 중지
    return "docker stop "+containerId

def deleteContainerCmd(containerId) :   # containerid로 컨테이너 삭제 
    return "docker rm "+containerId

# 이미지 관련 명령어 
def createImgCmd(containerId, userId, port) : # registry.p2kcloud.com/base/userid:port 이름의 새로운 이미지 생성
    return "docker commit "+containerId+" registry.p2kcloud.com/base/"+userId+":"+port
    
def pushImgCmd(userId, port) :          # harbor에 이미지 저장 
    return "docker push registry.p2kcloud.com/base/"+userId+":"+port

def deleteImgCmd(imageId) :             # imageid로 이미지 삭제 
    return "docker rmi -f "+imageId

def pullImgCmd() :      # harbor에서 kasm 이미지 pull -> 이미 pull 받아짐
    return "docker pull registry.p2kcloud.com/base/vncdesktop"

baseImageId = '9e4131d0' # kasm window 이미지 


# spring 서버에서 컨테이너 생성 요청이 왔을 때, base 이미지로 컨테이너 생성하고 이미지 저장 
@app.route('/create', methods=['POST'])
def create():
    
    requestDTO = request.get_json() 
    print("[create requestDTO] ", requestDTO)
    userId, port, pwd = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['password'])
    
    stream1 = os.popen(createContainerCmd(port, pwd, baseImageId))
    containerId = stream1.read()[:12]
    time.sleep(5)
    
    stream2 = os.popen(createImgCmd(containerId, userId, port))
    imageId = stream2.read()[7:20]
    
    response = {
            'port': port,
            'containerId' : containerId,
            'imageId' : imageId
        }
    
    return jsonify(response), 200



#spring 서버에서 가상환경 로드했을 때, 이미지로 컨테이너 생성 후 새로운 이미지로 저장
@app.route('/load', methods=['POST'])
def load() :
    
    requestDTO = request.get_json()
    print("[load requestDTO] ", requestDTO)
    userId, port, pwd, imageId = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['password']), str(requestDTO['key'])
    
    stream1 = os.popen(createContainerCmd(port, pwd, imageId))
    containerId = stream1.read()[:12]
    
    stream2 = os.popen(createImgCmd(containerId, userId, port))
    imageId = stream2.read()[7:20]
    
    response = {
        'containerId' : containerId,
        'imageId' : imageId
    }
    
    return jsonify(response), 200



# spring 서버에서 컨테이너 실행 요청이 왔을 때, 컨테이너 실행
@app.route('/start', methods=['POST'])
def start():    
    
    requestDTO = request.get_json()
    print("[start requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    os.popen(startContainerCmd(containerId))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200



# spring 서버에서 컨테이너 중지 요청이 왔을 때, 컨테이너 중지
@app.route('/stop', methods=['POST'])
def stop():    
    
    requestDTO = request.get_json()
    print("[stop requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    
    os.popen(stopContainerCmd(containerId))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200



# spring 서버에서 컨테이너 저장 요청이 왔을 때, 현재 컨테이너의 이미지 생성 -> 기존 이미지 삭제 -> push
@app.route('/save', methods=['POST'])
def save() :    
    
    requestDTO = request.get_json()
    print("[save requestDTO] ", requestDTO)
    userId, port, pwd = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['pwd'])
    containerId, imageId = str(requestDTO['containerId']), str(requestDTO['imageId'])
    
    stream1 = os.popen(createImgCmd(containerId, userId, port))
    newImageId = stream1.read()[7:20]
    print("1 : ", stream1.read())
    
    stream2 = os.popen(deleteImgCmd(imageId))
    print("2 : ", stream2.read())
    
    stream3 = os.popen(pushImgCmd(userId, port))
    print("3 : ", stream3.read())
    time.sleep(3)
    
    print("newImageId : ", newImageId)
    
    response = {
            'containerId' : containerId,
            'imageId' : newImageId
        }
    
    return jsonify(response), 200



# spring 서버에서 컨테이너 삭제 요청이 왔을 때, 컨테이너, 이미지 삭제  
@app.route('/delete', methods=['POST'])
def delete():    
    
    requestDTO = request.get_json()
    print("[delete requestDTO] ", requestDTO)
    userId, port = str(requestDTO['id']), str(requestDTO['port'])
    containerId, imageId = str(requestDTO['containerId']), str(requestDTO['imageId'])
    
    os.popen(deleteContainerCmd(containerId))
    os.popen(deleteImgCmd(imageId))
    
    response = {
            'port' : port,
            'containerId' : containerId
        }
    
    return jsonify(response), 200


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)