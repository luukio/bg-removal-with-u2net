import io
import os
import sys
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import numpy as np
import time
import logging

import u2net

logging.basicConfig(level=logging.INFO)

# Initialize the Flask application
app = Flask(__name__)
CORS(app)


# Simple probe.
@app.route('/', methods=['GET'])
def hello():
    return 'Hello U^2-Net!'


# Route http posts to this method
@app.route('/', methods=['POST'])
def run():
    start = time.time()

    # Convert string of image data to uint8
    if 'data' not in request.files:
        return jsonify({'error': 'missing file param `data`'}), 400
    data = request.files['data'].read()
    if len(data) == 0:
        return jsonify({'error': 'empty image'}), 400

    # Convert string data to PIL Image
    img = Image.open(io.BytesIO(data))

    # Ensure i,qge size is under 1024
    if img.size[0] > 1024 or img.size[1] > 1024:
        img.thumbnail((1024, 1024))

    # Process Image
    res = u2net.run(np.array(img))

    # Convert to BW and make it to the size of original image
    mask = res.convert('L').resize((img.width, img.height))

    # Making final composite
    logging.info(' > compositing final image...')
    empty = Image.new("RGBA", img.size, 0)
    img = Image.composite(img, empty, mask)

    # Save to buffer
    buff = io.BytesIO()
    img.save(buff, 'PNG')
    buff.seek(0)

    # Print stats
    logging.info(f'Completed in {time.time() - start:.2f}s')

    # Return data
    return send_file(buff, mimetype='image/png')


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
