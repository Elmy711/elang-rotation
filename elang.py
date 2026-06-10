import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# --- KONFIGURASI PENGUJIAN ---
TARGET_URL = "https://example.com"
TOTAL_REQUESTS = 100
CONCURRENCY = 10  # Jumlah Threads / Workers Pool
TIMEOUT = 5  # Timeout per request dalam detik


def load_proxies(filename="proxies.txt"):
    """Membaca daftar proxy dari file teks."""
    proxies = []
    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    # Format standar http://IP:PORT
                    proxies.append({"http": f"http://{line}", "https": f"http://{line}"})
        print(f"[INFO] Berhasil memuat {len(proxies)} proxy.")
    except FileNotFoundError:
        print(f"[ERROR] File '{filename}' tidak ditemukan!")
        print("[INFO] Jalankan tanpa proxy (menggunakan IP lokal)...")
        proxies = [None]  # Tetap jalan tanpa proxy jika file tidak ada
    return proxies


def send_request(worker_id, url, proxy_list):
    """Fungsi utama worker untuk mengeksekusi request HTTP."""
    # Ambil proxy secara acak dari daftar untuk rotasi IP
    selected_proxy = random.choice(proxy_list)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    start_time = time.time()
    try:
        # Eksekusi HTTP GET
        response = requests.get(
            url, headers=headers, proxies=selected_proxy, timeout=TIMEOUT
        )
        duration = time.time() - start_time

        # Tampilkan status proxy yang digunakan di log debug
        proxy_str = (
            selected_proxy["http"] if selected_proxy else "IP Lokal / Tanpa Proxy"
        )

        return {
            "status_code": response.status_code,
            "duration": duration,
            "proxy_used": proxy_str,
            "error": None,
        }

    except requests.RequestException as e:
        duration = time.time() - start_time
        proxy_str = (
            selected_proxy["http"] if selected_proxy else "IP Lokal / Tanpa Proxy"
        )
        # Menangkap error timeout, koneksi diputus, atau proxy mati
        error_name = type(e).__name__
        return {
            "status_code": 0,
            "duration": duration,
            "proxy_used": proxy_str,
            "error": error_name,
        }


def main():
    print("=====================================================")
    print("             HTTP TESTER PROXY ROTATION             ")
    print("=====================================================")
    print(f"Target URL   : {TARGET_URL}")
    print(f"Concurrency  : {CONCURRENCY} Threads")
    print(f"Total Req    : {TOTAL_REQUESTS}")
    print("=====================================================")

    # 1. Load Daftar Proxy
    proxy_list = load_proxies("proxies.txt")
    if not proxy_list:
        print("[WARNING] Daftar proxy kosong! Menggunakan IP lokal.")
        proxy_list = [None]

    success_count = 0
    fail_count = 0
    status_codes = {}
    errors = {}

    start_test_time = time.time()

    # 2. Inisialisasi ThreadPoolExecutor (Workers Pool di Python)
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        # Kirim seluruh tugas ke antrean executor
        futures = [
            executor.submit(send_request, i, TARGET_URL, proxy_list)
            for i in range(TOTAL_REQUESTS)
        ]

        # Ambil hasil dari setiap thread secara real-time saat selesai
        for future in as_completed(futures):
            res = future.result()

            if res["error"]:
                fail_count += 1
                errors[res["error"]] = errors.get(res["error"], 0) + 1
                print(
                    f"[DEBUG] Proxy: {res['proxy_used']} -> GAGAL ({res['error']}) [{res['duration']:.2f}s]"
                )
            else:
                success_count += 1
                status_codes[res["status_code"]] = (
                    status_codes.get(res["status_code"], 0) + 1
                )
                print(
                    f"[DEBUG] Proxy: {res['proxy_used']} -> SUKSES ({res['status_code']}) [{res['duration']:.2f}s]"
                )

    total_time = time.time() - start_test_time

    # --- OUTPUT LAPORAN AKHIR ---
    print("\n==================== HASIL AKHIR ====================")
    print(f"Total Waktu Berjalan : {total_time:.2f} detik")
    print(f"Requests Sukses      : {success_count}")
    print(f"Requests Gagal       : {fail_count}")
    if total_time > 0:
        print(f"Rata-rata Kecepatan  : {TOTAL_REQUESTS / total_time:.2f} req/sec")

    if statusCodes := status_codes:
        print("\nDetail Status Code   :")
        for code, count in statusCodes.items():
            print(f"  - Status {code} : {count} kali")

    if errorLog := errors:
        print("\nRincian Error (Proxy Mati / Timeout) :")
        for err_msg, count in errorLog.items():
            print(f"  - [ {count} kali ] {err_msg}")
    print("=====================================================")


if __name__ == "__main__":
    main()

