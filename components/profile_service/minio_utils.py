import boto3
import uuid
from botocore.exceptions import ClientError, EndpointConnectionError


class MinIOClient:
    def __init__(self, bucket_name: str, endpoint_url: str, access_key: str, secret_key: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def upload_file(self, file_data: bytes, file_name: str) -> str:
        """
        Uploads a file to the specified S3 bucket.

        Args:
            file_data (bytes): File content in bytes.
            file_name (str): File name to store in the bucket.

        Returns:
            str: Publicly accessible S3 file URL.
        """
        try:
            self._ensure_bucket_exists()
            unique_file_name = f"{file_name}_{uuid.uuid4()}"  # Generate unique file name
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_file_name,
                Body=file_data,
                ContentType="image/jpeg",  # Specify file type (Change based on file type)
            )
            # Return the object URL
            return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{unique_file_name}"
        except ClientError as e:
            raise Exception(f"Failed to upload file to MinIO: {e}")

    def _ensure_bucket_exists(self):
        """
        Check if the bucket exists and create it if it does not.
        """
        try:
            # Check if the bucket exists
            response = self.s3_client.list_buckets()
            buckets = [bucket["Name"] for bucket in response.get("Buckets", [])]

            if self.bucket_name not in buckets:
                # Create the bucket if it doesn't exist
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"Bucket '{self.bucket_name}' created successfully.")
        except EndpointConnectionError as e:
            raise Exception(f"Unable to connect to the MinIO server: {e}")
        except ClientError as e:
            raise Exception(f"Error ensuring bucket existence: {e}")

