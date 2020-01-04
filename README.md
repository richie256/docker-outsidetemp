# Outside temps from openweathermap.org

This Outside temps API is mainly used to retrive weather condition in InfluxDB format.


## TODO List

- [ ] Need to set Environment variables instead of config file to be able to launch the container from a registry.
- [ ] Once done, put this into a Container registry.

## Requirement

- You'll need a Openweathermap API key to use this service.
- You need to retrieve the Location_ID of your city from Openweathermap.

## Frequency
Calls per minute (no more than)	60
no more than one time every 10 minutes for one location (city / coordinates / zip-code).

## Notes

Forecast:
http://api.openweathermap.org/data/2.5/forecast?id={CITY_CODE_ID}&APPID={APPID}

Current:
http://api.openweathermap.org/data/2.5/weather?id={CITY_CODE_ID}&APPID={APPID}&units=metric

Details on the api response
https://openweathermap.org/current

Weather sample:
https://samples.openweathermap.org/data/2.5/weather?id=2172797&appid=b6907d289e10d714a6e88b30761fae22

Weather Icons list:
https://openweathermap.org/weather-conditions


## Edge case not managed

If blocked:
{
"cod": 429,
"message": "Your account is temporary blocked due to exceeding of requests limitation of your subscription type. 
Please choose the proper subscription http://openweathermap.org/price"
}

## Example

curl http://localhost:5001/conditions/5909629?format=influx
