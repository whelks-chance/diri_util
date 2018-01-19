import json
import os
import pprint

import exifread
import dateutil.parser
import geojson
import math
from PIL import Image
from colours import colours
from exifread.utils import Ratio

# http://www.thephotoforum.com/threads/calculate-angle-of-view-from-exif-tags.129742/

class ImgExif:

    def __init__(self):
        self.all_cache = {}
        self.lnglats = []
        self.all_points = []
        self.bearing_features = []
        self.all_dates = []
        self.c_scale = colours.mqc_colour_scale(name='RdYlGn-rev', minval=0, maxval=200)

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
        dd = float(lat_arr_final[0]) + float(lat_arr_final[1]) / 60 + float(lat_arr_final[2]) / (60 * 60)

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

    def read_exif(self, folder, show_img=True):
        print('Running')

        for f in os.listdir(folder):
            # Reset everything before either reading img or grabbinng from cache
            lat = None
            lng = None
            time_str = None
            value = None

            if f in self.all_cache and self.all_cache[f]['value'] is not '':
                props = self.all_cache[f]
                lat = props['lat']
                lng = props['lng']
                time_str = props['datetime']
                value = props['value']
            else:

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

                    bdeg = None
                    if 'GPS GPSDestBearing' in tags.keys():
                        gps_dest_bearing = tags['GPS GPSDestBearing']
                        bdeg = gps_dest_bearing.values[0].num / gps_dest_bearing.values[0].den
                        print('GPSDestBearing', gps_dest_bearing, bdeg)



                    if 'EXIF LensSpecification' in tags.keys():
                        gps_lens_specification = tags['EXIF LensSpecification']
                        print('LensSpecification', gps_lens_specification)
                        a = gps_lens_specification.values[0].num / gps_lens_specification.values[0].den
                        b = gps_lens_specification.values[2].num / gps_lens_specification.values[2].den
                        print('a', a, 'b', b)

                    if 'EXIF FocalLength' in tags.keys():
                        gps_focal_length = tags['EXIF FocalLength']
                        foc = gps_focal_length.values[0].num / gps_focal_length.values[0].den
                        print('FocalLength', gps_focal_length, foc)

                        FOV = 2*math.atan((math.sqrt(a*a + b*b)/2)/foc)

                        print('FOV', FOV)

                    # FOV = 2*arctan((SQRT(a*a + b*b)/2)/f)
                    # Where SQRT = square root
                    # a = lenght of sensor in mm
                    # b = width of sensor in mm
                    # f = focal length in mm

                    if 'GPS GPSLongitude' in tags.keys():
                        lat, lng = self.exif_latlng_to_wgs84(
                            tags['GPS GPSLatitude'],
                            tags['GPS GPSLongitude'],
                            tags['GPS GPSLatitudeRef'],
                            tags['GPS GPSLongitudeRef'],
                        )
                        print(lat, lng)

                        value = ''
                        if show_img:
                            img = Image.open(full_filepath)
                            img.show()

                            value = input("Input the value >> ")
                            print(value)

                        self.cache({
                            'img_name': 'http://dataportal1-wiserd.cf.ac.uk/static/dataportal/media/aqp/' + f,
                            'value': value,
                            'datetime': time_str,
                            'lat': lat,
                            'lng': lng
                        })

                        if value == '':
                            if bdeg:
                                bearing_line_length = 0.0005
                                x_shift, y_shift, radians = self.deg_to_bearing_line_coord(
                                    bdeg, bearing_line_length
                                )
                                ls = self.bearing_linestring_from_offset(lat, lng, x_shift, y_shift)
                                self.add_feature(ls, {
                                    'bearing': bdeg,
                                    'radians': radians,
                                    'img_name': 'http://dataportal1-wiserd.cf.ac.uk/static/dataportal/media/aqp/' + f,
                                    'datetime': time_str
                                })

                                self.add_arrow(radians, lat + x_shift, lng + y_shift, 0.0005 * 0.1)

                            self.bearing_features.append(geojson.Feature(
                                geometry=geojson.Point((lng, lat)),
                                properties={
                                    'img_name': 'http://dataportal1-wiserd.cf.ac.uk/static/dataportal/media/aqp/' + f,
                                    'marker-symbol': 'circle',
                                    'marker-color': '#ff0000'
                                }
                            ))
            if lat and lng and time_str and value:
                self.add_to_geojson(
                    lat, lng, {
                        'datetime': time_str,
                        'img_name': 'http://dataportal1-wiserd.cf.ac.uk/static/dataportal/media/aqp/' + f,
                        'value': value,
                        'REMOTE_VALUE': value,
                        'marker-symbol': 'heart',
                        'marker-color': self.c_scale.get_colour(value)
                    })

            print('x'*20, '\n\n')

    def add_to_geojson(self, lat, lng, props=None):
        if props is None:
            props = {}
        self.all_points.append(
            geojson.Feature(
                geometry=geojson.Point((lng, lat)),
                properties=props
            )
        )
        self.lnglats.append((lng, lat))

    def print_geojson(self, indents=True):
        ls = geojson.LineString(self.lnglats)
        self.all_points.append(geojson.Feature(geometry=ls))
        fc = geojson.FeatureCollection(self.all_points)
        print(geojson.dumps(fc))

        with open('jakarta_geo.json', 'w') as geo1:
            if indents:
                geo1.write(geojson.dumps(fc, indent=4))
            else:
                geo1.write(geojson.dumps(fc))

        print('\n\n\n')

        fc2 = geojson.FeatureCollection(self.bearing_features)
        print(geojson.dumps(fc2))
        with open('jakarta_bearing_geo.json', 'w') as geo2:
            if indents:
                geo2.write(geojson.dumps(fc2, indent=4))
            else:
                geo2.write(geojson.dumps(fc2))

    def print_dates(self):
        print(self.all_dates)
        print(sorted(self.all_dates))

    def cache(self, params):
        self.all_cache[params['img_name']] = params
        with open('cache.json', 'w') as c1:
            json.dump(self.all_cache, c1, indent=4)

    def load_cache(self):
        if os.path.exists('cache.json'):
            with open('cache.json', 'r') as c2:
                try:
                    self.all_cache = json.load(c2)
                except:
                    pass
        print(self.all_cache)

    def deg_to_bearing_line_coord(self, bdeg, line_length):
        radians = (bdeg - 90) * -0.0174533
        x_shift = line_length * math.sin(radians)
        y_shift = line_length * math.cos(radians)
        return x_shift, y_shift, radians

    def bearing_linestring_from_offset(self, lat, lng, x_shift, y_shift):
        return geojson.LineString((
            (lng, lat),
            (lng + y_shift, lat + x_shift)
        ))

    def add_feature(self, feature, properties):
        self.bearing_features.append(geojson.Feature(
            geometry=feature,
            properties=properties
        ))

    def add_bearing_star(self):
        lng = 0
        lat = 0
        line_length = 5
        for bdeg in range(0, 360, 10):
            x_shift, y_shift, radians = self.deg_to_bearing_line_coord(bdeg, line_length)
            ls = self.bearing_linestring_from_offset(lat, lng, x_shift, y_shift)
            self.add_feature(ls, {
                'bearing': bdeg,
                'radians': radians
            })
            self.add_arrow(radians, lat+x_shift, lng+y_shift, line_length*0.1)

    def add_arrow(self, radians, lat, lng, length, arrow_angle=0.1):
        arrow_x_shift = length * math.sin(math.pi + radians + (math.pi * arrow_angle))
        arrow_y_shift = length * math.cos(math.pi + radians + (math.pi * arrow_angle))
        arrow1 = geojson.LineString((
            (lng, lat),
            (lng + arrow_y_shift, lat + arrow_x_shift)
        ))
        self.bearing_features.append(geojson.Feature(
            geometry=arrow1, properties={}
        ))
        arrow_x_shift = length * math.sin(math.pi + radians + (math.pi * -arrow_angle))
        arrow_y_shift = length * math.cos(math.pi + radians + (math.pi * -arrow_angle))
        arrow2 = geojson.LineString((
            (lng, lat),
            (lng + arrow_y_shift, lat + arrow_x_shift)
        ))
        self.bearing_features.append(geojson.Feature(
            geometry=arrow2, properties={}
        ))


if __name__ == '__main__':
    img_location = "C:\\Users\\Ian Harvey\\OneDrive - Cardiff University\\Email attachments"
    ie = ImgExif()
    ie.load_cache()
    ie.read_exif(img_location, show_img=False)
    # ie.add_bearing_star()
    ie.print_geojson(indents=True)

