import boto3
import os
import json
import csv
from io import StringIO


class AWS_S3:
    def __init__(self):
        with open("cred.json", "r") as fh:
            creds = json.load(fh)
            self.aws_access_key = creds["aws_access_key"]
            self.aws_secret_key = creds["aws_secret_key"]
            self.aws_region_name = creds["aws_region_name"]

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region_name,
        )
        self.bucket = "tickertape-screener-bucket"

    def upload_file(self, file_name):
        object_name = os.path.basename(file_name)
        try:
            response = self.s3_client.upload_file(file_name, self.bucket, object_name)
        except:
            return False
        return True

    def download_file(self, file_name):
        try:
            obj = self.s3_client.get_object(Bucket=self.bucket, Key=file_name)
            data = obj["Body"].read().decode()
        except Exception as e:
            print("Error", e)
            return None
        return data


if __name__ == "__main__":
    content = AWS_S3().download_file("results.csv")
    file = StringIO(content)
    input_file = csv.DictReader(file)
    for rows in input_file:
        for item in rows:
            if item == "ticker":
                print(rows["ticker"])
    # csv_data = csv.reader(file, delimiter=",")
    # for row in csv_data:
    #     print(row['ticker'])
    # AWS_S3().upload_file('results.csv')
