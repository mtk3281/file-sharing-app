from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for configuration
app.secret_key = os.getenv('SECRET_KEY')
S3_BUCKET = os.getenv('S3_BUCKET')

s3 = boto3.client('s3')

upload_folder = '/tmp'

app.config['UPLOAD_FOLDER'] = upload_folder

Allowed_Extensions = set(['txt', 'pdf', 'png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Allowed_Extensions

@app.route('/')
def index():
    # List files in the S3 bucket
    s3_objects = s3.list_objects_v2(Bucket=S3_BUCKET)
    files = [obj['Key'] for obj in s3_objects.get('Contents', [])]
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle file upload
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Upload file to S3
        s3.upload_file(filepath, S3_BUCKET, filename)
        flash(f'Successfully uploaded {filename}')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    # Generate a pre-signed URL for secure download
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': filename},
        ExpiresIn=3600  # URL expires in 1 hour
    )
    return redirect(url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
