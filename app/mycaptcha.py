from PIL import ImageFont, ImageDraw, Image
import cv2
import numpy as np
import random
import string
import glob
import io
import jwt
import os
from app import app
# from flask import send_file

def gen_captcha():
    # Setting up the canvas
    size = random.randint(30,40)
    length = random.randint(5,8)
    img = np.zeros((90, 240, 3), np.uint8) # np.zeros(((size*2)+5, length*size, 3), np.uint8)
    img_pil = Image.fromarray(img+255)

    # Get Fonts
    font_path = os.getcwd() + '/Fonts' #r'\Fonts'
    fonts = glob.glob(f'{font_path}/arial*.ttf')

    # Drawing text and lines
    font = ImageFont.truetype(random.choice(fonts), random.randint(36,48))
    draw = ImageDraw.Draw(img_pil)
    text = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length)) # + string.ascii_lowercase
    txt_token = jwt.encode({'text': text}, app.config['SECRET_KEY'], algorithm="HS256")
    fill = random.randint(0, 255), random.randint(0,255), random.randint(0,255)
    draw.text((random.randint(15, 30), random.randint(8, 16)), text, font=font,
              fill=fill)
    draw.line([(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))
               ,(random.choice(range(length*size)), random.choice(range((size*2)+5)))]
              , width=2, fill=fill)

    # Adding noise and blur
    img = np.array(img_pil)
    thresh = random.randint(1,5)/100
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            rdn = random.random()
            if rdn < thresh:
                img[i][j] = random.randint(0,123)
            elif rdn > 1-thresh:
                img[i][j] = random.randint(123,255)
    # img = cv2.blur(img, (int(size/random.randint(5, 10)), int(size/random.randint(5, 10))))
    img = cv2.blur(img, (int(random.randint(5, 7)), int(random.randint(5, 7))))
    img_io = io.BytesIO()
    img2 = Image.fromarray(img)
    img2.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return text, img_io, txt_token #send_file(img_io, mimetype='image/jpeg')
