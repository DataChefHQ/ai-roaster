import json
import os
from flask import Flask, render_template, jsonify, request
import boto3
import awsgi
from .bedrock import find_chef, roast_chef, generate_roast_image_url
from .utils import load_json_from_s3

app = Flask(__name__)
s3 = boto3.client('s3')
S3_BUCKET = os.environ.get('BUCKET_NAME')
REGION = os.environ.get('REGION')


@app.after_request
def add_cache_control(response):
    # Disable caching for all responses
    response.cache_control.no_store = True
    response.expires = -1
    response.headers['Pragma'] = 'no-cache'
    return response


def sign_s3_file(key):
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=3600  # URL valid for 1 hour
    )
    return url


def list_images():
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix='team/')
    images = []
    if 'Contents' in response:
        for item in response['Contents']:
            images.append(item['Key'])
    return images


def get_image(chef):
    all_images = list_images()
    for image in all_images:
        if f'team/{chef.lower()}.' in image.lower():
            return image
    return "not-found.png"


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', s3_bucket=S3_BUCKET, region=REGION)


@app.route('/share/<roast_id>', methods=['GET'])
def share(roast_id):
    result = load_json_from_s3(f"results/roasts/{roast_id}.json")
    return render_template(
        'index.html',
        image=sign_s3_file(get_image(result['name'])),
        roast_image=sign_s3_file(result['image_key']),
        roast= result['roast'].replace('"', ''),
        roast_audio_s3_url= sign_s3_file(result['audio_key']),
        s3_bucket=S3_BUCKET,
        region=REGION
    )


@app.route('/image', methods=['POST'])
def roast_image():
    return jsonify(generate_roast_image_url(request.get_json()))


@app.route('/find', methods=['POST'])
def submit():
    return jsonify(find_chef(request.get_json()))


@app.route('/roast', methods=['POST'])
def roast():
    result = roast_chef(request.get_json())
    return jsonify({
        "url": sign_s3_file(get_image(result['name'])),
        "roast_image": sign_s3_file("generating-roast.png"),
        "roast": result['roast'].replace('"', ''),
        "roast_audio_s3_url": result['roast_audio_s3_url'],
        "roast_id": result['roast_id'],
    })


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def catch_all(path):
    """Catches all requests."""
    return jsonify({'error': f'Path {path} is not allowed.'}), 404


def lambda_handler(event, context):
    if 'source' in event and event['source'] == 'serverless-plugin-warmup':
        return {}
    print(json.dumps(event))
    return awsgi.response(app, event, context)


if __name__ == "__main__":
    app.run(debug=True)
