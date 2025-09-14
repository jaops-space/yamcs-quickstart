
import time
import argparse
from PIL import Image, ImageDraw, ImageFont
import os
from yamcs.client import YamcsClient, Credentials

# Configuration constants
YAMCS_HOST = "localhost:8090"
YAMCS_INSTANCE = "myproject"
YAMCS_PROCESSOR = "realtime"
IMG_DIR = "/tmp/images"
WIDTH = 640
HEIGHT = 480
SLEEP_INTERVAL = 5

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", default="operator")
parser.add_argument("-p", "--password", default="tobechanged")
args = parser.parse_args()

# Try without credentials first, then with credentials if needed
try:
    client = YamcsClient(YAMCS_HOST)
    processor = client.get_processor(instance=YAMCS_INSTANCE, processor=YAMCS_PROCESSOR)
    _ = processor.name  # Test if authentication is actually working by accessing processor info
    print("Connected without authentication")
except Exception as e:
    print(f"When connecting to Yamcs without authentication and trying to access processor name, got error: {e}")
    print(f"Now trying using credentials")
    credentials = Credentials(username=args.username, password=args.password)
    client = YamcsClient(YAMCS_HOST, credentials=credentials)
    processor = client.get_processor(instance=YAMCS_INSTANCE, processor=YAMCS_PROCESSOR)
    print(f"Connected with username {args.username}")

os.makedirs(IMG_DIR, exist_ok=True)

font = ImageFont.load_default(HEIGHT//10) # Use default font with size based on height

n = 1
while True:
    # Create a blank white image with black text centered
    img = Image.new('RGB', (WIDTH, HEIGHT), color='white')
    d = ImageDraw.Draw(img)
    text = f"image {n}"
    bbox = d.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (WIDTH - text_width) // 2
    y = (HEIGHT - text_height) // 2
    d.text((x, y), text, font=font, fill='black')

    # Save image with 4 leading zero padding
    image_name = f"image_{n:04d}.png"
    img_path = f"{IMG_DIR}/{image_name}" 
    img.save(img_path)
    print(f"Saved {img_path}")
    url_storage = f"/storage/buckets/images/objects/{image_name}"
    url_full = f"http://{YAMCS_HOST}/api{url_storage}"
    processor.set_parameter_values({
        "/images/number": n,
        "/images/url_storage": url_storage,
        "/images/url_full": url_full,
    })

    n += 1
    time.sleep(SLEEP_INTERVAL)