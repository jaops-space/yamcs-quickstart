
import time
from PIL import Image, ImageDraw, ImageFont
import os
from yamcs.client import YamcsClient


client = YamcsClient("localhost:8090")
processor = client.get_processor(instance="myproject", processor="realtime")

imgdir="/tmp/images"
os.makedirs(imgdir, exist_ok=True)
WIDTH = 640
HEIGHT = 480

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
    img_path = f"{imgdir}/{image_name}" 
    img.save(img_path)
    print(f"Saved {img_path}")
    url_storage = f"/storage/buckets/images/objects/{image_name}"
    url_full = f"http://localhost:8090/api{url_storage}"
    processor.set_parameter_values({
        "/images/number": n,
        "/images/url_storage": url_storage,
        "/images/url_full": url_full,
    })

    n += 1
    time.sleep(5)