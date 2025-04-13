from flask import Flask, render_template, request, send_file, url_for, redirect, flash
from PIL import Image
import os
import io
import uuid

app = Flask(__name__)
app.secret_key = "image-converter-secret-key"

# Create uploads folder if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']

    # Check if file is selected
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    # Check if file is valid
    if not file or not allowed_file(file.filename):
        flash('Invalid file type. Allowed formats: PNG, JPG, JPEG, GIF, WebP, BMP')
        return redirect(url_for('index'))

    # Get form data
    target_format = request.form.get('format', 'png').lower()
    resize = request.form.get('resize', 'no')

    try:
        # Open image
        img = Image.open(file.stream)

        # Handle resize
        if resize == 'yes':
            width = int(request.form.get('width', 0))
            height = int(request.form.get('height', 0))

            # If both dimensions are provided
            if width > 0 and height > 0:
                img = img.resize((width, height), Image.LANCZOS)
            # If only width is provided, maintain aspect ratio
            elif width > 0:
                aspect_ratio = img.height / img.width
                new_height = int(width * aspect_ratio)
                img = img.resize((width, new_height), Image.LANCZOS)
            # If only height is provided, maintain aspect ratio
            elif height > 0:
                aspect_ratio = img.width / img.height
                new_width = int(height * aspect_ratio)
                img = img.resize((new_width, height), Image.LANCZOS)

        # Save to memory
        output = io.BytesIO()

        # Set format-specific parameters
        if target_format == 'jpg' or target_format == 'jpeg':
            # Convert RGBA to RGB if needed as JPEG doesn't support alpha channel
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            quality = int(request.form.get('quality', 90))
            img.save(output, format=target_format.upper(), quality=quality)
        elif target_format == 'png':
            compression = int(request.form.get('compression', 6))  # 0-9, higher is more compression
            img.save(output, format='PNG', compress_level=compression)
        elif target_format == 'webp':
            quality = int(request.form.get('quality', 80))
            img.save(output, format='WEBP', quality=quality)
        else:
            img.save(output, format=target_format.upper())

        output.seek(0)

        # Generate a unique filename
        new_filename = f"{uuid.uuid4().hex}.{target_format}"

        # Return the processed image for download
        return send_file(
            output,
            download_name=new_filename,
            as_attachment=True,
            mimetype=f'image/{target_format}'
        )

    except Exception as e:
        flash(f'Error processing image: {str(e)}')
        return redirect(url_for('index'))


@app.route('/batch', methods=['GET', 'POST'])
def batch():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('No files part')
            return redirect(url_for('batch'))

        files = request.files.getlist('files[]')

        if not files or files[0].filename == '':
            flash('No files selected')
            return redirect(url_for('batch'))

        # Process each file
        # For actual batch processing, we would need to implement a way to
        # zip multiple files and download them together
        flash('Batch processing not fully implemented in this demo')
        return redirect(url_for('batch'))

    return render_template('batch.html')


# Templates directory
if not os.path.exists('templates'):
    os.makedirs('templates')

# Create templates
with open('templates/base.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Image Converter and Resizer{% endblock %}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="file"], 
        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #2980b9;
        }
        .flash-messages {
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .flash-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .flash-success {
            background-color: #d4edda;
            color: #155724;
        }
        .toggle-container {
            margin-bottom: 15px;
        }
        .hidden {
            display: none;
        }

        nav {
            margin-bottom: 20px;
        }
        nav a {
            margin-right: 15px;
            text-decoration: none;
            color: #3498db;
        }
        nav a:hover {
            text-decoration: underline;
        }
        footer {
            margin-top: 30px;
            text-align: center;
            font-size: 0.8em;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <nav>
            <a href="{{ url_for('index') }}">Single File</a>
            <a href="{{ url_for('batch') }}">Batch Processing</a>
        </nav>

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="flash-messages flash-error">
                    <ul>
                        {% for message in messages %}
                            <li>{{ message }}</li>
                        {% endfor %}
                    </ul>
                </div>
            {% endif %}
        {% endwith %}

        {% block content %}
        {% endblock %}

        <footer>
            <p>Made with Pillow and Flask</p>
        </footer>
    </div>

    {% block scripts %}
    {% endblock %}
</body>
</html>''')

with open('templates/index.html', 'w') as f:
    f.write('''{% extends "base.html" %}

{% block title %}Image Converter and Resizer{% endblock %}

{% block content %}
    <h1>Image Converter and Resizer</h1>
    <form action="{{ url_for('convert') }}" method="post" enctype="multipart/form-data">
        <div class="form-group">
            <label for="file">Select Image:</label>
            <input type="file" id="file" name="file" accept=".png,.jpg,.jpeg,.gif,.webp,.bmp">
        </div>

        <div class="form-group">
            <label for="format">Convert to:</label>
            <select id="format" name="format">
                <option value="png">PNG</option>
                <option value="jpg">JPG</option>
                <option value="webp">WebP</option>
                <option value="gif">GIF</option>
                <option value="bmp">BMP</option>
            </select>
        </div>

        <div id="format-options" class="form-group">
            <!-- Format-specific options will be shown here -->
        </div>

        <div class="toggle-container">
            <label>
                <input type="checkbox" id="resize-toggle"> Resize image
            </label>
        </div>

        <div id="resize-options" class="form-group hidden">
            <input type="hidden" name="resize" id="resize" value="no">
            <div class="form-group">
                <label for="width">Width (px):</label>
                <input type="number" id="width" name="width" placeholder="Leave empty to maintain aspect ratio">
            </div>
            <div class="form-group">
                <label for="height">Height (px):</label>
                <input type="number" id="height" name="height" placeholder="Leave empty to maintain aspect ratio">
            </div>
        </div>

        <div class="form-group">
            <button type="submit">Convert & Download</button>
        </div>
    </form>
{% endblock %}

{% block scripts %}
<script>
    // Handle format options
    const formatSelect = document.getElementById('format');
    const formatOptions = document.getElementById('format-options');

    function updateFormatOptions() {
        const format = formatSelect.value;
        let optionsHTML = '';

        if (format === 'jpg' || format === 'webp') {
            optionsHTML = `
                <label for="quality">Quality (1-100):</label>
                <input type="number" id="quality" name="quality" value="85" min="1" max="100">
            `;
        } else if (format === 'png') {
            optionsHTML = `
                <label for="compression">Compression Level (0-9):</label>
                <input type="number" id="compression" name="compression" value="6" min="0" max="9">
            `;
        }

        formatOptions.innerHTML = optionsHTML;
    }

    formatSelect.addEventListener('change', updateFormatOptions);
    updateFormatOptions();

    // Handle resize toggle
    const resizeToggle = document.getElementById('resize-toggle');
    const resizeOptions = document.getElementById('resize-options');
    const resizeInput = document.getElementById('resize');

    resizeToggle.addEventListener('change', function() {
        if (this.checked) {
            resizeOptions.classList.remove('hidden');
            resizeInput.value = 'yes';
        } else {
            resizeOptions.classList.add('hidden');
            resizeInput.value = 'no';
        }
    });
</script>
{% endblock %}''')

with open('templates/batch.html', 'w') as f:
    f.write('''{% extends "base.html" %}

{% block title %}Batch Image Processing{% endblock %}

{% block content %}
    <h1>Batch Image Processing</h1>
    <p>Upload multiple images to process them at once.</p>

    <form action="{{ url_for('batch') }}" method="post" enctype="multipart/form-data">
        <div class="form-group">
            <label for="files">Select Images:</label>
            <input type="file" id="files" name="files[]" multiple accept=".png,.jpg,.jpeg,.gif,.webp,.bmp">
        </div>

        <div class="form-group">
            <label for="batch-format">Convert all to:</label>
            <select id="batch-format" name="format">
                <option value="png">PNG</option>
                <option value="jpg">JPG</option>
                <option value="webp">WebP</option>
                <option value="gif">GIF</option>
                <option value="bmp">BMP</option>
            </select>
        </div>

        <div class="toggle-container">
            <label>
                <input type="checkbox" id="batch-resize-toggle"> Resize all images
            </label>
        </div>

        <div id="batch-resize-options" class="form-group hidden">
            <input type="hidden" name="resize" id="batch-resize" value="no">
            <div class="form-group">
                <label for="batch-width">Width (px):</label>
                <input type="number" id="batch-width" name="width" placeholder="Leave empty to maintain aspect ratio">
            </div>
            <div class="form-group">
                <label for="batch-height">Height (px):</label>
                <input type="number" id="batch-height" name="height" placeholder="Leave empty to maintain aspect ratio">
            </div>
        </div>

        <div class="form-group">
            <button type="submit">Process & Download</button>
        </div>
    </form>
    <p><em>Note: This is a demo version. In a full implementation, processed files would be zipped together for download.</em></p>
{% endblock %}

{% block scripts %}
<script>
    // Handle resize toggle for batch
    const batchResizeToggle = document.getElementById('batch-resize-toggle');
    const batchResizeOptions = document.getElementById('batch-resize-options');
    const batchResizeInput = document.getElementById('batch-resize');

    batchResizeToggle.addEventListener('change', function() {
        if (this.checked) {
            batchResizeOptions.classList.remove('hidden');
            batchResizeInput.value = 'yes';
        } else {
            batchResizeOptions.classList.add('hidden');
            batchResizeInput.value = 'no';
        }
    });
</script>
{% endblock %}''')

if __name__ == '__main__':
    app.run(debug=True)