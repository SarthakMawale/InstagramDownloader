from flask import Flask, render_template, request, jsonify, send_from_directory
import instaloader
import os
import re
from urllib.parse import unquote

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = os.path.join(os.getcwd(), 'downloads')
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Configure Instaloader
L = instaloader.Instaloader(
    dirname_pattern=app.config['DOWNLOAD_FOLDER'],
    save_metadata=False,
    download_videos=True,
    download_pictures=False,
    download_geotags=False,
    download_comments=False,
    compress_json=False
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Validate Instagram URL
    if not re.match(r'https?://(www\.)?instagram\.com/(p|reel|tv)/[a-zA-Z0-9_-]+/?', url):
        return jsonify({'error': 'Invalid Instagram URL'}), 400
    
    try:
        shortcode = url.split('/')[-2]
        
        # Clear download folder before new download
        for f in os.listdir(app.config['DOWNLOAD_FOLDER']):
            os.remove(os.path.join(app.config['DOWNLOAD_FOLDER'], f))
        
        # Download the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=shortcode)
        
        # Find the downloaded video file
        video_files = [f for f in os.listdir(app.config['DOWNLOAD_FOLDER']) 
                      if f.endswith('.mp4')]
        
        if not video_files:
            return jsonify({'error': 'No video file found after download'}), 404
        
        video_filename = video_files[0]
        
        return jsonify({
            'success': True,
            'filename': video_filename,
            'video_url': f'/video/{video_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/video/<filename>')
def serve_video(filename):
    try:
        # Serve the video for both playback and download
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            filename,
            as_attachment=False,  # Changed to False for playback
            mimetype='video/mp4'
        )
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
