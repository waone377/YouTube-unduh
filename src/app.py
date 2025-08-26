from flask import Flask, request, render_template, jsonify, Response, send_from_directory
import yt_dlp
import os
import uuid
import threading
import json
import time

# Inisialisasi aplikasi Flask
app = Flask(__name__)
app.secret_key = 'kunci_rahasia_super_aman'

# Konfigurasi folder untuk menyimpan file unduhan permanen
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'permanent_downloads')
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Dictionary untuk melacak progres unduhan setiap tugas
download_progress = {}

# Fungsi untuk membersihkan file lama secara periodik
def cleanup_old_files():
    while True:
        # Cek setiap jam
        time.sleep(3600)
        for filename in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    # Hapus file jika lebih tua dari 1 jam (3600 detik)
                    if (time.time() - os.path.getmtime(file_path)) > 3600:
                        os.unlink(file_path)
            except Exception as e:
                print(f"Error saat membersihkan file lama: {e}")

# Jalankan thread pembersihan di latar belakang
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# Hook yang dipanggil oleh yt-dlp untuk melaporkan progres
def progress_hook(d):
    task_id = d['info_dict']['task_id']
    if d['status'] == 'downloading':
        percent_str = d.get('_percent_str', '0.0%').strip().replace('%', '')
        try:
            percent = float(percent_str)
        except ValueError:
            percent = 0.0
        download_progress[task_id] = {
            'status': 'mengunduh',
            'percent': percent,
            'eta': d.get('eta', 0),
            'speed': d.get('_speed_str', 'N/A')
        }
    elif d['status'] == 'finished':
        final_filename = os.path.basename(d['filename'])
        download_progress[task_id] = {
            'status': 'selesai',
            'percent': 100,
            'filename': final_filename
        }
    elif d['status'] == 'error':
        download_progress[task_id] = {'status': 'gagal', 'message': 'Gagal saat proses unduh.'}

# Fungsi yang dijalankan di thread terpisah untuk mengunduh video
def download_video_thread(url, format_id, task_id, use_unique_name=False):
    if use_unique_name:
        # Jika diminta, tambahkan ID unik pendek ke nama file untuk menghindari penimpaan
        unique_suffix = uuid.uuid4().hex[:8]
        output_path = os.path.join(DOWNLOAD_FOLDER, f'%(title)s-%(id)s-{unique_suffix}.%(ext)s')
    else:
        # Perilaku default, akan menimpa file yang ada jika namanya sama
        output_path = os.path.join(DOWNLOAD_FOLDER, f'%(title)s-%(id)s.%(ext)s')
    
    ydl_opts = {
        'format': f'{format_id}+bestaudio/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
    }
    
    # Kelas kustom untuk menyisipkan task_id ke dalam info_dict
    class CustomYoutubeDL(yt_dlp.YoutubeDL):
        def process_info(self, info_dict):
            info_dict['task_id'] = task_id
            return super().process_info(info_dict)
    
    try:
        with CustomYoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error di thread unduhan [{task_id}]: {e}")
        download_progress[task_id] = {'status': 'gagal', 'message': str(e)}

# Route utama untuk halaman depan
@app.route('/')
def index():
    return render_template('index.html')

# Route untuk mendapatkan informasi video dari URL
@app.route('/info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            seen_resolutions = set()
            unique_formats = []
            # Ambil format video dengan resolusi standar (misal: 1080p, 720p)
            for f in reversed(info.get('formats', [])):
                resolution = f.get('format_note') or f.get('resolution')
                if f.get('vcodec') != 'none' and resolution and isinstance(resolution, str) and resolution.endswith('p') and resolution not in seen_resolutions:
                    unique_formats.append({
                        'id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': resolution,
                        'filesize': f.get('filesize') or f.get('filesize_approx'),
                    })
                    seen_resolutions.add(resolution)
            video_info = {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'formats': list(reversed(unique_formats))
            }
            return jsonify(video_info)
    except Exception as e:
        return jsonify({'error': f'Gagal mendapatkan info video: {str(e)}'}), 500

# Route untuk memulai proses unduhan
@app.route('/download', methods=['POST'])
def start_download():
    url = request.json.get('url')
    format_id = request.json.get('format_id')
    force_download = request.json.get('force', False)
    rename_if_exists = request.json.get('rename', False)

    if not url or not format_id:
        return jsonify({'error': 'URL dan ID Format dibutuhkan'}), 400

    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')

        # Cek apakah file dengan ID video yang sama sudah ada
        existing_file = None
        for f in os.listdir(DOWNLOAD_FOLDER):
            if video_id in f and os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f)):
                existing_file = f
                break

        # Jika file ada dan tidak ada aksi (force/rename) yang diminta, kirim konfirmasi ke klien
        if existing_file and not force_download and not rename_if_exists:
            return jsonify({
                'status': 'exists',
                'filename': existing_file
            })

        # Jika tidak ada file atau ada aksi, mulai unduhan
        task_id = str(uuid.uuid4())
        download_progress[task_id] = {'status': 'memulai', 'percent': 0}
        thread = threading.Thread(target=download_video_thread, args=(url, format_id, task_id, rename_if_exists))
        thread.start()
        return jsonify({'task_id': task_id, 'status': 'started'})

    except Exception as e:
        return jsonify({'error': f'Gagal memulai unduhan: {str(e)}'}), 500

# Route untuk mengirim progres unduhan ke klien (Server-Sent Events)
@app.route('/progress/<task_id>')
def progress(task_id):
    def generate():
        while True:
            if task_id in download_progress:
                progress_data = download_progress[task_id]
                yield f"data: {json.dumps(progress_data)}\n\n"
                # Hentikan stream jika unduhan selesai atau gagal
                if progress_data['status'] in ['selesai', 'gagal']:
                    break
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Task ID tidak ditemukan'})}\n\n"
                break
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

# Route untuk mengunduh file yang sudah selesai dari server
@app.route('/get-file/<filename>')
def get_file(filename):
    try:
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return "File tidak ditemukan atau sudah dihapus.", 404

# Jalankan aplikasi jika file ini dieksekusi secara langsung
if __name__ == '__main__':
    app.run(debug=True, threaded=True)