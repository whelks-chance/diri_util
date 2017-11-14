import os
import exifread
import dateutil.parser


class ImgExif:

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

                if 'GPS GPSDate' in tags.keys():
                    # 2008-08-09T18:39:22Z
                    # Lets build a datetime string!
                    time_str, time_obj = self.exif_date_to_iso8601(
                        tags['GPS GPSDate'],
                        tags['GPS GPSTimeStamp']
                    )
                    print('\n', 'datetime.datetime object:', time_obj)
                    print(time_str)

                print(len(gps_keys))
                print('x'*20, '\n\n')

if __name__ == '__main__':
    img_location = "C:\\Users\\Ian Harvey\\OneDrive - Cardiff University\\Email attachments"
    ie = ImgExif()
    ie.read_exif(img_location)
