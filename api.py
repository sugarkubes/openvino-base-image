from __future__ import print_function
import grpc
import numpy as np
import tensorflow.contrib.util as tf_contrib_util
import datetime
import argparse
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc
import cv2
import os.path
import json
import os
from flask import Flask, request, send_from_directory, jsonify
import urllib.request
from pprint import pprint
from base64 import b64encode
from flask_cors import CORS
import httplib2
from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, '.2f')

COLOR = (255,92,122)
font = cv2.FONT_HERSHEY_SIMPLEX
FACE_CONFIDENCE_THRESH = 0.2


with open('config.json') as f:
    config = json.load(f)

with open('classes.json') as f:
    classes = json.load(f)
    classes = classes['classes']

print("Using configs:")
pprint(config)

channel = grpc.insecure_channel("{}:{}".format(config['grpc_address'],config['grpc_port']))
stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

def downloadFile(URL=None):
    h = httplib2.Http(".cache")
    resp, content = h.request(URL, "GET")
    return content

def url_ok(url=""):
    if (url is None):
        return False
    return len(url) != 0

'''
~ 50ms
'''
def generic_predict(img, name, input, output1):
    request = predict_pb2.PredictRequest()
    request.model_spec.name = name
    request.inputs[input].CopyFrom(tf_contrib_util.make_tensor_proto(img, shape=(img.shape)))
    start_time = datetime.datetime.now()
    result = stub.Predict(request, 10.0) # result includes a dictionary with all model outputs
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds() * 1000
    output1 = tf_contrib_util.make_ndarray(result.outputs[output1])
    print('{} Processing time: {:.2f} ms; speed {:.2f} fps'.format(name, round(duration), 2), round(1000 / duration, 2))
    return output1, duration

def predict_objects(img):
    orig_height, orig_width, chan = img.shape
    req_width = 300
    req_height = 300
    scale_width = orig_width / req_width
    scale_height = orig_height / req_height

    img = cv2.resize(img, (req_width, req_height), interpolation = cv2.INTER_CUBIC)
    transpose = np.transpose(img, (2, 0, 1))
    transpose = transpose.reshape(1, 3, req_height, req_width)
    output, duration = generic_predict(transpose, 'ssd_mobilenet_v2_oid_v4_2018_12_12', 'image_tensor', 'DetectionOutput')
    # print('OUTPUT1', output.shape)
    # print("output2", output[0][0].shape)

    confident = []
    '''
    output is
        batch index
        class label
        class probability
        x_1 box coordinate
        y_1 box coordinate
        x_2 box coordinate
        y_2 box coordinate.
    '''
    for (batch_idx, class_label, class_probability, x1, y1, x2, y2) in output[0][0]:
        if (class_probability > config['confidence']):
            # print("confident! ", batch_idx, class_label, class_probability, x1, y1, x2, y2)
            # print('X, Y, W, H', x, y, w, h)
            x1 = (x1 * req_width) * scale_width
            y1 = (y1 * req_height) * scale_height
            x2 = (x2 * req_width) * scale_width
            y2 = (y2 * req_height) * scale_height
            # # scale to original
            confident.append([classes[int(class_label) - 1]['name'], str(round(class_probability, 2)), int(x1), int(y1), int(x2), int(y2)])
    return confident, duration

def draw_detections(frame, objects):
    for (className, conf, x1, y1, x2, y2) in objects:
        cv2.circle(frame,(int(x1), int(y1)), 5, COLOR, -1)
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), COLOR)
        cv2.putText(frame, className + ' (' + conf + ')', (x1,y1), font, 0.5, COLOR,1,cv2.LINE_AA)

    return frame

app = Flask(__name__, static_url_path='/root/face')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

@app.route("/predict", methods=['POST'])
def predict():
    """
    Predict Handler
    """
    try:
        request_json = request.get_json()
        return_image = request_json.get('return_image', False)

        url = request.args.get('url')
        if (not url_ok(url)):
            if (request_json is not None):
                url = request_json.get('url', '')
        if (not url_ok(url)):
            url = request.form.get('url')

        if (url_ok(url)):
            photo = downloadFile(url)
            frame = cv2.imdecode(np.fromstring(photo, np.uint8), 1)
        elif (len(request.files) > 0):
            photo = request.files.get('image')
            frame = cv2.imdecode(np.fromstring(photo.read(), np.uint8), 1)
        else:
            photo = request.data
            # print('request', frame)
            # photo = cv2.imdecode(np.fromstring(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
            # type = "string"

        height, width, chan = frame.shape

        objects, duration = predict_objects(frame)

        if (return_image == True):
            frame = draw_detections(frame, objects);
            _, binframe = cv2.imencode('.jpg', frame)
            base64_bytes = b64encode(binframe)
            base64_string = base64_bytes.decode('utf-8')
            return jsonify({ "speed": str(duration) + " ms", "base64": base64_string, "objects": objects, "image_size": [width, height] }), 200, {'ContentType': 'application/json'}

        return jsonify({ "speed": str(duration) + " ms", "objects": objects, "image_size": [width, height] }), 200, {'ContentType': 'application/json'}

    except Exception as exc:
        # 'errors': exc
        print(exc)
        return json.dumps({'errors': "error" }),\
            200, {'ContentType': 'application/json'}

@app.route('/tester/<path:path>')
def send_html(path):
    return send_from_directory('app', path)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route("/")
@app.route("/health")
def test():
    try:
        return json.dumps({'success': True}), 200,\
                {'ContentType': 'application/json'}
    except Exception as exc:
        # 'errors': exc
        return json.dumps({'success': False }), 200,\
            {'ContentType': 'application/json'}

if __name__ == "__main__":
    app.run(host=config["host"], port=config["port"], debug=False)
