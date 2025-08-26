# Proyek Pengunduh Video YouTube Interaktif (Revisi 5)

Aplikasi web yang telah ditingkatkan, dibangun dengan Flask dan `yt-dlp`, untuk mengunduh video dari YouTube. Versi ini menambahkan opsi untuk membuat file baru dengan nama unik jika video sudah pernah diunduh.

## Fitur Unggulan

-   **Antarmuka Interaktif**: Proses multi-langkah yang dipandu oleh JavaScript untuk pengalaman pengguna yang lebih baik.
-   **Pemilihan Format yang Disaring**: Pengguna dapat melihat dan memilih dari semua format resolusi video standar (misal: 1080p, 720p, dll.) yang tersedia.
-   **Pengecekan File Duplikat**: Memberi tahu pengguna jika video sudah pernah diunduh dan memberikan opsi untuk menggunakan file yang ada, menimpa, atau mengunduh sebagai file baru dengan nama unik.
-   **Progres Real-time**: Melacak status unduhan secara langsung di browser menggunakan Server-Sent Events (SSE), lengkap dengan progress bar, kecepatan unduh, dan estimasi waktu selesai (ETA).
-   **Manajemen File**: Unduhan disimpan sementara di server dan tautan unduhan disediakan setelah selesai. File lama akan otomatis dibersihkan setelah 1 jam.
-   **Asinkron**: Proses unduhan berjalan di *background thread*, sehingga tidak memblokir antarmuka pengguna.

## Prasyarat

-   Python 3.6+
-   `pip` (manajer paket Python)
-   `ffmpeg`: Diperlukan oleh `yt-dlp` untuk menggabungkan video dan audio. Unduh dari [situs resmi ffmpeg](https://ffmpeg.org/download.html) dan pastikan path-nya terdaftar di variabel lingkungan sistem Anda.

## Instalasi

1.  **Buat Proyek**
    Buat folder proyek `yt-unduh5` dan semua file yang ada di dalam struktur ini.

2.  **Buat Lingkungan Virtual (Sangat Disarankan)**
    ```bash
    cd yt-unduh5
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Instal Dependensi**
    ```bash
    pip install -r requirements.txt
    ```

## Menjalankan Aplikasi

Jalankan server Flask dengan perintah:
```bash
python src/app.py
```
Aplikasi akan berjalan di `http://127.0.0.1:5000`.

## Cara Menggunakan

1.  Buka browser dan kunjungi `http://127.0.0.1:5000`.
2.  Tempelkan URL video YouTube ke dalam kolom input dan klik "Dapatkan Info Video".
3.  Pilih format resolusi yang Anda inginkan dengan mengklik tombol "Unduh".
4.  Jika file sudah ada, Anda akan diberi pilihan untuk menggunakan file tersebut, mengunduh ulang (menimpa), atau mengunduh sebagai file baru dengan nama unik.
5.  Proses unduhan akan dimulai di server, dan Anda akan melihat progress bar secara real-time.
6.  Setelah selesai, sebuah tautan akan muncul. Klik tautan tersebut untuk mengunduh file video ke komputer Anda.

---

## Dokumentasi API Server

Aplikasi ini menggunakan beberapa endpoint untuk menciptakan pengalaman interaktif.

### 1. Dapatkan Info Video

-   **Endpoint**: `/info`
-   **Metode**: `POST`
-   **Deskripsi**: Mengambil metadata video tanpa mengunduhnya.
-   **Field Request (JSON Body)**:
    -   `url` (string, wajib): URL video YouTube.
-   **Field Respon Sukses (200 OK)**:
    ```json
    {
      "title": "Judul Video",
      "thumbnail": "https://url.to/thumbnail.jpg",
      "duration": "10:35",
      "formats": [
        {
          "id": "137",
          "ext": "mp4",
          "resolution": "1080p",
          "filesize": 152428800
        }
      ]
    }
    ```

### 2. Mulai Unduhan

-   **Endpoint**: `/download`
-   **Metode**: `POST`
-   **Deskripsi**: Memeriksa apakah file sudah ada, atau memulai proses unduhan di background thread.
-   **Field Request (JSON Body)**:
    -   `url` (string, wajib): URL video YouTube.
    -   `format_id` (string, wajib): ID format yang dipilih dari endpoint `/info`.
    -   `force` (boolean, opsional): Jika `true`, akan mengunduh ulang dan menimpa file yang sudah ada. Defaultnya `false`.
    -   `rename` (boolean, opsional): Jika `true`, akan mengunduh video dengan nama file yang unik jika file dengan nama standar sudah ada. Defaultnya `false`.
-   **Field Respon Sukses (200 OK)**:
    -   Jika unduhan dimulai:
    ```json
    {
      "task_id": "unique-uuid-for-the-task",
      "status": "started"
    }
    ```
    -   Jika file sudah ada:
    ```json
    {
        "status": "exists",
        "filename": "nama-file-yang-ada.mp4"
    }
    ```

### 3. Lacak Progres Unduhan

-   **Endpoint**: `/progress/<task_id>`
-   **Metode**: `GET`
-   **Deskripsi**: Endpoint Server-Sent Events (SSE) yang mengirimkan update status unduhan.
-   **Field Respon (text/event-stream)**:
    Serangkaian event JSON yang dikirim ke klien, contoh:
    ```
    data: {"status": "mengunduh", "percent": 15.7, "eta": 120, "speed": "1.25MiB/s"}

    data: {"status": "selesai", "percent": 100, "filename": "Judul Video-video-id.mp4"}
    ```

### 4. Ambil File Selesai

-   **Endpoint**: `/get-file/<filename>`
-   **Metode**: `GET`
-   **Deskripsi**: Mengirim file video yang telah selesai diunduh ke klien.
-   **Field Respon Sukses (200 OK)**:
    -   **Tipe Konten**: `video/mp4`
    -   **Body**: Data biner dari file video.