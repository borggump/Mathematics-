import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gnupg
import getpass

def encrypt_message(recipient_email, message, public_key_path):
    gpg = gnupg.GPG()
    
    with open(public_key_path, 'rb') as f:
        key_data = f.read()
    
    import_result = gpg.import_keys(key_data)
    
    encrypted_data = gpg.encrypt(message, recipient_email)
    
    if encrypted_data.ok:
        return str(encrypted_data)
    else:
        return None

def send_email(sender_email, sender_password, recipient_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    
    message.attach(MIMEText(body, 'plain'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

def main():
    sender_email = input("Enter your Gmail address: ")
    sender_password = getpass.getpass("Enter your Gmail password or app password: ")
    recipient_email = input("Enter recipient's email address: ")
    subject = input("Enter email subject: ")
    message = input("Enter your message: ")
    public_key_path = input("Enter the path to the recipient's public key file: ")

    encrypted_message = encrypt_message(recipient_email, message, public_key_path)
    
    if encrypted_message:
        print("Message encrypted successfully.")
        send_email(sender_email, sender_password, recipient_email, subject, encrypted_message)
        print("Encrypted email sent successfully.")
    else:
        print("Encryption failed. Please check the public key and try again.")

if __name__ == "__main__":
    main()