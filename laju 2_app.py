import streamlit as st
import pandas as pd
from datetime import datetime
import time
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import random
import string

# --- KONFIGURASI HALAMAN & TEMA ---
st.set_page_config(page_title="Laju Logix", page_icon="🚚", layout="wide")

# Custom CSS untuk Tema Navy, Orange, Cream, Hitam
st.markdown("""
<style>
    /* Background & Text Utama */
    .stApp {
        background-color: #F5F5DC; /* Cream Background */
        color: #000000;
    }
    
    /* Sidebar (Menu) */
    section[data-testid="stSidebar"] {
        background-color: #001f3f; /* Navy */
        color: white;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #FF851B !important; /* Orange Headers in Sidebar */
    }
    
    /* Tombol Utama (Orange) */
    .stButton>button {
        background-color: #FF851B;
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #e67300;
        color: white;
    }
    
    /* Header/Judul */
    h1, h2, h3 {
        color: #001f3f; /* Navy Headers */
    }
    
    /* Card/Container Style */
    .css-1r6slb0 {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    
    /* Success Message */
    .stSuccess {
        background-color: #001f3f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SEMU & SESSION STATE ---

# Data User
USERS = {
    "alisa": {"jabatan": "manajer", "sandi": "000001", "img": "👩‍💼"},
    "cantika": {"jabatan": "admin", "sandi": "000002", "img": "👩‍💻"}
}

# Data Wilayah (Sampel Hierarki Pulau Jawa)
WILAYAH = {
    "Jawa Timur": {
        "Malang": {
            "Klojen": ["Kauman", "Oro-oro Dowo", "Bareng"],
            "Lowokwaru": ["Jatimulyo", "Tunggulwulung", "Dinoyo"]
        },
        "Surabaya": {
            "Gubeng": ["Airlangga", "Gubeng", "Kertajaya"],
            "Wonokromo": ["Darmo", "Jagir"]
        }
    },
    "Jawa Barat": {
        "Bandung": {
            "Cicendo": ["Arjuna", "Husein"],
            "Coblong": ["Dago", "Lebakgede"]
        }
    }
}

# Inisialisasi State
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None
if 'login_history' not in st.session_state:
    st.session_state.login_history = []
if 'shipping_data' not in st.session_state:
    st.session_state.shipping_data = [] # Database pengiriman
if 'current_order' not in st.session_state:
    st.session_state.current_order = {}

# --- FUNGSI HELPER ---
def generate_resi():
    """Membuat ID Resi Random"""
    return "LJU" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_barcode(resi):
    """Membuat gambar barcode"""
    EAN = barcode.get_barcode_class('code128')
    my_ean = EAN(resi, writer=ImageWriter())
    buffer = BytesIO()
    my_ean.write(buffer)
    return buffer

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# --- HALAMAN-HALAMAN ---

def login_page():
    st.markdown("<h1 style='text-align: center; color: #001f3f;'>Login Laju Logix</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username (Nama)")
            password = st.text_input("Password (Sandi)", type="password")
            submit = st.form_submit_button("Masuk")
            
            if submit:
                if username.lower() in USERS and USERS[username.lower()]['sandi'] == password:
                    st.session_state.user = username.lower()
                    st.session_state.login_time = datetime.now()
                    st.session_state.page = 'dashboard'
                    st.success(f"Welcome to Laju, {username.capitalize()}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Username/Password salah")
        
        # Tampilkan Data User (Sesuai Prompt)
        st.info("ℹ️ **Data User Terdaftar:**")
        user_df = pd.DataFrame([
            {"Nama": k, "Jabatan": v['jabatan'], "Sandi": v['sandi']} 
            for k, v in USERS.items()
        ])
        st.dataframe(user_df, hide_index=True)

def dashboard_page():
    user_data = USERS[st.session_state.user]
    
    # --- HEADER DASHBOARD (Profile) ---
    col_prof, col_title, col_menu = st.columns([2, 6, 2])
    with col_prof:
        # Menampilkan foto profil lingkaran dan nama
        st.markdown(f"""
        <div style="display: flex; align-items: center; background-color: #001f3f; padding: 10px; border-radius: 50px; color: white;">
            <div style="font-size: 40px; margin-right: 10px;">{user_data['img']}</div>
            <div>
                <strong>{st.session_state.user.capitalize()}</strong><br>
                <small>{user_data['jabatan'].capitalize()}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- MENU TITIK 3 (Sidebar Logic) ---
    with st.sidebar:
        st.header("Menu")
        menu_choice = st.radio("Navigasi", ["Beranda", "Data", "Rekap Login"])
        
        st.divider()
        if st.button("Log Out"):
            # Catat log out
            now = datetime.now()
            duration = now - st.session_state.login_time
            seconds = duration.total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            
            st.session_state.login_history.append({
                "User": st.session_state.user,
                "Login": st.session_state.login_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Logout": now.strftime("%Y-%m-%d %H:%M:%S"),
                "Durasi": f"{hours} jam {minutes} menit"
            })
            
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()

    # --- CONTENT DASHBOARD ---
    if menu_choice == "Beranda":
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if st.button("📦 Kirim Barang", use_container_width=True):
                st.session_state.page = "kirim_barang"
                st.rerun()
        with c2:
            if st.button("🔄 Transit", use_container_width=True):
                st.session_state.page = "transit"
                st.rerun()
        with c3:
            if st.button("📍 Tracking", use_container_width=True):
                st.info("Fitur Tracking sedang dikembangkan.")
                
    elif menu_choice == "Data":
        tabs = st.tabs(["Data User", "Rekap Pengiriman", "Keuangan"])
        with tabs[0]:
            st.dataframe(pd.DataFrame(USERS).T)
        with tabs[1]:
            if st.session_state.shipping_data:
                st.dataframe(pd.DataFrame(st.session_state.shipping_data))
            else:
                st.write("Belum ada data pengiriman.")
        with tabs[2]:
            st.metric("Total Pemasukan", "Rp 0 (Dummy)")
            
    elif menu_choice == "Rekap Login":
        st.subheader("Rekap Login User")
        if st.session_state.login_history:
            st.dataframe(pd.DataFrame(st.session_state.login_history))
        else:
            st.write("Belum ada riwayat login.")
        # Tampilkan sesi aktif
        st.write(f"Sesi Aktif: {st.session_state.user} (Login sejak: {st.session_state.login_time})")

def shipping_form_page():
    st.markdown("## 📝 Formulir Kirim Barang")
    
    with st.form("form_resi"):
        st.markdown("### Pengirim")
        col1, col2 = st.columns(2)
        sender_name = col1.text_input("Nama Pengirim")
        sender_phone = col2.text_input("No. Telp Pengirim")
        sender_addr = st.text_area("Alamat Pengirim (Cabang Asal)")
        
        st.markdown("### Penerima")
        col3, col4 = st.columns(2)
        recv_name = col3.text_input("Nama Penerima")
        recv_phone = col4.text_input("No. Telp Penerima")
        
        # Lokasi Bertingkat
        st.markdown("#### Alamat Penerima")
        prov = st.selectbox("Provinsi (Jawa)", list(WILAYAH.keys()))
        cities = list(WILAYAH[prov].keys())
        city = st.selectbox("Kota/Kabupaten", cities)
        kels = list(WILAYAH[prov][city].keys())
        kel = st.selectbox("Kecamatan", kels) # Simplified hierarchy for demo
        subs = WILAYAH[prov][city][kel]
        sub = st.selectbox("Kelurahan", subs)
        street = st.text_input("Nama Jalan (User Mengisi)")
        
        st.markdown("### Detail Barang")
        item_type = st.selectbox("Jenis Barang", [
            "Barang Pecah Belah", "Fashion & Tekstil", "Elektronik", 
            "Kosmetik & Perawatan", "Perlengkapan Rumah Tangga", "Dokumen", 
            "Makanan & Minuman", "Otomotif", "Alat Kesehatan"
        ])
        
        c_dim1, c_dim2, c_dim3, c_dim4 = st.columns(4)
        p = c_dim1.number_input("Panjang (cm)", min_value=1)
        l = c_dim2.number_input("Lebar (cm)", min_value=1)
        t = c_dim3.number_input("Tinggi (cm)", min_value=1)
        vol_total = p * l * t
        c_dim4.metric("Volume Total (cm3)", vol_total)
        
        weight = st.number_input("Berat (kg)", min_value=0.1)
        
        ship_type = st.selectbox("Pilihan Pengiriman", ["Express", "Cargo", "Makanan"])
        
        # Logika Garansi
        pake_garansi = st.checkbox("Gunakan Garansi?")
        harga_barang = 0
        biaya_garansi = 0
        klaim_info = ""
        
        if pake_garansi:
            st.info("Input Nilai Barang untuk asuransi")
            harga_barang = st.number_input("Harga Barang (Rp)", min_value=0)
            
            if ship_type == "Express":
                biaya_garansi = 0.003 * harga_barang
                klaim_info = "Klaim: 100% Harga Barang + Ongkir"
            elif ship_type == "Cargo":
                biaya_garansi = 0.005 * harga_barang
                klaim_info = "Klaim: Sesuai % Kerusakan (Max 100%)"
            elif ship_type == "Makanan":
                biaya_garansi = 5000
                klaim_info = "Klaim: 100% Harga Barang + Ongkir (Flat Rate)"
            
            st.write(f"**Biaya Garansi:** {format_rupiah(biaya_garansi)}")
            st.caption(klaim_info)
            
        submitted = st.form_submit_button("Lanjut ke Pembayaran")
        
        if submitted:
            # Validasi Form
            if not all([sender_name, sender_phone, sender_addr, recv_name, recv_phone, street]):
                st.error("Mohon lengkapi semua data formulir!")
            else:
                # Simpan ke session state sementara
                st.session_state.current_order = {
                    "sender": {"name": sender_name, "phone": sender_phone, "addr": sender_addr},
                    "receiver": {"name": recv_name, "phone": recv_phone, "addr": f"{street}, {sub}, {kel}, {city}, {prov}"},
                    "item": {"type": item_type, "dims": (p, l, t), "vol": vol_total, "weight": weight, "price": harga_barang},
                    "shipping": {"type": ship_type, "warranty_cost": biaya_garansi, "use_warranty": pake_garansi},
                    "resi": generate_resi(),
                    "status": "Pending Payment"
                }
                st.session_state.page = "pembayaran"
                st.rerun()
    
    if st.button("Kembali"):
        st.session_state.page = "dashboard"
        st.rerun()

def payment_page():
    st.markdown("## 💰 Halaman Pembayaran")
    order = st.session_state.current_order
    
    # Hitung Ongkir Dasar
    weight = order['item']['weight']
    vol = order['item']['vol']
    ship_type = order['shipping']['type']
    base_cost = 0
    surcharge = 0
    
    if ship_type == "Express":
        # 17rb/kg min 1kg
        charge_weight = max(1, weight)
        base_cost = charge_weight * 17000
        
    elif ship_type == "Cargo":
        # 4000/kg min 10kg, max dim 40x40x40
        charge_weight = max(10, weight)
        base_cost = charge_weight * 4000
        
        # Cek Volume
        max_vol = 40 * 40 * 40 # 64000
        if vol > max_vol:
            excess = vol - max_vol
            # 1500 per 250cm3
            blocks = excess / 250
            surcharge = blocks * 1500
            
    elif ship_type == "Makanan":
        # 25rb/kg min 1kg
        charge_weight = max(1, weight)
        base_cost = charge_weight * 25000

    warranty_cost = order['shipping']['warranty_cost']
    subtotal = base_cost + surcharge + warranty_cost
    
    # Tampilan Rincian
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Layanan:** {ship_type}")
        st.write(f"**Berat:** {weight} kg | **Volume:** {vol} cm3")
        st.write(f"Ongkir Dasar: {format_rupiah(base_cost)}")
        if surcharge > 0:
            st.write(f"Biaya Tambahan Volume: {format_rupiah(surcharge)}")
        st.write(f"Biaya Garansi: {format_rupiah(warranty_cost)}")
    
    # Metode Pembayaran
    st.write("---")
    pay_system = st.radio("Sistem Pembayaran", ["Prepaid", "COD"])
    pay_method = st.radio("Metode Pembayaran", ["Cash", "Transfer (BNI)"])
    
    cod_fee = 0
    if pay_system == "COD":
        if subtotal < 100000:
            cod_fee = subtotal * 0.05
        else:
            cod_fee = subtotal * 0.025
    
    total_final = subtotal + cod_fee
    
    st.markdown(f"### Total Tagihan: {format_rupiah(total_final)}")
    if pay_system == "COD":
        st.caption(f"(Termasuk biaya layanan COD: {format_rupiah(cod_fee)})")
    
    # Generate Resi Display
    st.write("---")
    st.subheader(f"No. Resi: {order['resi']}")
    # Barcode
    st.image(generate_barcode(order['resi']), caption="Scan Barcode", width=300)
    
    # Tombol Aksi
    col_pay, col_print = st.columns(2)
    
    payment_done = False
    
    with col_pay:
        if st.button("Sudah Bayar"):
            st.success("Pembayaran Dikonfirmasi!")
            st.session_state.current_order['status'] = "Lunas"
            st.session_state.payment_confirmed = True # Flag sementara
    
    # Logic Tombol Cetak
    can_print = False
    if pay_system == "COD":
        can_print = True
    elif pay_system == "Prepaid":
        # Harus klik sudah bayar dulu (cek session state flag atau logic sederhana)
        if st.session_state.get('payment_confirmed', False):
            can_print = True
        else:
            st.warning("Klik 'Sudah Bayar' untuk membuka tombol cetak.")

    with col_print:
        if can_print:
            if st.button("Cetak Resi"):
                # Simpan data lengkap ke database utama
                final_record = order.copy()
                final_record.update({
                    "total_cost": total_final,
                    "payment_system": pay_system,
                    "payment_method": pay_method,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state.shipping_data.append(final_record)
                
                st.session_state.page = "cetak_resi"
                st.rerun()
        else:
            st.button("Cetak Resi", disabled=True)

def print_receipt_page():
    st.markdown("## 🖨️ Cetak Resi")
    order = st.session_state.current_order
    
    # Tampilan Resi (Simulasi Kertas)
    with st.container():
        st.markdown(f"""
        <div style="border: 2px solid black; padding: 20px; background-color: white;">
            <h2 style="text-align: center;">LAJU LOGISTICS</h2>
            <hr>
            <h3>RESI: {order['resi']}</h3>
            <p><strong>Tanggal:</strong> {datetime.now().strftime("%Y-%m-%d")}</p>
            <table style="width:100%">
                <tr>
                    <td style="width:50%; vertical-align:top;">
                        <strong>PENGIRIM:</strong><br>
                        {order['sender']['name']}<br>
                        {order['sender']['phone']}<br>
                        {order['sender']['addr']}
                    </td>
                    <td style="width:50%; vertical-align:top;">
                        <strong>PENERIMA:</strong><br>
                        {order['receiver']['name']}<br>
                        {order['receiver']['phone']}<br>
                        {order['receiver']['addr']}
                    </td>
                </tr>
            </table>
            <hr>
            <p><strong>Barang:</strong> {order['item']['type']} ({order['item']['weight']} kg)</p>
            <p><strong>Layanan:</strong> {order['shipping']['type']}</p>
            <h3 style="text-align: right;">JANGAN DIBANTING!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.image(generate_barcode(order['resi']), width=250)
    
    st.button("Simpan Gambar Resi (Simulasi Download)")
    
    if st.button("Kembali ke Dashboard"):
        st.session_state.current_order = {} # Clear order
        st.session_state.payment_confirmed = False
        st.session_state.page = "dashboard"
        st.rerun()

def transit_page():
    st.markdown("## 🔄 Menu Transit")
    
    # Simulasi Scan
    col_cam, col_input = st.columns(2)
    with col_cam:
        enable_cam = st.button("📷 Buka Kamera Scanner")
        if enable_cam:
            st.camera_input("Scan Barcode Resi")
            st.caption("Simulasi: Kamera aktif.")
            
    with col_input:
        input_resi = st.text_input("Atau Masukkan No. Resi Manual")
    
    # Cari Data
    found_data = None
    if input_resi:
        # Cari di shipping_data
        for data in st.session_state.shipping_data:
            if data['resi'] == input_resi:
                found_data = data
                break
        
        if found_data:
            st.success("Data Ditemukan!")
            st.json({
                "Pengirim": found_data['sender']['name'],
                "Penerima": found_data['receiver']['name'],
                "Alamat Tujuan": found_data['receiver']['addr'],
                "Barang": found_data['item']['type'],
                "Berat": f"{found_data['item']['weight']} kg"
            })
            
            if st.button("Verifikasi & Lanjut"):
                st.session_state.verified_transit = True
        else:
            st.warning("Resi tidak ditemukan di database.")

    # Tombol Status (Muncul setelah verifikasi)
    if st.session_state.get('verified_transit', False):
        st.divider()
        c1, c2, c3 = st.columns(3)
        if c1.button("⚙️ Diproses"):
            st.toast("Status Update: Paket Diproses")
        if c2.button("🚛 Siap Transit"):
            st.toast("Status Update: Paket Siap Transit")
        if c3.button("✅ Diterima Customer"):
            st.balloons()
            st.success("Paket Selesai!")
            
    if st.button("Kembali ke Menu"):
        st.session_state.verified_transit = False
        st.session_state.page = "dashboard"
        st.rerun()

# --- MAIN ROUTER ---
if st.session_state.page == 'login':
    login_page()
elif st.session_state.page == 'dashboard':
    dashboard_page()
elif st.session_state.page == 'kirim_barang':
    shipping_form_page()
elif st.session_state.page == 'pembayaran':
    payment_page()
elif st.session_state.page == 'cetak_resi':
    print_receipt_page()
elif st.session_state.page == 'transit':
    transit_page()