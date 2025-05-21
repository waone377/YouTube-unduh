import { spawn, exec } from "child_process";
import promptSync from "prompt-sync";
const prompt = promptSync();

function downloadVideo(url, output) {
  const nama = `save/${output}.mp4`;
  console.clear();
  console.log("memproses permintaan..");
  const proses = spawn("yt-dlp", ["-f", "best", "-o", nama, link]);
  proses.stdout.on("data", (data) => {
    console.clear();
    process.stdout.write(data.toString()); // tampilkan progress di terminal
  });

  proses.stderr.on("data", (data) => {
    process.stderr.write(data.toString()); // kalau error
  });

  proses.on("close", (code) => {
    console.clear();
    console.log(`\nProses selesai dengan kode: ${code}`);
    console.log("di simpan di: ", nama);
  });
  proses.on("error", (err) => {
    console.error(`Gagal menjalankan proses: ${err.message}`);
  });
}
console.log("masukkan link url video YouTube yang akan diunduh dibawah..\n");
const link = prompt("masukkan link?: ");
console.log("masukkan nama vidio hasil download di bawah tanpa menyertakan ekstensi format..\n");
const nama = prompt("file name?: ");

downloadVideo(link, nama);
