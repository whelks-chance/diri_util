import json
import os
import pprint

import exifread
import dateutil.parser
import geojson
from PIL import Image


class ImgExif:

    def __init__(self):
        self.all_cache = {}
        self.lnglats = []
        self.all_points = []
        self.all_dates = []

    def exif_latlng_to_wgs84(self, lat, lng, lat_dir, lng_dir):
        lat_arr = str(lat).replace('[', '').replace(']', '').split(',')
        lat_arr_final = []
        for lat_part in lat_arr:
            if '/' in lat_part:
                fraction_parts = lat_part.split('/')
                lat_part = str(
                    round(
                        float(fraction_parts[0]) / float(fraction_parts[1])
                    )
                )
            lat_arr_final.append(lat_part.strip())
        dd = float(lat_arr_final[0]) + float(lat_arr_final[1]) / 60 + float(lat_arr_final[2]) / (60 * 60);

        print('lat', dd, 'is S == *{}*'.format(lat_dir), lat_dir == "S")
        if str(lat_dir) == 'S':
            dd *= -1

        lng_arr = str(lng).replace('[', '').replace(']', '').split(',')
        lng_arr_final = []
        for lng_part in lng_arr:
            if '/' in lng_part:
                fraction_parts = lng_part.split('/')
                lng_part = str(
                    round(
                        float(fraction_parts[0]) / float(fraction_parts[1])
                    )
                )
            lng_arr_final.append(lng_part.strip())
        d_lng = float(lng_arr_final[0]) + float(lng_arr_final[1]) / 60 + float(lng_arr_final[2]) / (60 * 60);
        if str(lng_dir) == 'W':
            d_lng *= -1
        return dd, d_lng

    def exif_date_to_iso8601(self, gps_date, gps_timestamp):

        gps_timestamp = str(gps_timestamp).replace('[', '').replace(']', '')
        gps_timestamp_arr = gps_timestamp.split(',')
        gps_timestamp_arr_final = []
        for gps_timestamp_part in gps_timestamp_arr:

            # LOL
            if '/' in gps_timestamp_part:
                fraction_parts = gps_timestamp_part.split('/')
                fraction_realised = str(
                        round(
                            float(fraction_parts[0]) / float(fraction_parts[1])
                        )
                    )
                gps_timestamp_arr_final.append(
                    fraction_realised.strip()
                )
            else:
                gps_timestamp_part = gps_timestamp_part.strip()
                if len(gps_timestamp_part) == 1:
                    gps_timestamp_part = '0' + gps_timestamp_part
                gps_timestamp_arr_final.append(gps_timestamp_part)

        time_str = '{}T{}Z'.format(
            str(gps_date).replace(':', '-'),
            ':'.join(gps_timestamp_arr_final)
        )

        # Forces an error to occur if the resultant string doesn't parse
        test_date = dateutil.parser.parse(time_str)
        return time_str, test_date

    def read_exif(self, folder):
        print('Running')

        for f in os.listdir(folder):
            full_filepath = os.path.join(folder, f)
            if os.path.isfile(full_filepath):
                print(f)

                # Open image file for reading (binary mode)
                a_file = open(full_filepath, 'rb')

                # Return Exif tags
                tags = exifread.process_file(a_file)
                # print(pprint.pformat(tags))

                gps_keys = []
                for key in tags.keys():
                    # if 'JPEGThumbnail' not in key:
                    #     print(key, tags[key])

                    if 'GPS' in key:
                        gps_keys.append(key)
                        print(key, tags[key])

                time_str = ''
                if 'GPS GPSDate' in tags.keys():
                    # 2008-08-09T18:39:22Z
                    # Lets build a datetime string!
                    time_str, time_obj = self.exif_date_to_iso8601(
                        tags['GPS GPSDate'],
                        tags['GPS GPSTimeStamp']
                    )
                    print('\n', 'datetime.datetime object:', time_obj)
                    print(time_str)
                    self.all_dates.append(time_str)

                if 'GPS GPSLongitude' in tags.keys():
                    lat, lng = self.exif_latlng_to_wgs84(
                        tags['GPS GPSLatitude'],
                        tags['GPS GPSLongitude'],
                        tags['GPS GPSLatitudeRef'],
                        tags['GPS GPSLongitudeRef'],
                    )
                    print(lat, lng)

                    img = Image.open(full_filepath)
                    img.show()

                    value = input("Input the value >> ")
                    print(value)

                    self.create_geojson(lat, lng, {
                                            'datetime': time_str,
                                            'img_name': f,
                                            'value': value
                                        })
                    self.cache({
                        'img_name': f,
                        'value': value,
                        'datetime': time_str,
                        'lat': lat,
                        'lng': lng
                    })
                print('x'*20, '\n\n')

    def create_geojson(self, lat, lng, props=None):
        if props is None:
            props = {}
        self.all_points.append(
            geojson.Feature(
                geometry=geojson.Point((lng, lat)),
                properties=props
            )
        )
        self.lnglats.append((lng, lat))

    def print_geojson(self):
        ls = geojson.LineString(self.lnglats)
        self.all_points.append(geojson.Feature(geometry=ls))
        fc = geojson.FeatureCollection(self.all_points)
        print(geojson.dumps(fc))

        with open('jakarta_geo.json', 'w') as geo1:
            geo1.write(geojson.dumps(fc))

    def print_dates(self):
        print(self.all_dates)
        print(sorted(self.all_dates))

    def cache(self, params):
        self.all_cache[params['img_name']] = params
        with open('cache.json', 'w') as c1:
            c1.write(pprint.pformat(self.all_cache))

    def load_cache(self):
        with open('cache.json', 'r') as c2:
            self.all_cache = json.load(c2)
        print(self.all_cache)


if __name__ == '__main__':
    img_location = "C:\\Users\\Ian Harvey\\OneDrive - Cardiff University\\Email attachments"
    ie = ImgExif()
    ie.load_cache()
    ie.read_exif(img_location)
    ie.print_geojson()
