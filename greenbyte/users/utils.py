import os
import secrets 
from PIL import Image
from flask import url_for, current_app
from greenbyte import mail
from flask_mail import Message


def savePicture(formPicture):
    random_hex = secrets.token_hex(8)
    _, fExt = os.path.splitext(formPicture.filename)
    pictureFileName = random_hex + fExt
    picturePath = os.path.join(current_app.root_path, 'static/profilePics', pictureFileName)
    outputSize = (125,125)
    i = Image.open(formPicture )
    i.thumbnail(outputSize)
    i.save(picturePath)
    return pictureFileName

def sendResetEmail(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='bigmamafreak@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('utils.resetToken', token=token, _external=True)}
If you did not make this request, simply ignore the email and no changes will be made
'''
    mail.send(msg)
