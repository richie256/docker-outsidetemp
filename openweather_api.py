# OutsideTemp service

from flask import Flask
from flask import Response
from flask import jsonify
from flask import request

from flask_restful import Resource, Api, reqparse, abort

from urllib.request import urlopen

import json
import time

import sys

from const import (
    _LOGGER,
    OPENWEATHER_CONFIG_FILENAME,
    OPENWEATHER_API_KEY,
)

import os

from util import config_from_file

import socket

# # create logger with 'openweather_application'
# logger = logging.getLogger('openweather_application')
# logger.setLevel(logging.DEBUG)
# # create file handler which logs even debug messages
# fh = logging.FileHandler('openweather.log')
# fh.setLevel(logging.DEBUG)
# # create console handler with a higher log level
# ch = logging.StreamHandler()
# ch.setLevel(logging.ERROR)
# # create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# ch.setFormatter(formatter)
# # add the handlers to the logger
# logger.addHandler(fh)
# logger.addHandler(ch)

app = Flask(__name__)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('api_key')


def internet(host="1.1.1.1", port=53, timeout=3):
    """
    Host: 1.1.1.1 (1dot1dot1dot1.cloudflare-dns.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print(ex.message)
        return False


class OutsideTemp(Resource):
    CONST_JSON = 'JSON'
    CONST_INFLUX = 'influx'
    CONST_METRIC_UNIT = 'metric'

    # global location
    # global location_id
    # global tempVal
    # global observation_epoch

    # global pressure
    # global humidity

    # Wind
    # global wind_speed
    # global windDeg

    # Weather condition
    # global weatherId
    # global weatherMain
    # global weatherDescription

    # global OPENWEATHER_UNITS

    def __init__(self):

        self.tempVal = ''
        self.pressure = 0
        self.humidity = 0
        self.observation_epoch = 0

        self.config_filename = OPENWEATHER_CONFIG_FILENAME

        if os.path.isfile(self.config_filename):
            config_from_file(self.config_filename)

            self.config = config_from_file(self.config_filename)
            self.OPENWEATHER_API_KEY = self.config[OPENWEATHER_API_KEY]

        else:
            raise FileNotFoundError

        # Wind
        self.wind_speed = ''
        self.windDeg = 0

        # Weather condition
        self.weatherId = 0
        self.weatherMain = ''
        self.weatherDescription = ''

        self.location = ''

        # _LOGGER.info('About to retrieve the format')
        self.success_result = True
        self.opt_format = request.args.get("format")
        if self.opt_format is None:
            self.opt_format = self.CONST_JSON

        self.OPENWEATHER_UNITS = request.args.get("units")
        if self.OPENWEATHER_UNITS is None:
            self.OPENWEATHER_UNITS = self.CONST_METRIC_UNIT

        # if os.environ['LOCATION_ID'] is None:

        # self.location_id = os.getenv('LOCATION_ID', None)
        # if self.location_id is None:
        #     raise KeyError

    # print(os.environ['HOME'])

    # Load variables
    # with open('openweather-vars.json') as f:
    # configdata = json.load(f)

    # self.OPENWEATHER_LOCATION_ID = configdata['LOCATION_ID']
    # self.OPENWEATHER_API_KEY = configdata['API_KEY']
    # self.OPENWEATHER_UNITS = configdata['UNITS']
    # logger.info('Api Key:' + self.OPENWEATHER_API_KEY)
    # logger.info('Units:' + self.OPENWEATHER_UNITS)

    def get_outside_info(self, location_id):
        # Initialize
        self.success_result = True
        openweathermap = None
        is_connected = False
        json_string = ''

        try:
            self.location_id = location_id

            nboftrials = 0

            while not is_connected and nboftrials < 5:
                is_connected = internet()
                if not is_connected:
                    nboftrials += 1
                    time.sleep(10)

            # Python 3.4:
            openweathermap = urlopen('http://api.openweathermap.org/data/2.5/weather?id=' + str(
                location_id) + '&appid=' + self.OPENWEATHER_API_KEY + '&units=' + self.OPENWEATHER_UNITS)

            json_string = openweathermap.read()
            parsed_json = json.loads(json_string)

            # Default: Kelvin, Metric: Celsius, Imperial: Fahrenheit.
            self.tempVal = parsed_json['main']['temp']

            # Atmospheric pressure (on the sea level, if there is no sea_level or grnd_level data), hPa
            self.pressure = int(parsed_json['main']['pressure'])

            # Humidity, %
            self.humidity = int(parsed_json['main']['humidity'])

            # Time of data calculation, unix, UTC
            self.observation_epoch = int(parsed_json['dt'])

            # Wind
            # Unit Default: meter/sec, Metric: meter/sec, Imperial: miles/hour.
            self.wind_speed = parsed_json['wind']['speed']
            self.windDeg = int(parsed_json['wind']['deg'])

            # Weather condition
            self.weatherId = int(parsed_json['weather'][0]['id'])
            self.weatherMain = parsed_json['weather'][0]['main']
            self.weatherDescription = parsed_json['weather'][0]['description']

            self.location = parsed_json['name']

        except:
            self.success_result = False
            if openweathermap is not None:
                _LOGGER.error('Problem with getting outside infos in JSON. openweathermap = ' + str(
                    openweathermap) + ' and json_string = ' + str(json_string))
            else:
                _LOGGER.error('Problem with getting outside infos in JSON. openweathermap is None.')

            # logger.error(sys.exc_info()[0])
            _LOGGER.error(sys.exc_info())
            return sys.exc_info()[0]

        finally:
            if openweathermap is not None:
                openweathermap.close()

    def get(self, location_id):
        _LOGGER.info('Receive a request. location_id: ' + str(location_id))
        count = 0
        self.success_result = False

        while not self.success_result:
            self.get_outside_info(location_id)

            count += 1
            if (count >= 3) or (self.success_result == True):
                break
            else:
                time.sleep(3)

        if not self.success_result:
            abort(500)

        # JSON Format
        if self.opt_format == self.CONST_JSON:

            outside_temp = {'service': 'outsideTemp',
                            'tempVal': self.tempVal,
                            'pressure': self.pressure,
                            'humidity': self.humidity,
                            'observation_epoch': self.observation_epoch,
                            'windSpeed': self.wind_speed,
                            'windDeg': self.windDeg,
                            'weatherId': self.weatherId,
                            'weatherMain': self.weatherMain,
                            'weatherDescription': self.weatherDescription,
                            'location': self.location
                            }

            return jsonify(outside_temp)

        # Infuxdb format
        elif self.opt_format == self.CONST_INFLUX:

            influxdb_measurement = 'apidata'
            influxdb_tag_set = 'source=wunderground,location=' + self.location + ',opt_format=' + self.opt_format
            influxdb_field_set = 'tempVal=' + str(self.tempVal) + ',humidity=' + str(
                self.humidity) + ',windSpeed=' + str(self.wind_speed) + ',windDeg=' + str(
                self.windDeg) + ',weatherId=' + str(self.weatherId)
            influxdb_timestamp = str(self.observation_epoch) + '000000000'

            return_value = (
                    influxdb_measurement + ',' + influxdb_tag_set + ' ' + influxdb_field_set + ' ' + influxdb_timestamp + '\n')

            return Response(return_value, mimetype='text/xml')


class ApiManagement(Resource):

    def __init__(self):
        args = parser.parse_args()
        self.api_key = args['api_key']
        self.config_filename = OPENWEATHER_CONFIG_FILENAME

    def _write_config(self) -> None:
        """Writes API Key to a file."""
        config = dict()
        config[OPENWEATHER_API_KEY] = self.api_key

        config_from_file(self.config_filename, config)

    def post(self):
        self._write_config()

        return "Success", 201


api.add_resource(OutsideTemp, '/conditions/<int:location_id>')

api.add_resource(ApiManagement, '/set_api')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
