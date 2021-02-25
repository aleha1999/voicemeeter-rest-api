import voicemeeter
import os
from flask import Flask
from flask_json import FlaskJSON, json_response, as_json, request
from flask_cors import CORS
import signal, sys
import json
import glob
from gevent.pywsgi import WSGIServer

app = Flask(__name__, static_folder='static', static_url_path='')
FlaskJSON(app)
CORS(app)

kind = 'banana'

#voicemeeter.launch(kind)

vmi = None

with voicemeeter.remote(kind) as vm:
    vmi = vm

@app.route('/play')
@as_json
def play():
    name = request.args.get('sound')
    if(name is not None):
        f = os.path.abspath('sounds/%s' % name)
        vmi.set("Recorder.load", f)
    vmi.set("Recorder.play", 1)
    return True

@app.route("/stop")
@as_json
def stop():
    vmi.set('Recorder.stop',1)
    return True

@app.route('/sounds')
@as_json
def index():
    f = glob.glob('sounds/**/*.mp3', recursive=True)
    f.extend(glob.glob('sounds/**/*.wav', recursive=True))
    final = []
    for file in f:
        final.append(file[len("sounds/"):])
    return final

@app.route('/tmute/<device>/<track>')
@as_json
def toggle_mute(device,track):
    d = '%s[%s].mute' % (device, track);
    s = vmi.get(d)
    vmi.set(d, not s)
    return vmi.get(d)

@app.route('/isMuted/<device>/<track>')
@as_json
def is_muted(device, track):
    d = '%s[%s].mute' % (device, track);
    return vmi.get(d)

@app.route('/mute/<track>')
@as_json
def mute(track):
    vmi.inputs[int(track)].mute = True
    return True

@app.route('/unmute/<track>')
@as_json
def unmute(track):
    vmi.inputs[int(track)].mute = False
    return True

@app.route('/fadeto')
@as_json
def fade_to():
    device = request.args.get('device')
    i = request.args.get('index', type=int)
    time = request.args.get('time', type=int)
    target = request.args.get('target', type=float)
    print(target)
    if None in [device, i, target, time]:
        return False
    vmi.set('%s[%i].FadeTo' % (device, i), '(%f, %i);' % (target,time))

@app.route('/gain', methods=['GET','POST'])
@as_json
def gain():
    if(request.method == 'GET'):
        device = request.args.get('device', type=str)
        i = request.args.get('index', type=int)
        if None in [device, i]:
            return False
    if(request.method == 'POST'):
        data = request.get_json(force=True)
        try:
           device = data['device']
           i = data['index']
           target = data['target']
        except:
            return False

    d = '%s[%s].Gain' % (device, i)
    if device == "Recorder":
        d = "Recorder.Gain"
    if(request.method == 'POST'):
        if target is None:
            return False
        vmi.set(d, target)
        return True
    else:
        return vmi.get(d)    

def handle_int(sig, frame):
    vmi.logout()
    print("Goodbye")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_int)

http_server = WSGIServer(('0.0.0.0', 5000), app)
http_server.serve_forever()