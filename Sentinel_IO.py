# import required libraries
import boto3

# Define repository
HOST = 'http://data.cloud.code-de.org'
BUCKET = 'CODEDE'


class SentinelIOClient():
    def __init__(self, access_key, secret_key):
        self.ACCESS_KEY = access_key
        self.SECRET_KEY = secret_key
        self.aws_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                       endpoint_url=HOST)

    def get_data_file_keys(self, collection: str, date: str, tile_id: str, resolution: str, bands: list,
                           max_directory_depth=5):
        prefix = collection + date + '/'
        i = 0
        data_keys = []
        while i < max_directory_depth and data_keys == []:  # Schleife durch die Ebenen
            #             print(prefix)
            try:
                objects = [i for i in
                           self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix, MaxKeys=30000)[
                               'CommonPrefixes']]

            except KeyError:
                try:
                    objects = [i for i in self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix,
                                                                       MaxKeys=30000)['Contents']]
                except KeyError:
                    print(self.aws_client.list_objects(Delimiter='/', Bucket='CODEDE', Prefix=prefix, MaxKeys=30000))
                    raise KeyError('The object does neither feature the key \'CommonPrefixes\' nor \'Contents\'')

            for object_key in objects:  # Schleife durch die Objekte einer Ebene
                try:
                    if tile_id in object_key['Prefix'].split('/')[-2]:  # enter GRANULE data
                        prefix = object_key['Prefix']
                        if not tile_id + '_A0' in object_key['Prefix'].split('/')[-2]:
                            prefix += 'GRANULE/'
                            continue

                    if object_key['Prefix'].endswith('IMG_DATA/'):
                        prefix = object_key['Prefix']
                        continue

                    if object_key['Prefix'].endswith('R' + resolution + '/'):
                        prefix = object_key['Prefix']
                        continue

                except KeyError:
                    try:
                        if object_key['Key'].endswith('.jp2'):
                            if object_key['Key'][-11:-8] in bands or object_key['Key'][
                                                                     -7:-4] in bands:  # assumes ending of key like: ...T103021_B04_10m.jp2
                                data_keys.append(object_key['Key'])

                    except KeyError as err:
                        print(f"The object does neither feature the key \"Prefix\" nor \"Key\":")
                        print(object_key)

            i += 1

        print(f"{len(data_keys)} elements have been found")
        for key in data_keys:
            print(key)
        return data_keys

    def download_band_data(self, target_files: list, download_files: list):
        if len(target_files) != len(download_files):
            raise ValueError('The file lists have to be the same length.')

        for i_file in range(len(target_files)):
            with open(target_files[i_file], 'wb') as data:
                self.aws_client.download_fileobj('CODEDE', download_files[i_file], data)
