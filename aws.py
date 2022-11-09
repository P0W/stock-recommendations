import boto3
import pandas
import os
import json


class AWS_S3:
    def __init__(self):
        with open("cred.json", "r") as fh:
            creds = json.load(fh)
            self.aws_access_key = creds["aws_access_key"]
            self.aws_secret_key = creds["aws_secret_key"]

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name="ap-south-1",
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
            data = pandas.read_csv(obj["Body"])
        except:
            return None
        return data


if __name__ == "__main__":
    #data = AWS_S3().download_file("results.csv")
    #print(data["ticker"].tolist())
    AWS_S3().upload_file('results.csv')
