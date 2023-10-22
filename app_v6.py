from flask import Flask, render_template, request, jsonify
import os, time
import func

app = Flask(__name__)

baseImageId = '539c2be37d94' # kasm-1.14.0 이미지 - test 서버 
#baseImageId = '' # kasm-1.14.0 이미지 - 실서버
#baseImageId = '1692c5f95a70e' # 로컬 이미지

BS = 16
pad = (lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode())
unpad = (lambda s: s[:-ord(s[len(s)-1:])])

# spring 서버에서 컨테이너 생성 요청이 왔을 때, base 이미지로 컨테이너 생성하고 이미지 저장
@app.route('/create', methods=['POST']) 
def create(): 

    requestDTO = request.get_json()
    print("[create requestDTO] ", requestDTO)
    userId, port, pwd = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['password'])
    scope, control = str(requestDTO['scope']), str(requestDTO['control'])

    stream1 = os.popen(func.createContainerCmd(port, pwd, baseImageId))
    containerId = stream1.read()[:12]
    time.sleep(5)
    enContainerId = func.aes.encrypt(containerId) # containerId 암호화

    stream2 = os.popen(func.createImgCmd(containerId, userId, port))
    imageId = stream2.read()[7:20]
    enImageId = func.aes.encrypt(imageId)  # imageId 암호화
    vmName = "vm"+port
    scriptPath = "/dockerstartup/start.sh" 
    nodePort = str(requestDTO['nodePort']) 
    imagePath = str(requestDTO['imagePath'])

    os.popen(func.startContainerCmd(containerId))
    os.popen(func.copyScriptToContainer(containerId))
    os.popen(func.stopContainerCmd(containerId))

    # PV yaml 파일 생성 
    pvPodYaml = func.generatePVYaml(vmName, vmName, vmName)
    pvFilePath = "/home/yaml/"+vmName+"PV.yaml"
    with open(pvFilePath, 'w') as pvYamlFile:
        pvYamlFile.write(pvPodYaml)

    # PVC yaml 파일 생성 
    pvcPodYaml = func.generatePVCYaml(vmName, vmName)
    pvcFilePath = "/home/yaml/"+vmName+"PVC.yaml"
    with open(pvcFilePath, 'w') as pvcYamlFile:
        pvcYamlFile.write(pvcPodYaml)

    # Depolyment yaml 파일 생성 
    deploymentPodYaml = func.generateDeploymentPodYaml(vmName, vmName, imagePath, port)
    deploymentFilePath = "/home/yaml/"+vmName+"Deployment.yaml"
    with open(deploymentFilePath, 'w') as deploymentYamlFile:
        deploymentYamlFile.write(deploymentPodYaml) 

    # Service yaml 파일 생성 
    servicePodYaml = func.generateServiceYaml(vmName, port, nodePort)
    serviceFilePath = "/home/yaml/"+vmName+"Service.yaml"
    with open(serviceFilePath, 'w') as serviceYamlFile:
        serviceYamlFile.write(servicePodYaml)

    print(deploymentPodYaml)
    print(servicePodYaml)

    os.popen(func.applyPodCmd(pvFilePath))
    os.popen(func.applyPodCmd(pvcFilePath))
    os.popen(func.applyPodCmd(deploymentFilePath))
    os.popen(func.applyPodCmd(serviceFilePath))

    nodeList = func.extractNodeInfo()
    time.sleep(60)
    externalNodeIp = func.extractNodeIpOfPod(nodeList)

    print("nodes: ", nodeList)
    print("externalIp: ", externalNodeIp)

    response = {
            'port': port,
            'containerId' : enContainerId,
            'imageId' : enImageId,
            'externalNodeIp': externalNodeIp
        }

    return jsonify(response), 200



#spring 서버에서 가상환경 로드했을 때, 이미지로 컨테이너 생성 후 새로운 이미지로 저장
@app.route('/load', methods=['POST'])
def load() :

    requestDTO = request.get_json()
    print("[load requestDTO] ", requestDTO)
    userId, port, pwd, imageId = str(requestDTO['id']), str(requestDTO['port']), str(requestDTO['password']), str(requestDTO['key'])
    loadKey = str(requestDTO['key'])
    deloadKey = func.aes.decrypt(loadKey)
    scope, control = str(requestDTO['scope']), str(requestDTO['control'])
    vmName = "vm"+port
    nodePort = str(requestDTO['nodePort'])
    imagePath = str(requestDTO['imagePath'])

    # PV yaml 파일 생성 
    pvPodYaml = func.generatePVYaml(vmName, vmName, vmName)
    pvFilePath = "/home/yaml/"+vmName+"PV.yaml"
    with open(pvFilePath, 'w') as pvYamlFile:
        pvYamlFile.write(pvPodYaml)

    # PVC yaml 파일 생성 
    pvcPodYaml = func.generatePVCYaml(vmName, vmName)
    pvcFilePath = "/home/yaml/"+vmName+"PVC.yaml"
    with open(pvcFilePath, 'w') as pvcYamlFile:
        pvcYamlFile.write(pvcPodYaml)

    # Depolyment yaml 파일 생성 
    deploymentPodYaml = func.generateDeploymentPodYaml(vmName, vmName, deloadKey, port)
    deploymentFilePath = "/home/yaml/"+vmName+"Deployment.yaml"
    with open(deploymentFilePath, 'w') as deploymentYamlFile:
        deploymentYamlFile.write(deploymentPodYaml) 

    # Service yaml 파일 생성 
    servicePodYaml = func.generateServiceYaml(vmName, port, nodePort)
    serviceFilePath = "/home/yaml/"+vmName+"Service.yaml"
    with open(serviceFilePath, 'w') as serviceYamlFile:
        serviceYamlFile.write(servicePodYaml)
        
    print(deploymentPodYaml)
    print(servicePodYaml)

    os.popen(func.applyPodCmd(pvFilePath))
    os.popen(func.applyPodCmd(pvcFilePath))
    os.popen(func.applyPodCmd(deploymentFilePath))
    os.popen(func.applyPodCmd(serviceFilePath))

    nodeList = func.extractNodeInfo()
    time.sleep(60)
    externalNodeIp = func.extractNodeIpOfPod(nodeList)

    print("nodes: ", nodeList)
    print("externalIp: ", externalNodeIp)

    response = {
            'port': port,
            'externalNodeIp': externalNodeIp
        }


    return jsonify(response), 200



# spring 서버에서 컨테이너 실행 요청이 왔을 때, 컨테이너 실행
@app.route('/start', methods=['POST'])
def start():

    print("hello")
    print(request.get_json())

    requestDTO = request.get_json()
    print("[start requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    pwd = str(requestDTO['password'])
    scope, control = str(requestDTO['scope']), str(requestDTO['control'])

    vmName = "vm"+port

    pvFilePath = "/home/yaml/"+vmName+"PV.yaml"
    pvcFilePath = "/home/yaml/"+vmName+"PVC.yaml"
    deploymentFilePath = "/home/yaml/"+vmName+"Deployment.yaml"
    serviceFilePath = "/home/yaml/"+vmName+"Service.yaml"

    os.popen(func.applyPodCmd(pvFilePath))
    os.popen(func.applyPodCmd(pvcFilePath))
    os.popen(func.applyPodCmd(deploymentFilePath))
    os.popen(func.applyPodCmd(serviceFilePath))

    time.sleep(3)
    
    stream1 = os.popen(func.getPodName(port))
    podName = stream1.read()[4:-1]
    
    print("podName:", podName)
    
    os.popen(func.copyScriptToPod(podName, vmName))
    
    time.sleep(1)
    
    changeVncScopeAndControlCmd = "kubectl exec -it "+podName+" bash /tmp/start.sh "+scope+" "+control+" "+pwd+" --kubeconfig /root/kubeconfig.yml"
    os.popen(changeVncScopeAndControlCmd)

    time.sleep(2)

    response = {
            'port' : port,
            'containerId' : containerId
        }

    return jsonify(response), 200



# spring 서버에서 컨테이너 중지 요청이 왔을 때, 컨테이너 중지
# pod안의 내용을 sh로 copy하고 -> 나중에 save하게 되면 dockerfile 작성할 때 쓰임 
# pod를 지움 
@app.route('/stop', methods=['POST'])
def stop():

    requestDTO = request.get_json()
    print("[stop requestDTO] ", requestDTO)
    port, containerId = str(requestDTO['port']), str(requestDTO['containerId'])
    vmName = "vm"+port # containerName과 동일 

    podName = os.popen(func.getPodName(port)).read()[4:-1]
    namespace = os.popen(func.getPodNameSpace(podName)).read()[:-1]

    print("start")
    '''
    stopScript = func.createStopScript(vmName)
    scriptFilePath = "/tmp/script/stop/"+vmName+".sh"
    with open(scriptFilePath, 'w') as scriptFile:
        scriptFile.write(stopScript)

    print("stop script: "+stopScript)

    accessContainer = f"kubectl exec -it {podName} bash /tmp/script/stop/{vmName}.sh --kubeconfig /root/kubeconfig.yml"
    os.popen(accessContainer)'''

    # backup을 위한 stopScript (나중에 저장할 때 쓰이기 위함) - 실제 정지시키는 역할이 아님 
    stopScript = func.createStopScript(vmName)
    scriptFilePath = "/home/stop/"+vmName+".sh"
    with open(scriptFilePath, 'w') as scriptFile:
        scriptFile.write(stopScript)

    print("stop script: "+stopScript)

    accessContainer = f"kubectl exec -it {podName} bash /home/stop/{vmName}.sh --kubeconfig /root/kubeconfig.yml"
    os.popen(accessContainer)


    func.deleteDeployPodCmd(vmName)
    func.deleteServicePodCmd(vmName)

    time.sleep(2)

    print("end")

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

    vmName = "vm"+port
    imagePath = "registry.p2kcloud.com/base/"+userId
    podName = os.popen(func.getPodName(port)).read()[4:-1]
    loadKey = func.aes.encrypt(imagePath+":"+port)
    
    backupScript = func.createBackupScript(vmName, imagePath, port)
    scriptFilePath = "/tmp/script/backup/"+vmName+".sh"
    with open(scriptFilePath, 'w') as scriptFile:
        scriptFile.write(backupScript)

    print("save script: "+backupScript)

    accessContainer = f"kubectl exec -it {podName} bash /tmp/script/backup/{vmName}.sh --kubeconfig /root/kubeconfig.yml"
    os.popen(accessContainer)
    
    time.sleep(2)

    print("path: "+imagePath+":"+port)

    response = {
            'containerId' : containerId,
            'imageId' : imageId, 
            'loadKey' : loadKey
        }

    return jsonify(response), 200



# spring 서버에서 컨테이너 삭제 요청이 왔을 때, 컨테이너, 이미지 삭제
@app.route('/delete', methods=['POST'])
def delete():

    requestDTO = request.get_json()
    print("[delete requestDTO] ", requestDTO)
    userId, port = str(requestDTO['id']), str(requestDTO['port'])
    containerId, imageId = str(requestDTO['containerId']), str(requestDTO['imageId'])

    vmName = "vm"+port

    deploymentFilePath = "/home/yaml/"+vmName+"Deployment.yaml"
    serviceFilePath = "/home/yaml/"+vmName+"Service.yaml"

    os.popen(func.deleteYamlFile(deploymentFilePath))
    os.popen(func.deleteYamlFile(serviceFilePath))


    response = {
            'port' : port,
            'containerId' : containerId
        }

    return jsonify(response), 200

if __name__ == '__main__':

    app.run('0.0.0.0', port=5000, debug=True)