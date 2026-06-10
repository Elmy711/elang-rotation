import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


def load_proxies(filename="proxies.txt"):
    """Membaca daftar proxy dari file teks."""
    proxies = []
    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    proxies.append({"http": f"http://{line}", "https": f"http://{line}"})
        print(f"[INFO] Berhasil memuat {len(proxies)} proxy.")
    except FileNotFoundError:
        print(f"[ERROR] File '{filename}' tidak ditemukan!")
        print("[INFO] Jalankan tanpa proxy (menggunakan IP lokal)...")
        proxies = [None]
    return proxies


def send_request(worker_id, url, proxy_list, timeout):
    """Fungsi utama worker untuk mengeksekusi request HTTP."""
    selected_proxy = random.choice(proxy_list)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    start_time = time.time()
    try:
        response = requests.get(
            url, headers=headers, proxies=selected_proxy, timeout=timeout
        )
        duration = time.time() - start_time
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
        error_name = type(e).__name__
        return {
            "status_code": 0,
            "duration": duration,
            "proxy_used": proxy_str,
            "error": error_name,
        }


def main():
    print("=====================================================")
    print("       ELANG HTTP TESTER WITH PROXY ROTATION      ")
    print("=====================================================")

    # 1. Input Manual URL Target
    target_url = input(
        "1. Masukkan URL Target (contoh: https://example.com): "
    ).strip()
    if not target_url:
        print("[ERROR] URL tidak boleh kosong!")
        sys.exit(1)

    # 2. Input Manual Concurrency (Threads)
    try:
        concurrency = int(
            input("2. Masukkan Jumlah Threads/Concurrency (contoh: 10): ").strip()
        )
        if concurrency <= 0:
            raise ValueError
    except ValueError:
        print("[ERROR] Jumlah threads harus berupa angka bulat positif!")
        sys.exit(1)

    # 3. Input Manual Total Request
    try:
        total_requests = int(
            input("3. Masukkan Total Requests (contoh: 100): ").strip()
        )
        if total_requests <= 0:
            raise ValueError
    except ValueError:
        print("[ERROR] Total requests harus berupa angka bulat positif!")
        sys.exit(1)

    # 4. Input Manual Timeout (Opsional, Default 5 detik)
    timeout_input = input(
        "4. Masukkan Timeout per request dalam detik [Default: 5]: "
    ).strip()
    timeout = 5 if not timeout_input else int(timeout_input)

    print("=====================================================")

    # Load Daftar Proxy
    proxy_list = load_proxies("proxies.txt")
    if not proxy_list:
        proxy_list = [None]

    print("\n=================== KONFIGURASI =====================")
    print(f"Target URL   : {target_url}")
    print(f"Concurrency  : {concurrency} Threads")
    print(f"Total Req    : {total_requests}")
    print(f"Timeout      : {timeout} detik")
    print("=====================================================")
    print("Memulai pengujian... Tekan Ctrl+C untuk membatalkan.\n")

    success_count = 0
    fail_count = 0
    status_codes = {}
    errors = {}

    start_test_time = time.time()

    # Eksekusi dengan ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_request, i, target_url, proxy_list, timeout)
            for i in range(total_requests)
        ]

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
        print(f"Rata-rata Kecepatan  : {total_requests / total_time:.2f} req/sec")

    if status_codes:
        print("\nDetail Status Code   :")
        for code, count in status_codes.items():
            print(f"  - Status {code} : {count} kali")

    if errors:
        print("\nRincian Error (Proxy Mati / Timeout) :")
        for err_msg, count in errors.items():
            print(f"  - [ {count} kali ] {err_msg}")
    print("=====================================================")


if __name__ == "__main__":
    main()
    
