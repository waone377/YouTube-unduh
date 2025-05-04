import { spawn, exec } from "child_process";
import promptSync from "prompt-sync";
const prompt = promptSync();

function downloadVideo(url, output) {
  const nama = `data/${output}.mp4`;
  const proses = spawn("yt-dlp", ["-f", "best", "-o", nama, link]);

  proses.stdout.on("data", (data) => {
    process.stdout.write(data.toString()); // tampilkan progress di terminal
  });

  proses.stderr.on("data", (data) => {
    process.stderr.write(data.toString()); // kalau error
  });

  proses.on("close", (code) => {
    console.log(`\nProses selesai dengan kode: ${code}`);
  });
  proses.on("error", (err) => {
    console.error(`Gagal menjalankan proses: ${err.message}`);
  });
}

// Contoh penggunaan
const link = prompt("masukkan link video YouTube: ");
const nama = prompt("masukkan nama output tanpa ekstensi: ");

downloadVideo(link, nama);

