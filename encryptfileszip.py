import os
import zipfile
from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def generate_key():
    return Fernet.generate_key()

def encrypt_file(key, input_file, output_file):
    with open(input_file, 'rb') as f:
        data = f.read()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)
    with open(output_file, 'wb') as f:
        f.write(encrypted)

def encrypt_directory(directory, key):
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            encrypted_file_path = file_path + '.encrypted'
            encrypt_file(key, file_path, encrypted_file_path)
            os.remove(file_path)  # Remove the original file

def zip_directory(directory, output_filename):
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory)
                zipf.write(file_path, arcname)

def get_google_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(service, file_path, file_name):
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f'File ID: {file.get("id")}')

def main():
    directory = input("Enter the directory path to encrypt and upload: ")
    key = generate_key()
    print(f"Encryption key: {key.decode()}  (Save this securely!)")

    # Encrypt all files in the directory
    encrypt_directory(directory, key)
    print("All files encrypted.")

    # Zip the directory
    zip_file_name = os.path.basename(directory) + '_encrypted.zip'
    zip_file_path = os.path.join(os.path.dirname(directory), zip_file_name)
    zip_directory(directory, zip_file_path)
    print(f"Directory zipped to {zip_file_path}")

    # Upload to Google Drive
    service = get_google_drive_service()
    upload_to_drive(service, zip_file_path, zip_file_name)
    print(f"File {zip_file_name} uploaded to Google Drive")

    # Clean up: remove the zip file
    os.remove(zip_file_path)
    print("Temporary zip file removed")

if __name__ == '__main__':
    main()