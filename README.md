# Openvino base image

**Thanks for visiting! Inside this repo you'll find a FREE SugarKube!**

*Like what you see? check us out at (sugarkubes.io)[https://sugarkubes.io]*

## What is openvino?

- Learn about [openvino here](https://software.intel.com/en-us/openvino-toolkit)
- TLDR; openvino gets you GPU-like inference speeds on certain intel CPUs, it's pretty sweet. Just make sure you're on a supported CPU otherwise the acceleration won't work.

## How to use the base image

The base image is up on docker hub so just

```sh
docker pull sugarkubes/openvino:latest
```

*We use this base image to build on top of in other docker files, see Dockerfile.quick for an example*


Let's walk through a brief example of how to use this base image

You need to have your models in the openvino format which is a .bin and .xml. It's kind of a pain to get them into this format using their model converter but the documentation to do that is [here](https://software.intel.com/en-us/articles/OpenVINO-Using-TensorFlow).


Pull the base image and add a few packages.

```sh
FROM sugarkubes/openvino:latest as RELEASE
RUN apt-get update && apt-get install -y \
  wget \
  unzip \
  libglib2.0-0 \
  libsm6 \
  libxrender1 \
  libxext6 \
  vim
```

You need to have your models in the openvino format which is a .bin and .xml file. It's kind of a pain to get them into this format using their model converter but the documentation to do that is [here](https://software.intel.com/en-us/articles/OpenVINO-Using-TensorFlow). Fortunately I already did this for you guys and gals so just go ahead and grab the model.

Once you have a converted model, zip the model into a folder. Make sure the following structure is in place once unzipped.
```sh
<model-name>/<version-number>/<model-name>.(bin, xml)
```
So for example our *ssd_mobilenet_v2_oid_v4_2018_12_12* has one folder inside named *1*. This *1* is the version number. Inside the *1* folder are two files:
```
ssd_mobilenet_v2_oid_v4_2018_12_12/1/ssd_mobilenet_v2_oid_v4_2018_12_12.bin
ssd_mobilenet_v2_oid_v4_2018_12_12/1/ssd_mobilenet_v2_oid_v4_2018_12_12.xml
```

Since all this is done for you just grab the models. The openvino base image expects them under */opt/ml/ssd_mobilenet_v2_oid_v4_2018_12_12/1/ssd_mobilenet_v2_oid_v4_2018_12_12.bin*.
```sh
RUN wget -P /opt/ml https://s3.us-west-1.wasabisys.com/public.sugarkubes/repos/sugar-cv/intel-object-detection/ssd_mobilenet_v2_oid_v4_2018_12_12.zip
RUN cd /opt/ml && unzip ssd_mobilenet_v2_oid_v4_2018_12_12.zip

```
Now go into the model_configuration_file.json included in this repo. Make sure for new models you change the name, but here it is done for this ssd model.


```json
{
   "model_config_list":[
      {
         "config": {
            "name":"ssd_mobilenet_v2_oid_v4_2018_12_12",
            "base_path":"/opt/ml/ssd_mobilenet_v2_oid_v4_2018_12_12",
            "batch_size": "auto",
            "model_version_policy": {"all": {}}
         }
      }
    ]
}
```

openvino model server allows for various models to be loaded at the same time, as well as different versions of the same model loaded at the same time. Just add another object with the same structure to the array to serve multiple models.

```json
{
   "model_config_list":[
      {
         "config": {
            "name":"model1",
            "base_path":"/opt/ml/model1",
            "batch_size": "auto",
            "model_version_policy": {"all": {}}
         }
      },
      {
         "config": {
            "name":"model2",
            "base_path":"/opt/ml/model2",
            "batch_size": "auto",
            "model_version_policy": {"all": {}}
         }
      }
    ]
}
```

Finally, copy all the code from the repo into the docker container including our configs, and api.py  to run the python server.

```sh
COPY . /var/sugar/
RUN . .venv/bin/activate && \
    pip3 install -r /var/sugar/requirements.txt

# In this directory, modify the model_configuration_file.json to refer to your models. See README
RUN mv /var/sugar/model_configuration_file.json /opt/ml/config.json

# Start script if that's how you want to do things
RUN chmod +x /var/sugar/start.sh
EXPOSE 9090
CMD ["/var/sugar/start.sh"]
```

Now you should be able to run the image!

### Wrapping up

#### Build it!

```sh
docker build \
-f Dockerfile.quick \
-t registry.sugarkubes.io/sugar-cv/intel-object-detection:latest .
```

#### Run it!

```sh
docker run --rm -dti \
-p 9090:9090 \
registry.sugarkubes.io/sugar-cv/intel-object-detection:latest
```

#### Call It
```sh
curl -X POST \
  http://0.0.0.0:9090/predict \
  -H 'Content-Type: application/json' \
  -d '{ "url": "https://s3.us-west-1.wasabisys.com/public.sugarkubes/repos/sugar-cv/object-detection/friends.jpg" }'
```

## Free SugarKube!

![Demo!](https://s3.us-west-1.wasabisys.com/public.sugarkubes/repos/sugar-cv/intel-object-detection/intel-object-detection.mov)

Inside this repo is all the code and a docker file needed to run the intel-object-detection SugarKube.

It is an SSD model trained on openimages v4 and can detect 601 classes with ~50ms inference times. As with all SugarKubes, it has a simple, well documented api and is ready to use!

[List of 600 objects](https://s3.us-west-1.wasabisys.com/public.sugarkubes/repos/sugar-cv/object-detection/accurate-600.csv)

Visit [http://0.0.0.0:9090/tester/index.html](http://0.0.0.0:9090/tester/index.html) to test the object detection api.



![Example Response!](https://s3.us-west-1.wasabisys.com/public.sugarkubes/repos/sugar-cv/intel-object-detection/object-example.png)

```sh
# Example Output

# (x1, y1) are top left of bounding box
# (x2, y2) are lower right of bounding box
{
  "objects": [
    [
      "Woman", // label
      "0.65", // confidence
      673, // x1
      188, // y1
      832, // x2
      730 // y2
    ],
    [
      "Woman",
      "0.49",
      1012,
      128,
      1192,
      800
    ],
    [
      "Woman",
      "0.41",
      512,
      173,
      671,
      728
    ],
    [
      "Man",
      "0.63",
      356,
      155,
      526,
      721
    ],
    [
      "Man",
      "0.62",
      204,
      171,
      376,
      716
    ],
    [
      "Man",
      "0.62",
      831,
      100,
      1025,
      737
    ],
    [
      "Man",
      "0.54",
      40,
      189,
      226,
      697
    ],
    [
      "Footwear",
      "0.52",
      51,
      626,
      105,
      676
    ],
    [
      "Footwear",
      "0.49",
      231,
      653,
      304,
      717
    ],
    [
      "Footwear",
      "0.49",
      728,
      683,
      772,
      726
    ],
    [
      "Footwear",
      "0.48",
      890,
      675,
      940,
      729
    ],
    [
      "Footwear",
      "0.45",
      870,
      697,
      927,
      749
    ],
    [
      "Footwear",
      "0.39",
      1068,
      751,
      1112,
      788
    ],
    [
      "Footwear",
      "0.39",
      372,
      678,
      445,
      729
    ],
    [
      "Footwear",
      "0.32",
      141,
      619,
      198,
      661
    ],
    [
      "Human face",
      "0.44",
      1064,
      158,
      1120,
      229
    ],
    [
      "Jeans",
      "0.46",
      1035,
      399,
      1176,
      746
    ]
  ],
  "image_size": [
    1200,
    800
  ]
}
```
