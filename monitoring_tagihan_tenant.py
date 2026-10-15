"""
Sistem Monitoring Tagihan Tenant
================================

Aplikasi berbasis terminal untuk membantu pengelola mal atau gedung komersial
mencatat tenant beserta tagihannya (sewa, service charge, listrik, dan lainnya),
lalu memantau tagihan mana yang sudah dan belum dibayar.

Untuk siapa:
    Staf administrasi / finance di building management yang mengelola banyak
    tenant dan perlu tahu dengan cepat siapa yang masih menunggak, tanpa harus
    merekap spreadsheet secara manual.

Fitur utama:
    1. Lihat data   - daftar semua tenant + ringkasan tagihan (total, persentase
                      lunas, tunggakan terbesar, tunggakan per kategori),
                      detail satu tenant beserta seluruh invoicenya, atau
                      export laporan tagihan ke CSV (bisa dibuka di Excel).
    2. Tambah data  - daftarkan tenant baru beserta tagihan pertamanya.
    3. Ubah data    - ubah data tenant, tambah invoice, atau ubah status bayar.
    4. Hapus data   - hapus tenant ke Recycle Bin (masih bisa dipulihkan),
                      atau hapus permanen.

    Semua perubahan otomatis tersimpan ke file data_tagihan.csv dan dibaca
    kembali saat program dibuka, jadi data tidak hilang.

Validasi yang dijaga:
    - Tenant ID unik dengan format T + 3 angka (contoh: T001).
    - Satu unit hanya boleh ditempati satu tenant.
    - Nomor invoice unik di seluruh tenant.
    - Periode tagihan harus tanggal yang benar-benar ada (DD-MM-YYYY).
    - Jumlah tagihan harus angka lebih dari 0.

Cara menjalankan:
    python3 monitoring_tagihan_tenant.py

File yang dihasilkan:
    data_tagihan.csv  - penyimpanan data (dibuat otomatis dari data contoh saat
                        pertama kali program dijalankan). Satu baris = satu invoice.
    laporan/          - folder hasil export laporan tagihan.

Dibuat oleh: Raihan Hasbi
"""

import csv
import os
from datetime import datetime


# ==========================================================
# LOKASI FILE
# ==========================================================
# File disimpan di folder yang sama dengan program ini
FOLDER_PROGRAM = os.path.dirname(os.path.abspath(__file__))
FILE_DATA = os.path.join(FOLDER_PROGRAM, 'data_tagihan.csv')
FOLDER_LAPORAN = os.path.join(FOLDER_PROGRAM, 'laporan')

# Urutan kolom di file CSV. Satu baris = satu invoice.
KOLOM_CSV = ['tenant_id', 'nama_tenant', 'unit', 'kategori',
             'no_invoice', 'jenis', 'periode', 'jumlah', 'status',
             'status_tenant', 'dihapus_pada']


# ==========================================================
# DATA
# ==========================================================
# Key luar = Tenant ID (unik). Setiap tenant menyimpan list invoice di 'tagihan'.
# Isi di bawah adalah data contoh, dipakai saat data_tagihan.csv belum ada.
data_tenant = {
    'T001': {
        'nama_tenant': 'Kopi Sudut',
        'unit': 'GF-12',
        'kategori': 'F&B',
        'tagihan': [
            {'no_invoice': 'INV001', 'jenis': 'Sewa', 'periode': '01-09-2026', 'jumlah': 15000000, 'status': 'Lunas'},
            {'no_invoice': 'INV002', 'jenis': 'Service Charge', 'periode': '01-09-2026', 'jumlah': 2500000, 'status': 'Belum Lunas'}
        ]
    },
    'T002': {
        'nama_tenant': 'Roti Pagi',
        'unit': 'LG-05',
        'kategori': 'F&B',
        'tagihan': [
            {'no_invoice': 'INV003', 'jenis': 'Sewa', 'periode': '01-09-2026', 'jumlah': 12000000, 'status': 'Belum Lunas'}
        ]
    },
    'T003': {
        'nama_tenant': 'Mode Kita',
        'unit': 'UG-21',
        'kategori': 'Fashion',
        'tagihan': [
            {'no_invoice': 'INV004', 'jenis': 'Sewa', 'periode': '01-09-2026', 'jumlah': 20000000, 'status': 'Lunas'},
            {'no_invoice': 'INV005', 'jenis': 'Listrik', 'periode': '01-09-2026', 'jumlah': 3200000, 'status': 'Belum Lunas'}
        ]
    }
}

# Tenant yang dihapus disimpan di sini dulu supaya masih bisa dipulihkan.
# Format: {tenant_id: {'data': {...data tenant...}, 'dihapus_pada': 'DD-MM-YYYY HH:MM'}}
recycle_bin = {}

# Kolom yang boleh diubah (tenant_id tidak, karena primary key)
kolom_update = ['nama_tenant', 'unit', 'kategori', 'tagihan']

# Pilihan baku supaya penulisan selalu seragam
daftar_kategori = ['F&B', 'Fashion', 'Entertainment', 'Elektronik', 'Lainnya']
daftar_jenis_tagihan = ['Sewa', 'Service Charge', 'Listrik', 'Air', 'Lainnya']


# ==========================================================
# FUNCTION BANTUAN: VALIDASI INPUT
# ==========================================================
def hanya_spasi(teks):
    # True kalau teks kosong atau isinya spasi semua
    for karakter in teks:
        if karakter != ' ':
            return False
    return True


def input_tidak_kosong(pesan):
    # Minta input sampai tidak kosong (spasi saja juga dianggap kosong)
    teks = input(pesan)
    while hanya_spasi(teks):
        print('Input tidak boleh kosong.')
        teks = input(pesan)
    return teks


def semua_angka(teks):
    # True kalau teks tidak kosong dan semua karakternya angka 0-9
    if teks == '':
        return False
    for karakter in teks:
        if karakter not in '0123456789':
            return False
    return True


def input_angka(pesan):
    # Minta input sampai berupa angka lebih dari 0
    teks = input(pesan)
    while not semua_angka(teks) or int(teks) <= 0:
        print('Input harus berupa angka lebih dari 0.')
        teks = input(pesan)
    return int(teks)


def input_ya_tidak(pesan):
    # Minta input sampai dijawab y atau n
    jawaban = input(pesan).lower()
    while jawaban != 'y' and jawaban != 'n':
        print('Jawab dengan y atau n.')
        jawaban = input(pesan).lower()
    return jawaban


def input_status():
    # Pilih status pakai angka supaya tulisannya seragam
    pilihan = input('Status (1. Belum Lunas / 2. Lunas): ')
    while pilihan != '1' and pilihan != '2':
        print('Pilih 1 atau 2.')
        pilihan = input('Status (1. Belum Lunas / 2. Lunas): ')
    if pilihan == '1':
        return 'Belum Lunas'
    else:
        return 'Lunas'


def input_pilihan(judul, daftar):
    # Tampilkan daftar bernomor, user pilih angka, kembalikan isi yang dipilih.
    # Dipakai untuk kategori tenant dan jenis tagihan.
    print(judul)
    for i in range(len(daftar)):
        print('  {}. {}'.format(i + 1, daftar[i]))
    pesan = 'Pilih (1-{}): '.format(len(daftar))
    pilihan = input(pesan)
    while not semua_angka(pilihan) or int(pilihan) < 1 or int(pilihan) > len(daftar):
        print('Pilih angka 1 sampai {}.'.format(len(daftar)))
        pilihan = input(pesan)
    return daftar[int(pilihan) - 1]


# ==========================================================
# VALIDASI FORMAT: TENANT ID DAN PERIODE
# ==========================================================
def format_tenant_id_benar(tenant_id):
    # Format benar: T + 3 angka, contoh T001
    if len(tenant_id) != 4:
        return False
    if tenant_id[0] != 'T':
        return False
    if not semua_angka(tenant_id[1:]):
        return False
    return True


def input_tenant_id(pesan):
    # Minta Tenant ID sampai formatnya benar
    tenant_id = input(pesan).upper()
    while not format_tenant_id_benar(tenant_id):
        print('Format Tenant ID salah. Harus huruf T + 3 angka, contoh T004.')
        tenant_id = input(pesan).upper()
    return tenant_id


def format_periode_benar(periode):
    # Format benar: DD-MM-YYYY dan tanggalnya ada di kalender
    if len(periode) != 10:
        return False
    if periode[2] != '-' or periode[5] != '-':
        return False
    hari = periode[:2]
    bulan = periode[3:5]
    tahun = periode[6:]
    if not semua_angka(hari) or not semua_angka(bulan) or not semua_angka(tahun):
        return False
    if int(bulan) < 1 or int(bulan) > 12:
        return False
    if int(tahun) < 2000 or int(tahun) > 2100:
        return False

    # Jumlah hari tiap bulan (index 0 = Januari). Tahun kabisat: Februari 29 hari.
    hari_per_bulan = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if int(tahun) % 4 == 0 and (int(tahun) % 100 != 0 or int(tahun) % 400 == 0):
        hari_per_bulan[1] = 29
    if int(hari) < 1 or int(hari) > hari_per_bulan[int(bulan) - 1]:
        return False
    return True


def input_periode():
    # Minta periode sampai formatnya benar
    periode = input('Periode (DD-MM-YYYY, contoh 01-09-2026): ')
    while not format_periode_benar(periode):
        print('Format periode salah. Contoh yang benar: 01-09-2026, dan tanggalnya harus ada di kalender.')
        periode = input('Periode (DD-MM-YYYY, contoh 01-09-2026): ')
    return periode


# ==========================================================
# FUNCTION BANTUAN: TAGIHAN
# ==========================================================
def format_rupiah(nominal):
    # 15000000 -> 'Rp 15.000.000'
    return 'Rp ' + '{:,}'.format(nominal).replace(',', '.')


def cek_no_invoice(no_invoice):
    # True kalau nomor invoice sudah dipakai, termasuk oleh tenant di Recycle Bin
    # (supaya tidak bentrok saat tenant itu dipulihkan)
    for tenant in data_tenant.values():
        for tagihan in tenant['tagihan']:
            if tagihan['no_invoice'] == no_invoice:
                return True
    for item in recycle_bin.values():
        for tagihan in item['data']['tagihan']:
            if tagihan['no_invoice'] == no_invoice:
                return True
    return False


def hitung_belum_lunas(daftar_tagihan):
    # Jumlah semua tagihan yang statusnya Belum Lunas
    total = 0
    for tagihan in daftar_tagihan:
        if tagihan['status'] == 'Belum Lunas':
            total += tagihan['jumlah']
    return total


def input_tagihan_baru():
    # Minta data 1 invoice, kembalikan sebagai dictionary (belum disimpan)
    no_invoice = input_tidak_kosong('No Invoice: ').upper()
    while cek_no_invoice(no_invoice):
        print('No Invoice sudah dipakai.')
        no_invoice = input_tidak_kosong('No Invoice: ').upper()
    jenis = input_pilihan('Jenis tagihan:', daftar_jenis_tagihan)
    periode = input_periode()
    jumlah = input_angka('Jumlah tagihan (Rp): ')
    status = input_status()
    return {'no_invoice': no_invoice, 'jenis': jenis, 'periode': periode, 'jumlah': jumlah, 'status': status}


# ==========================================================
# VALIDASI UNIT: SATU UNIT UNTUK SATU TENANT
# ==========================================================
def cari_pemilik_unit(unit):
    # Tenant ID yang menempati unit itu, atau '' kalau unit kosong
    for tenant_id in data_tenant:
        if data_tenant[tenant_id]['unit'] == unit:
            return tenant_id
    return ''


def input_unit(pesan, tenant_id_sendiri):
    # Minta unit sampai tidak dipakai tenant lain (unit milik sendiri boleh)
    unit = input_tidak_kosong(pesan).upper()
    pemilik = cari_pemilik_unit(unit)
    while pemilik != '' and pemilik != tenant_id_sendiri:
        print('Unit {} sudah ditempati {} ({}).'.format(
            unit, data_tenant[pemilik]['nama_tenant'], pemilik))
        unit = input_tidak_kosong(pesan).upper()
        pemilik = cari_pemilik_unit(unit)
    return unit


# ==========================================================
# TAMPILAN
# ==========================================================
def tampil_semua_tenant():
    print('\nDaftar Tenant')
    print('{:<6} {:<20} {:<7} {:<14} {:>7} {:>18}'.format(
        'ID', 'Nama Tenant', 'Unit', 'Kategori', 'Invoice', 'Belum Lunas'))
    print('-' * 77)
    for tenant_id, tenant in data_tenant.items():
        print('{:<6} {:<20} {:<7} {:<14} {:>7} {:>18}'.format(
            tenant_id,
            tenant['nama_tenant'],
            tenant['unit'],
            tenant['kategori'],
            len(tenant['tagihan']),
            format_rupiah(hitung_belum_lunas(tenant['tagihan']))
        ))


def tampil_detail(tenant_id, tenant):
    # Tampilkan 1 tenant beserta semua invoicenya
    print('\nTenant ID   : {}'.format(tenant_id))
    print('Nama Tenant : {}'.format(tenant['nama_tenant']))
    print('Unit        : {}'.format(tenant['unit']))
    print('Kategori    : {}'.format(tenant['kategori']))
    print('Daftar Tagihan:')
    if len(tenant['tagihan']) == 0:
        print('  (belum ada tagihan)')
    else:
        print('  {:<8} {:<16} {:<11} {:>16}  {}'.format('Invoice', 'Jenis', 'Periode', 'Jumlah', 'Status'))
        for tagihan in tenant['tagihan']:
            print('  {:<8} {:<16} {:<11} {:>16}  {}'.format(
                tagihan['no_invoice'],
                tagihan['jenis'],
                tagihan['periode'],
                format_rupiah(tagihan['jumlah']),
                tagihan['status']
            ))
    print('Total Belum Lunas: {}'.format(format_rupiah(hitung_belum_lunas(tenant['tagihan']))))


def tampil_detail_tenant(tenant_id):
    # Tampilkan detail tenant yang masih aktif
    tampil_detail(tenant_id, data_tenant[tenant_id])


def tampil_tidak_ada(tenant_id, pesan):
    # Pesan "tidak ada", plus petunjuk kalau tenant itu ternyata ada di Recycle Bin
    print(pesan)
    if tenant_id in recycle_bin:
        print('Catatan: tenant {} ada di Recycle Bin. Pulihkan lewat menu 4 (Hapus & Recycle Bin).'.format(tenant_id))


def tampil_statistik():
    # Ringkasan untuk pengelola: total tagihan, persentase lunas, tunggakan terbesar, per kategori
    jumlah_invoice = 0
    total_tagihan = 0
    total_lunas = 0
    tunggakan_terbesar = 0
    tenant_terbesar = ''
    per_kategori = {}

    for tenant_id, tenant in data_tenant.items():
        belum_lunas_tenant = hitung_belum_lunas(tenant['tagihan'])

        # Cari tenant dengan tunggakan terbesar
        if belum_lunas_tenant > tunggakan_terbesar:
            tunggakan_terbesar = belum_lunas_tenant
            tenant_terbesar = tenant_id

        # Total tunggakan per kategori
        kategori = tenant['kategori']
        if kategori not in per_kategori:
            per_kategori[kategori] = 0
        per_kategori[kategori] += belum_lunas_tenant

        for tagihan in tenant['tagihan']:
            jumlah_invoice += 1
            total_tagihan += tagihan['jumlah']
            if tagihan['status'] == 'Lunas':
                total_lunas += tagihan['jumlah']

    total_belum_lunas = total_tagihan - total_lunas

    print('\n--- Ringkasan ---')
    print('Jumlah tenant       : {}'.format(len(data_tenant)))
    print('Jumlah invoice      : {}'.format(jumlah_invoice))
    print('Total tagihan       : {}'.format(format_rupiah(total_tagihan)))

    if total_tagihan > 0:   # hindari pembagian dengan 0
        persen_lunas = total_lunas * 100 // total_tagihan
        print('Sudah lunas         : {} ({}%)'.format(format_rupiah(total_lunas), persen_lunas))
        print('Belum lunas         : {} ({}%)'.format(format_rupiah(total_belum_lunas), 100 - persen_lunas))

    if tenant_terbesar == '':
        print('Tunggakan terbesar  : tidak ada, semua sudah lunas')
    else:
        print('Tunggakan terbesar  : {} ({}) - {}'.format(
            data_tenant[tenant_terbesar]['nama_tenant'], tenant_terbesar, format_rupiah(tunggakan_terbesar)))

    print('Tunggakan per kategori:')
    for kategori, total in per_kategori.items():
        print('  {:<14} {}'.format(kategori, format_rupiah(total)))

    if len(recycle_bin) > 0:
        print('(Tidak termasuk {} tenant di Recycle Bin)'.format(len(recycle_bin)))


def tampil_recycle_bin():
    if len(recycle_bin) == 0:
        print('Recycle Bin kosong.')
        return
    print('\nIsi Recycle Bin')
    print('{:<6} {:<20} {:<7} {:<17} {:>18}'.format('ID', 'Nama Tenant', 'Unit', 'Dihapus pada', 'Belum Lunas'))
    print('-' * 72)
    for tenant_id, item in recycle_bin.items():
        tenant = item['data']
        print('{:<6} {:<20} {:<7} {:<17} {:>18}'.format(
            tenant_id,
            tenant['nama_tenant'],
            tenant['unit'],
            item['dihapus_pada'],
            format_rupiah(hitung_belum_lunas(tenant['tagihan']))
        ))


# ==========================================================
# PENYIMPANAN DATA (CSV)
# ==========================================================
def baris_csv(tenant_id, tenant, status_tenant, dihapus_pada):
    # Ubah 1 tenant jadi beberapa baris CSV (satu baris per invoice)
    baris = []
    for tagihan in tenant['tagihan']:
        baris.append({
            'tenant_id': tenant_id,
            'nama_tenant': tenant['nama_tenant'],
            'unit': tenant['unit'],
            'kategori': tenant['kategori'],
            'no_invoice': tagihan['no_invoice'],
            'jenis': tagihan['jenis'],
            'periode': tagihan['periode'],
            'jumlah': tagihan['jumlah'],
            'status': tagihan['status'],
            'status_tenant': status_tenant,
            'dihapus_pada': dihapus_pada
        })
    if len(baris) == 0:
        # Tenant tanpa invoice tetap disimpan (kolom invoice dikosongkan)
        baris.append({
            'tenant_id': tenant_id, 'nama_tenant': tenant['nama_tenant'],
            'unit': tenant['unit'], 'kategori': tenant['kategori'],
            'no_invoice': '', 'jenis': '', 'periode': '', 'jumlah': '', 'status': '',
            'status_tenant': status_tenant, 'dihapus_pada': dihapus_pada
        })
    return baris


def simpan_data():
    # Tulis semua tenant aktif dan isi Recycle Bin ke data_tagihan.csv
    semua_baris = []
    for tenant_id, tenant in data_tenant.items():
        semua_baris += baris_csv(tenant_id, tenant, 'Aktif', '')
    for tenant_id, item in recycle_bin.items():
        semua_baris += baris_csv(tenant_id, item['data'], 'Dihapus', item['dihapus_pada'])

    with open(FILE_DATA, 'w', newline='', encoding='utf-8') as file:
        penulis = csv.DictWriter(file, fieldnames=KOLOM_CSV)
        penulis.writeheader()
        penulis.writerows(semua_baris)


def muat_data():
    # Baca data_tagihan.csv saat program dibuka.
    # Kalau file belum ada, buat dari data contoh.
    if not os.path.exists(FILE_DATA):
        simpan_data()
        print('File data belum ada. Dibuat dari data contoh: {}'.format(os.path.basename(FILE_DATA)))
        return

    try:
        aktif = {}
        dihapus = {}
        with open(FILE_DATA, newline='', encoding='utf-8') as file:
            for baris in csv.DictReader(file):
                tenant_id = baris['tenant_id']
                if baris['status_tenant'] == 'Dihapus':
                    if tenant_id not in dihapus:
                        dihapus[tenant_id] = {
                            'data': {'nama_tenant': baris['nama_tenant'], 'unit': baris['unit'],
                                     'kategori': baris['kategori'], 'tagihan': []},
                            'dihapus_pada': baris['dihapus_pada']
                        }
                    tenant = dihapus[tenant_id]['data']
                else:
                    if tenant_id not in aktif:
                        aktif[tenant_id] = {'nama_tenant': baris['nama_tenant'], 'unit': baris['unit'],
                                            'kategori': baris['kategori'], 'tagihan': []}
                    tenant = aktif[tenant_id]

                if baris['no_invoice'] != '':
                    tenant['tagihan'].append({
                        'no_invoice': baris['no_invoice'],
                        'jenis': baris['jenis'],
                        'periode': baris['periode'],
                        'jumlah': int(baris['jumlah']),
                        'status': baris['status']
                    })
    except (KeyError, ValueError, TypeError, csv.Error):
        # File rusak: jangan crash. Cadangkan file lama, lalu pakai data contoh.
        cadangan = FILE_DATA.replace('.csv', '_rusak.csv')
        os.replace(FILE_DATA, cadangan)
        simpan_data()
        print('PERINGATAN: {} tidak bisa dibaca. File lama dicadangkan sebagai {}, '
              'program memakai data contoh.'.format(os.path.basename(FILE_DATA), os.path.basename(cadangan)))
        return

    data_tenant.clear()
    data_tenant.update(aktif)
    recycle_bin.clear()
    recycle_bin.update(dihapus)
    print('Data dimuat dari {} ({} tenant aktif, {} di Recycle Bin).'.format(
        os.path.basename(FILE_DATA), len(data_tenant), len(recycle_bin)))


def export_laporan():
    # Export tagihan tenant aktif ke CSV yang bisa dibuka di Excel
    if len(data_tenant) == 0:
        print('Data tidak ada')
        return

    print('1. Semua tagihan')
    print('2. Hanya tagihan Belum Lunas')
    jenis_laporan = input('Pilih (1-2): ')
    while jenis_laporan != '1' and jenis_laporan != '2':
        print('Pilih 1 atau 2.')
        jenis_laporan = input('Pilih (1-2): ')

    baris_laporan = []
    total = 0
    for tenant_id, tenant in data_tenant.items():
        for baris in baris_csv(tenant_id, tenant, 'Aktif', ''):
            if baris['no_invoice'] == '':
                continue
            if jenis_laporan == '2' and baris['status'] != 'Belum Lunas':
                continue
            del baris['status_tenant']
            del baris['dihapus_pada']
            baris_laporan.append(baris)
            total += baris['jumlah']

    if len(baris_laporan) == 0:
        print('Tidak ada tagihan yang sesuai. Laporan tidak dibuat.')
        return

    nama_jenis = 'semua' if jenis_laporan == '1' else 'belum_lunas'
    tanggal = datetime.now().strftime('%Y-%m-%d')
    os.makedirs(FOLDER_LAPORAN, exist_ok=True)
    nama_file = os.path.join(FOLDER_LAPORAN, 'laporan_tagihan_{}_{}.csv'.format(nama_jenis, tanggal))

    # utf-8-sig supaya Excel membaca hurufnya dengan benar
    with open(nama_file, 'w', newline='', encoding='utf-8-sig') as file:
        penulis = csv.DictWriter(file, fieldnames=KOLOM_CSV[:9])
        penulis.writeheader()
        penulis.writerows(baris_laporan)

    print('Laporan berhasil dibuat: laporan/{}'.format(os.path.basename(nama_file)))
    print('Isi: {} tagihan, total {}'.format(len(baris_laporan), format_rupiah(total)))


# ==========================================================
# MENU READ
# ==========================================================
def menu_read():
    while True:
        print('\n=== Menu Tampilkan Data ===')
        print('1. Tampilkan semua tenant')
        print('2. Tampilkan tagihan berdasarkan Tenant ID')
        print('3. Export laporan tagihan ke CSV (Excel)')
        print('4. Kembali ke menu utama')
        pilihan = input('Pilih menu (1-4): ')

        if pilihan == '1':
            if len(data_tenant) == 0:
                print('Data tidak ada')
            else:
                tampil_semua_tenant()
                tampil_statistik()
        elif pilihan == '2':
            if len(data_tenant) == 0:
                print('Data tidak ada')
            else:
                tenant_id = input_tenant_id('Masukkan Tenant ID: ')
                if tenant_id in data_tenant:
                    tampil_detail_tenant(tenant_id)
                else:
                    tampil_tidak_ada(tenant_id, 'Data tidak ada')
        elif pilihan == '3':
            export_laporan()
        elif pilihan == '4':
            break
        else:
            print('Pilihan yang Anda masukkan tidak valid')


# ==========================================================
# MENU CREATE
# ==========================================================
def menu_create():
    while True:
        print('\n=== Menu Tambah Data ===')
        print('1. Tambah tenant baru')
        print('2. Kembali ke menu utama')
        pilihan = input('Pilih menu (1-2): ')

        if pilihan == '1':
            tenant_id = input_tenant_id('Masukkan Tenant ID (contoh T004): ')
            if tenant_id in data_tenant:
                print('Data sudah ada')
            elif tenant_id in recycle_bin:
                print('Tenant ID {} masih ada di Recycle Bin. Pulihkan atau hapus permanen terlebih dahulu.'.format(tenant_id))
            else:
                nama_tenant = input_tidak_kosong('Nama Tenant: ')
                unit = input_unit('Unit: ', tenant_id)
                kategori = input_pilihan('Kategori:', daftar_kategori)
                print('Isi tagihan pertama untuk tenant ini')
                tagihan_baru = input_tagihan_baru()

                simpan = input_ya_tidak('Simpan data? (y/n): ')
                if simpan == 'y':
                    data_tenant[tenant_id] = {
                        'nama_tenant': nama_tenant,
                        'unit': unit,
                        'kategori': kategori,
                        'tagihan': [tagihan_baru]
                    }
                    simpan_data()
                    print('Data berhasil disimpan')
                else:
                    print('Data batal disimpan')
        elif pilihan == '2':
            break
        else:
            print('Pilihan yang Anda masukkan tidak valid')


# ==========================================================
# MENU UPDATE
# ==========================================================
def menu_update():
    while True:
        print('\n=== Menu Ubah Data ===')
        print('1. Ubah data tenant')
        print('2. Kembali ke menu utama')
        pilihan = input('Pilih menu (1-2): ')

        if pilihan == '1':
            tenant_id = input_tenant_id('Masukkan Tenant ID: ')
            if tenant_id not in data_tenant:
                tampil_tidak_ada(tenant_id, 'Data yang Anda cari tidak ada')
            else:
                tampil_detail_tenant(tenant_id)
                lanjut = input_ya_tidak('Lanjut ubah data? (y/n): ')
                if lanjut == 'y':
                    # User memasukkan nama kolom yang mau diubah
                    print('Kolom yang bisa diubah: {}'.format(', '.join(kolom_update)))
                    kolom = input('Masukkan nama kolom: ').lower()
                    while kolom not in kolom_update:
                        print('Kolom tidak ada atau tidak boleh diubah.')
                        kolom = input('Masukkan nama kolom: ').lower()

                    # User memasukkan nilai baru (belum disimpan dulu)
                    daftar_tagihan = data_tenant[tenant_id]['tagihan']
                    aksi = ''
                    if kolom == 'unit':
                        nilai_baru = input_unit('Masukkan unit baru: ', tenant_id)
                    elif kolom == 'kategori':
                        nilai_baru = input_pilihan('Kategori baru:', daftar_kategori)
                    elif kolom != 'tagihan':
                        nilai_baru = input_tidak_kosong('Masukkan nilai baru: ')
                    else:
                        # Khusus kolom tagihan: tambah invoice baru atau ubah status
                        print('1. Tambah tagihan baru')
                        print('2. Ubah status tagihan')
                        aksi = input('Pilih (1-2): ')
                        while aksi != '1' and aksi != '2':
                            print('Pilih 1 atau 2.')
                            aksi = input('Pilih (1-2): ')
                        if aksi == '2' and len(daftar_tagihan) == 0:
                            print('Tenant ini belum punya tagihan, jadi diarahkan ke tambah tagihan.')
                            aksi = '1'

                        if aksi == '1':
                            tagihan_baru = input_tagihan_baru()
                        else:
                            # Cari index invoice di list tagihan tenant ini
                            index_tagihan = -1
                            while index_tagihan == -1:
                                no_invoice = input('No Invoice yang diubah: ').upper()
                                for i in range(len(daftar_tagihan)):
                                    if daftar_tagihan[i]['no_invoice'] == no_invoice:
                                        index_tagihan = i
                                if index_tagihan == -1:
                                    print('No Invoice tidak ada di tenant ini.')
                            status_baru = input_status()

                    # Konfirmasi, baru data benar-benar diubah
                    ubah = input_ya_tidak('Ubah data? (y/n): ')
                    if ubah == 'y':
                        if kolom != 'tagihan':
                            data_tenant[tenant_id][kolom] = nilai_baru
                        elif aksi == '1':
                            daftar_tagihan.append(tagihan_baru)
                        else:
                            daftar_tagihan[index_tagihan]['status'] = status_baru
                        simpan_data()
                        print('Data berhasil diubah')
                    else:
                        print('Data batal diubah')
                else:
                    print('Data batal diubah')
        elif pilihan == '2':
            break
        else:
            print('Pilihan yang Anda masukkan tidak valid')


# ==========================================================
# MENU DELETE & RECYCLE BIN
# ==========================================================
def hapus_ke_recycle_bin():
    # Tenant tidak langsung hilang, tapi dipindahkan ke Recycle Bin
    tenant_id = input_tenant_id('Masukkan Tenant ID: ')
    if tenant_id not in data_tenant:
        tampil_tidak_ada(tenant_id, 'Data yang Anda cari tidak ada')
        return

    tampil_detail_tenant(tenant_id)
    tunggakan = hitung_belum_lunas(data_tenant[tenant_id]['tagihan'])
    if tunggakan > 0:
        print('PERINGATAN: tenant ini masih punya tunggakan {}.'.format(format_rupiah(tunggakan)))

    hapus = input_ya_tidak('Hapus data? Data akan dipindahkan ke Recycle Bin (y/n): ')
    if hapus == 'y':
        recycle_bin[tenant_id] = {
            'data': data_tenant.pop(tenant_id),
            'dihapus_pada': datetime.now().strftime('%d-%m-%Y %H:%M')
        }
        simpan_data()
        print('Data berhasil dihapus dan dipindahkan ke Recycle Bin. Data masih bisa dipulihkan.')
    else:
        print('Data batal dihapus')


def pulihkan_dari_recycle_bin():
    if len(recycle_bin) == 0:
        print('Recycle Bin kosong.')
        return
    tampil_recycle_bin()

    tenant_id = input_tenant_id('Masukkan Tenant ID yang akan dipulihkan: ')
    if tenant_id not in recycle_bin:
        print('Tenant ID tersebut tidak ada di Recycle Bin.')
        return

    tenant = recycle_bin[tenant_id]['data']
    tampil_detail(tenant_id, tenant)

    # Unit lama bisa saja sudah ditempati tenant lain selama tenant ini dihapus
    unit_baru = tenant['unit']
    pemilik = cari_pemilik_unit(unit_baru)
    if pemilik != '':
        print('Unit {} sekarang sudah ditempati {} ({}).'.format(
            unit_baru, data_tenant[pemilik]['nama_tenant'], pemilik))
        print('Masukkan unit lain untuk tenant ini.')
        unit_baru = input_unit('Unit baru: ', tenant_id)

    pulihkan = input_ya_tidak('Pulihkan tenant {} ({})? (y/n): '.format(tenant['nama_tenant'], tenant_id))
    if pulihkan == 'y':
        tenant['unit'] = unit_baru
        data_tenant[tenant_id] = recycle_bin.pop(tenant_id)['data']
        simpan_data()
        print('Data berhasil dipulihkan')
    else:
        print('Data batal dipulihkan')


def hapus_permanen():
    if len(recycle_bin) == 0:
        print('Recycle Bin kosong.')
        return
    tampil_recycle_bin()

    tenant_id = input_tenant_id('Masukkan Tenant ID yang akan dihapus permanen: ')
    if tenant_id not in recycle_bin:
        print('Tenant ID tersebut tidak ada di Recycle Bin.')
        return

    tenant = recycle_bin[tenant_id]['data']
    tampil_detail(tenant_id, tenant)
    tunggakan = hitung_belum_lunas(tenant['tagihan'])
    if tunggakan > 0:
        print('PERINGATAN: catatan tunggakan {} akan ikut hilang.'.format(format_rupiah(tunggakan)))

    hapus = input_ya_tidak('Hapus permanen? Data tidak bisa dikembalikan lagi (y/n): ')
    if hapus == 'y':
        del recycle_bin[tenant_id]
        simpan_data()
        print('Data berhasil dihapus permanen')
    else:
        print('Data batal dihapus')


def menu_delete():
    while True:
        print('\n=== Menu Hapus Data & Recycle Bin ===')
        print('1. Hapus data tenant (pindahkan ke Recycle Bin)')
        print('2. Lihat isi Recycle Bin')
        print('3. Pulihkan tenant dari Recycle Bin')
        print('4. Hapus permanen dari Recycle Bin')
        print('5. Kembali ke menu utama')
        pilihan = input('Pilih menu (1-5): ')

        if pilihan == '1':
            hapus_ke_recycle_bin()
        elif pilihan == '2':
            tampil_recycle_bin()
        elif pilihan == '3':
            pulihkan_dari_recycle_bin()
        elif pilihan == '4':
            hapus_permanen()
        elif pilihan == '5':
            break
        else:
            print('Pilihan yang Anda masukkan tidak valid')


# ==========================================================
# MENU UTAMA
# ==========================================================
def menu_utama():
    while True:
        print('\n===== SISTEM MONITORING TAGIHAN TENANT =====')
        print('1. Tampilkan data')
        print('2. Tambah data')
        print('3. Ubah data')
        print('4. Hapus data & Recycle Bin')
        print('5. Keluar')
        pilihan = input('Pilih menu (1-5): ')

        if pilihan == '1':
            menu_read()
        elif pilihan == '2':
            menu_create()
        elif pilihan == '3':
            menu_update()
        elif pilihan == '4':
            menu_delete()
        elif pilihan == '5':
            print('Terima kasih, program selesai.')
            break
        else:
            print('Pilihan yang Anda masukkan tidak valid')


if __name__ == '__main__':
    muat_data()
    menu_utama()
