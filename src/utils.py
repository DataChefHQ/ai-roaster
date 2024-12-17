import json
import os
import boto3
from botocore.exceptions import ClientError
import requests

REGION = os.environ.get('REGION')
S3_BUCKET = os.environ.get('BUCKET_NAME')
s3_client = boto3.client('s3', region_name=REGION)
OPENAI_KEY_SECRET_NAME = os.environ.get('OPENAI_KEY_SECRET_NAME')


def get_openai_api_key():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=REGION)

    try:
        # Fetch the secret value
        response = client.get_secret_value(SecretId=OPENAI_KEY_SECRET_NAME)
        # Decrypt the secret if it is encrypted
        if "SecretString" in response:
            secret = response["SecretString"]
            secret_dict = json.loads(secret)
            return secret_dict[OPENAI_KEY_SECRET_NAME]
        else:
            raise Exception("Secret value not found on the secret manager.")
    except ClientError as e:
        raise Exception(f"Error retrieving secret: {e}")
    
def read_txt_file(filename: str) -> str:
    with open(filename, 'r') as file:
        content = file.read()
    return content

def synthesize_speech_to_stream(text, voice_id, language_code="en-US"):
    """
    Converts text to speech using Amazon Polly and returns the audio stream.

    :param text: The text to convert to speech.
    :param voice_id: The voice ID to use (e.g., Joanna, Matthew).
    :param language_code: The language code (e.g., en-US for US English).
    :return: AudioStream of the synthesized speech.
    """
    # Initialize Polly client
    polly_client = boto3.client('polly', region_name=REGION)

    try:
        # Request speech synthesis
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            LanguageCode=language_code
        )
        return response['AudioStream']
    except Exception as e:
        print(f"An error occurred during speech synthesis: {e}")
        raise


def upload_to_s3_and_get_presigned_url(audio_stream, s3_key, expiration=3600):
    """
    Uploads an audio stream to S3 and generates a pre-signed URL.

    :param audio_stream: The audio stream to upload.
    :param s3_key: The key (path) for the file in S3.
    :param expiration: Time in seconds for the pre-signed URL to remain valid.
    :return: A pre-signed URL for the uploaded file.
    """
    try:
        # Upload audio stream directly to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=audio_stream.read(),
            ContentType='audio/mpeg'
        )

        # Generate a pre-signed URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return presigned_url
    except Exception as e:
        print(f"An error occurred during S3 upload or URL generation: {e}")
        raise


def text_to_speech_s3(text, s3_key, voice_id="Matthew", language_code="en-US", expiration=3600):
    """
    Combines text-to-speech conversion and S3 upload with a pre-signed URL.

    :param text: The text to convert to speech.
    :param s3_key: The key (path) for the file in S3.
    :param voice_id: The voice ID to use (e.g., Joanna, Matthew).
    :param language_code: The language code (e.g., en-US for US English).
    :param expiration: Time in seconds for the pre-signed URL to remain valid.
    :return: A pre-signed URL for the uploaded file.
    """
    try:
        audio_stream = synthesize_speech_to_stream(text, voice_id, language_code)
        presigned_url = upload_to_s3_and_get_presigned_url(audio_stream, s3_key, expiration)
        print(f"Speech synthesis complete. File uploaded to S3 and available at {presigned_url}")
        return presigned_url
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def save_json_to_s3(object_key, data):
    """
    Save JSON data to an S3 bucket.

    :param object_key: S3 object key (path/filename in the bucket)
    :param data: Python dictionary to save as JSON
    """
    json_data = json.dumps(data)  # Serialize data to JSON
    s3_client.put_object(Bucket=S3_BUCKET, Key=object_key, Body=json_data)
    print(f"Data successfully saved to s3://{S3_BUCKET}/{object_key}")


def load_json_from_s3(object_key):
    """
    Load JSON data from an S3 bucket.

    :param object_key: S3 object key (path/filename in the bucket)
    :return: Python dictionary with the JSON data
    """
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=object_key)
    json_data = response['Body'].read().decode('utf-8')  # Read and decode the body
    return json.loads(json_data)  # Parse JSON into a dictionary


def upload_image_to_s3(image_url, s3_key):
    try:
        # Fetch the image content from the URL
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for HTTP errors

        s3_client = boto3.client('s3', region_name=REGION)
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=response.content,
            ContentType=response.headers['Content-Type']  # Preserve the original content type
        )
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=604800
        )
        return presigned_url
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the image: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return ""