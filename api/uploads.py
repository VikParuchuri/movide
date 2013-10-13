import re
import time
from datetime import datetime
from django.conf import settings
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket
import os

def upload_to_s3(file_obj, class_name):
    filename = re.sub(r'[^0-9a-zA-Z\.]', '', file_obj.name.lower().encode("ascii", "ignore"))
    filename = "{0}/{1}_{2}".format(class_name, int(time.mktime(datetime.now().timetuple())), filename)
    file_obj.seek(0)
    if settings.AWS_ACCESS_KEY_ID != "":
        conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.create_bucket(settings.S3_BUCKETNAME.lower())
        k = Key(bucket)
        k.key = filename
        k.set_contents_from_string(file_obj.read())
        file_obj.close()
        url = conn.generate_url(settings.S3_FILE_TIMEOUT, 'GET', bucket=settings.S3_BUCKETNAME, key=filename)
    else:
        filepath = os.path.abspath(os.path.join(settings.FILE_UPLOAD_PATH, class_name, filename))
        directory = os.path.dirname(filepath)

        # Create class directory if it doesn't exist.
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, "w") as f:
            f.write(file_obj.read())
        url = os.path.abspath(os.path.join(settings.FILE_UPLOAD_URL, class_name, filename))

    return url, filename

def get_temporary_s3_url(key):
    if settings.AWS_ACCESS_KEY_ID != "":
        s3 = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, is_secure=False)
        file_url = s3.generate_url(settings.S3_FILE_TIMEOUT, 'GET', bucket=settings.S3_BUCKETNAME.lower(), key=key)
    else:
        file_url = os.path.abspath(os.path.join(settings.FILE_UPLOAD_URL, key))
    return file_url

