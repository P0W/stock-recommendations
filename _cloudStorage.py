# Imports the Google Cloud client library
from google.cloud import storage


def uploadDB(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket_name = "stocks-db-bucket"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )


def downloadDB(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    bucket_name = "stocks-db-bucket"
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )
