# Midtrans Payment Provider for Odoo 17

Integrasi payment gateway Midtrans untuk Odoo 17 dengan dukungan berbagai metode pembayaran.

## ✨ Fitur

- ✅ Kartu Kredit & Debit (Visa, Mastercard, JCB, Amex)
- ✅ Transfer Bank (BCA, Mandiri, BNI, BRI, Permata)
- ✅ E-Wallet (GoPay, OVO, Dana, LinkAja, ShopeePay)
- ✅ Retail (Alfamart, Indomaret)
- ✅ Sandbox & Production environment
- ✅ Real-time webhook notifications
- ✅ Integrasi website checkout

---

## 📦 Instalasi

### Step 1: Copy Module ke Odoo
```bash
# Copy folder ke addons directory
cp -r payment_midtrans /path/to/odoo/addons/
```

### Step 2: Restart Odoo
```bash
sudo systemctl restart odoo
```

### Step 3: Install Module di Odoo
1. Login sebagai **Admin**
2. Pergi ke **Apps**
3. Search: **Midtrans**
4. Klik **Install**

---

## ⚙️ Konfigurasi

### Step 1: Dapatkan Credentials Midtrans

1. Login ke [Midtrans Dashboard](https://dashboard.midtrans.com)
2. Pilih environment: **Sandbox** (untuk test) atau **Production** (live)
3. Pergi ke **Settings** → **Access Keys**
4. Copy 3 credentials:
   - **Merchant ID**: Contoh `M123456`
   - **Client Key**: Contoh `SB-Mid-client-xxxxx`
   - **Server Key**: Contoh `SB-Mid-server-xxxxx`

### Step 2: Konfigurasi di Odoo

1. Pergi ke **Accounting** → **Payments** → **Payment Providers**
2. Cari atau buat record **Midtrans**
3. Isi form:
   ```
   Name: Midtrans
   Code: midtrans
   State: Enabled ✓
   Published: Checked ✓
   Environment: Sandbox (untuk test)
   
   Credentials:
   - Merchant ID: [paste dari dashboard]
   - Client Key: [paste dari dashboard]
   - Server Key: [paste dari dashboard]
   ```
4. Klik **Save**

### Step 3: Setup Webhook Notification

Agar status pembayaran terupdate otomatis:

1. Di **Midtrans Dashboard**, pergi ke **Settings** → **Configuration**
2. Set **Payment Notification URL** ke:
   ```
   https://yoursite.com/payment/midtrans/notification
   ```
3. Save

### Step 4: Enable di Website

Agar Midtrans muncul di opsi pembayaran website:

1. Pergi ke **Website** → **Configuration** → **Settings**
2. Scroll ke section **E-Commerce**
3. Di **Payment Providers**, centang **Midtrans**
4. Klik **Save**

---

## 🧪 Testing

### Test dengan Sandbox

Pastikan credentials menggunakan **Sandbox keys** dari dashboard.

### Test Card Numbers

**Success Payment:**
```
Card Number: 4111111111111111
CVV: 123
Expiry: 12/25
```

**Failed Payment:**
```
Card Number: 5555555555554444
CVV: 123
Expiry: 12/25
```

### Test Checkout Flow

1. Buka website Anda
2. Tambah produk ke cart
3. Pergi ke **Checkout**
4. Pilih **Midtrans** dari payment options
5. Klik **Proceed to Payment**
6. Pilih payment method (Card, Bank, E-Wallet)
7. Lengkapi pembayaran dengan test card
8. Lihat hasil di payment status page

---

## 🔍 Troubleshooting

### Midtrans tidak muncul di opsi pembayaran

**Cek:**
- [ ] Payment Provider status = **Enabled**
- [ ] Payment Provider = **Published** ✓
- [ ] Midtrans sudah di-add ke **Website settings**
- [ ] Browser cache sudah di-clear (Ctrl+Shift+Delete)

**Solusi:**
```bash
# Restart Odoo
sudo systemctl restart odoo

# Clear browser cache
# Refresh website
```

### Error: "Transaction ID not found"

**Penyebab:** Transaksi belum create di database

**Solusi:**
1. Pastikan refresh checkout page
2. Tambah produk baru ke cart
3. Coba checkout lagi

### Error: "Invalid Credentials"

**Penyebab:** Merchant ID, Client Key, atau Server Key salah

**Solusi:**
1. Buka **Midtrans Dashboard**
2. Cek **Access Keys** sudah copy dengan benar
3. Pastikan tidak ada spasi tambahan
4. Update credentials di Payment Provider
5. Save dan coba lagi

### Webhook tidak diterima

**Penyebab:** Notification URL tidak diset atau tidak accessible

**Solusi:**
1. Pastikan website accessible dari internet (HTTPS)
2. Set **Payment Notification URL** di Midtrans Dashboard:
   ```
   https://yoursite.com/payment/midtrans/notification
   ```
3. Test dengan payment baru

### Payment stuck di "Pending"

**Solusi:**
1. Buka transaksi di Odoo
2. Manual check status di Midtrans Dashboard
3. Update status manual jika perlu

---

## 📊 Monitoring

### Check Payment Status

**Di Odoo:**
1. **Accounting** → **Payments** → **Transactions**
2. Cari transaksi berdasarkan order ID atau customer
3. Lihat status: Done / Pending / Cancelled / Error

**Di Midtrans Dashboard:**
1. Pergi ke **Monitoring** → **Transactions**
2. Lihat real-time transaction status

---

## 🎯 Production Deployment

Ketika siap go live:

### Step 1: Get Production Credentials
1. Login ke [Midtrans Dashboard](https://dashboard.midtrans.com)
2. Switch ke **Production** environment
3. Copy **Production** Access Keys

### Step 2: Update Odoo Configuration
1. Buka **Payment Provider** → **Midtrans**
2. Update credentials dengan **Production keys**
3. Ubah **Environment** dari `Sandbox` ke `Production`
4. Ubah **State** ke `Enabled`
5. Save

### Step 3: Verify
1. Test payment dengan production environment
2. Pastikan payment berhasil dan status terupdate
3. Monitor transaksi di Midtrans Dashboard

---

## 📞 Support

### Dokumentasi Resmi
- **Odoo**: https://www.odoo.com/documentation/17.0/
- **Midtrans**: https://docs.midtrans.com/
- **Midtrans API**: https://api-docs.midtrans.com/

### Bantuan Setup
Hubungi **Midtrans Support**:
- Email: support@midtrans.com
- Chat: https://midtrans.com

---

## 📝 Notes

- **Server Key** disimpan secara aman di database (admin-only access)
- **Webhook** diperlukan untuk update status otomatis
- **HTTPS** wajib untuk production environment
- **Currencies**: Pastikan website currency ada di supported list

---

**Version**: 17.0.1.0.0  
**Last Updated**: January 2026
