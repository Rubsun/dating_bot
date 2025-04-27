import boto3
import uuid
from botocore.exceptions import ClientError, EndpointConnectionError
from loguru import logger

class MinIOClient:
    def __init__(self, bucket_name: str, endpoint_url: str, access_key: str, secret_key: str):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        logger.info(f"Initializing MinIOClient for bucket: {bucket_name} at {endpoint_url}")
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
        logger.info(f"Attempting to upload file '{file_name}' to bucket '{self.bucket_name}'.")
        logger.debug(f"File size: {len(file_data)} bytes.")

        try:
            self._ensure_bucket_exists()
            unique_file_name = f"{file_name}_{uuid.uuid4()}"  # Generate unique file name
            logger.debug(f"Generated unique file name: '{unique_file_name}'")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_file_name,
                Body=file_data,
                ContentType="image/jpeg",  # Specify file type (Change based on file type)
            )
            # Return the object URL
            file_url = f"{self.endpoint_url}/{self.bucket_name}/{unique_file_name}"
            logger.info(f"File '{unique_file_name}' uploaded successfully to bucket '{self.bucket_name}'. URL: {file_url}")
            return file_url

        except ClientError as e:
            logger.exception(f"Failed to upload file '{file_name}' to MinIO bucket '{self.bucket_name}'. Error: {e}")
            raise Exception(f"Failed to upload file to MinIO: {e}")
        except Exception as e:
             logger.exception(f"An unexpected error occurred during file upload for '{file_name}'. Error: {e}")
             raise


    def _ensure_bucket_exists(self):
        """
        Check if the bucket exists and create it if it does not.
        """
        logger.debug(f"Ensuring bucket '{self.bucket_name}' exists.")
        try:
            # Check if the bucket exists
            response = self.s3_client.list_buckets()
            buckets = [bucket["Name"] for bucket in response.get("Buckets", [])]

            if self.bucket_name not in buckets:
                # Create the bucket if it doesn't exist
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created successfully.")
        except EndpointConnectionError as e:
            logger.error(f"Unable to connect to the MinIO server at {self.endpoint_url} while ensuring bucket existence. Error: {e}")
            raise Exception(f"Unable to connect to the MinIO server: {e}")
        except ClientError as e:
            logger.exception(f"Failed to create bucket '{self.bucket_name}'. Error: {e}")
            raise Exception(f"Error ensuring bucket existence: {e}")

