# Sistem Monitoring Tagihan Tenant

A command-line application that helps shopping mall and commercial building managers keep track of tenants and their monthly bills: rent, service charge, utilities. At any moment it shows who has paid, who hasn't, and how much is still outstanding. Everything is saved to a CSV file, and billing reports can be exported for Excel or further analysis.

> The interface is in Bahasa Indonesia, because it is built for building management teams in Indonesia.

---

## The problem

A mall's finance team often tracks dozens of tenants, each with several bills every month, in spreadsheets. Answering simple questions takes manual work:

- Which tenants still have unpaid bills?
- How much of this month's billing has actually been collected?
- Is this unit already occupied? Has this invoice number been used before?

Mistakes are easy to make, too: duplicate invoice numbers, two tenants recorded in the same unit, impossible dates such as 31 February, or a tenant deleted by accident together with its unpaid bills.

## Who it's for

Administrative and finance staff in **building management** who need a quick, reliable view of tenant billing without rebuilding a spreadsheet every time.

---

## Features

### 1. View data
- A table of all tenants with their unit, category, number of invoices and outstanding amount.
- A **billing summary** below the table:
  - total billed
  - amount and percentage already paid
  - the tenant with the largest outstanding balance
  - outstanding amount per tenant category
- Search one tenant by Tenant ID to see all of its invoices.
- **Export a billing report to CSV**, either all invoices or unpaid invoices only. The file opens directly in Excel or Google Sheets.

### 2. Add a tenant
- Register a new tenant together with its first invoice.
- Category and bill type are chosen from a list, so naming stays consistent.
- Nothing is saved until the user confirms.

### 3. Edit a tenant
- Change name, unit or category.
- Add a new invoice, or update an invoice's payment status (Paid / Unpaid).
- The Tenant ID itself cannot be changed, because it is the primary key.
- The new value is held temporarily and saved only after confirmation.

### 4. Delete with a Recycle Bin
- Deleting a tenant **moves it to a Recycle Bin** instead of erasing it, together with the time it was deleted.
- Before deleting, the app shows the tenant's details and **warns if the tenant still has unpaid bills**.
- From the Recycle Bin the user can:
  - **restore** a tenant. If its old unit has been taken by another tenant in the meantime, the app asks for a new unit.
  - **delete it permanently**, with a final confirmation.

### Data is saved automatically
- Every change is written to `data_tagihan.csv` and loaded again the next time the app starts, Recycle Bin included.
- On the first run, the file is created from three sample tenants so every feature can be tried right away.
- If the file is damaged, the app does not crash. It backs up the damaged file as `data_tagihan_rusak.csv` and starts from the sample data.

### Data validation
| Rule | Example of rejected input |
|---|---|
| Tenant ID must be unique, format `T` + 3 digits | `T1`, `abc`, an ID that already exists |
| One unit can only be occupied by one tenant | `GF-12` when Kopi Sudut already occupies it |
| Invoice numbers are unique across all tenants, including those in the Recycle Bin | `INV001` when it is already used |
| Billing period must be a real calendar date (`DD-MM-YYYY`), leap years included | `31-02-2026`, `1-9-2026`, `01/09/2026` |
| Amount must be a positive whole number | `abc`, `0`, `-5` |
| Text fields cannot be empty or spaces only | `"   "` |
| Every menu rejects invalid options and asks again | `9` in a menu with options 1–5 |

---

## Preview

```
Daftar Tenant
ID     Nama Tenant          Unit    Kategori       Invoice        Belum Lunas
-----------------------------------------------------------------------------
T001   Kopi Sudut           GF-12   F&B                  2       Rp 2.500.000
T002   Roti Pagi            LG-05   F&B                  1      Rp 12.000.000
T003   Mode Kita            UG-21   Fashion              2       Rp 3.200.000

--- Ringkasan ---
Jumlah tenant       : 3
Jumlah invoice      : 5
Total tagihan       : Rp 52.700.000
Sudah lunas         : Rp 35.000.000 (66%)
Belum lunas         : Rp 17.700.000 (34%)
Tunggakan terbesar  : Roti Pagi (T002) - Rp 12.000.000
Tunggakan per kategori:
  F&B            Rp 14.500.000
  Fashion        Rp 3.200.000
```

Deleting a tenant that still owes money:
```
PERINGATAN: tenant ini masih punya tunggakan Rp 12.000.000.
Hapus data? Data akan dipindahkan ke Recycle Bin (y/n): y
Data berhasil dihapus dan dipindahkan ke Recycle Bin. Data masih bisa dipulihkan.

Isi Recycle Bin
ID     Nama Tenant          Unit    Dihapus pada             Belum Lunas
------------------------------------------------------------------------
T002   Roti Pagi            LG-05   12-10-2026 09:53       Rp 12.000.000
```

Exporting unpaid invoices:
```
Laporan berhasil dibuat: laporan/laporan_tagihan_belum_lunas_2026-10-12.csv
Isi: 3 tagihan, total Rp 17.700.000
```

---

## How to run

Requires **Python 3** and nothing else. The app uses only the standard library.

```bash
git clone https://github.com/asabovetzy/sistem-monitoring-tagihan-tenant.git
cd sistem-monitoring-tagihan-tenant
python3 monitoring_tagihan_tenant.py
```

### Files created while running
```
sistem-monitoring-tagihan-tenant/
├── monitoring_tagihan_tenant.py     the application
├── data_tagihan.csv                 saved data (created on first run)
└── laporan/                         exported billing reports
    └── laporan_tagihan_belum_lunas_2026-10-12.csv
```

---

## The data file

`data_tagihan.csv` is a tidy table: **one row per invoice**, with the tenant's details repeated on each row.

```
tenant_id,nama_tenant,unit,kategori,no_invoice,jenis,periode,jumlah,status,status_tenant,dihapus_pada
T001,Kopi Sudut,GF-12,F&B,INV001,Sewa,01-09-2026,15000000,Lunas,Aktif,
T001,Kopi Sudut,GF-12,F&B,INV002,Service Charge,01-09-2026,2500000,Belum Lunas,Aktif,
T002,Roti Pagi,LG-05,F&B,INV003,Sewa,01-09-2026,12000000,Belum Lunas,Aktif,
```

Because of this shape, the file can go straight into analysis tools. For example, with pandas:

```python
import pandas as pd

df = pd.read_csv('data_tagihan.csv')
aktif = df[df['status_tenant'] == 'Aktif']

# Outstanding balance per tenant, largest first
aktif[aktif['status'] == 'Belum Lunas'].groupby('nama_tenant')['jumlah'].sum().sort_values(ascending=False)
```
```
nama_tenant
Roti Pagi     12000000
Mode Kita      3200000
Kopi Sudut     2500000
```

---

## How it works

### Menu structure
```
Main menu
├── 1. Tampilkan data
│      ├── all tenants + billing summary
│      ├── one tenant's invoices
│      └── export billing report to CSV
├── 2. Tambah data             add a tenant with its first invoice
├── 3. Ubah data               edit a column, add an invoice, or change payment status
├── 4. Hapus data & Recycle Bin
│      ├── delete (move to Recycle Bin)
│      ├── view Recycle Bin
│      ├── restore
│      └── delete permanently
└── 5. Keluar
```

Every data-changing action follows the same flow: **enter Tenant ID → check it exists → show the data → confirm (y/n) → apply the change → save to CSV.**

### Data model
While the app runs, tenants are kept in a dictionary keyed by Tenant ID, so lookups are direct and IDs are unique by design. Each tenant holds a list of invoices, because a tenant can have many invoices and the list grows every month.

```python
data_tenant = {
    'T001': {
        'nama_tenant': 'Kopi Sudut',
        'unit': 'GF-12',
        'kategori': 'F&B',
        'tagihan': [
            {'no_invoice': 'INV001', 'jenis': 'Sewa', 'periode': '01-09-2026',
             'jumlah': 15000000, 'status': 'Lunas'},
            ...
        ]
    },
    ...
}
```

Deleted tenants are moved to a separate `recycle_bin` dictionary together with their deletion time, so they can be restored with all their invoices intact.

When saving, this nested structure is flattened into the one-row-per-invoice CSV shown above. When loading, the rows are grouped back by Tenant ID.

### Code organisation
The program is split into small, single-purpose functions that are reused across menus:

| Group | Examples |
|---|---|
| Input validation | `input_angka`, `input_ya_tidak`, `input_tenant_id`, `input_periode`, `input_pilihan` |
| Business rules | `cek_no_invoice` (unique invoice), `input_unit` (one tenant per unit), `format_periode_benar` (valid date) |
| Calculations | `hitung_belum_lunas`, `tampil_statistik` |
| Display | `tampil_semua_tenant`, `tampil_detail`, `tampil_recycle_bin` |
| Storage and reports | `simpan_data`, `muat_data`, `export_laporan` |
| Menus | `menu_read`, `menu_create`, `menu_update`, `menu_delete`, `menu_utama` |

---

## Next steps

- Filter tenants by category or by unpaid status directly in the app.
- Track due dates and flag overdue bills.
- Move storage from CSV to a database (SQLite) for larger portfolios of tenants.
- A dashboard on top of the CSV data to visualise collection rates over time.

---

## Author

**Raihan Hasbi**
- GitHub: [asabovetzy](https://github.com/asabovetzy)
- LinkedIn: *add your LinkedIn URL here*
