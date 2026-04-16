from core.bot import bot, safe_reply
from telebot import types
import asyncio
import logging
import random
from database.db import db

# Game state storage
roulette_games = {}
active_games = {}
tebak_kata_games = {}

WORD_LIST = [
    # Binatang
    {"word": "kucing", "clue": "Hewan peliharaan yang mengeong"},
    {"word": "anjing", "clue": "Hewan peliharaan yang menggonggong"},
    {"word": "gajah", "clue": "Hewan besar dengan belalai"},
    {"word": "harimau", "clue": "Kucing besar yang loreng"},
    {"word": "jerapah", "clue": "Hewan dengan leher sangat panjang"},
    {"word": "burung", "clue": "Hewan yang memiliki sayap dan terbang"},
    {"word": "ikan", "clue": "Hewan yang bernapas dengan insang di air"},
    {"word": "semut", "clue": "Serangga kecil yang hidup berkoloni"},
    {"word": "lebah", "clue": "Serangga penghasil madu"},
    {"word": "monyet", "clue": "Primata yang suka makan pisang"},
    {"word": "ular", "clue": "Reptil melata tanpa kaki"},
    {"word": "kuda", "clue": "Hewan yang sering dijadikan tunggangan"},
    {"word": "sapi", "clue": "Hewan ternak penghasil susu"},
    {"word": "kambing", "clue": "Hewan ternak yang bunyinya mbeee"},
    {"word": "ayam", "clue": "Unggas yang berkokok di pagi hari"},
    {"word": "bebek", "clue": "Unggas yang suka berenang dan bunyi kwek"},
    {"word": "kelinci", "clue": "Hewan telinga panjang yang suka wortel"},
    {"word": "buaya", "clue": "Reptil besar pemakan daging di sungai"},
    {"word": "zebra", "clue": "Kuda liar dengan kulit belang hitam putih"},
    {"word": "singa", "clue": "Si raja hutan yang mengaum"},
    # Benda & Elektronik
    {"word": "lemari", "clue": "Tempat untuk menyimpan pakaian"},
    {"word": "pesawat", "clue": "Kendaraan udara untuk transportasi jarak jauh"},
    {"word": "komputer", "clue": "Alat elektronik pengolah data"},
    {"word": "internet", "clue": "Jaringan global yang menghubungkan dunia"},
    {"word": "buku", "clue": "Kumpulan kertas berisi tulisan atau gambar"},
    {"word": "pensil", "clue": "Alat tulis dari kayu dan grafit"},
    {"word": "sepatu", "clue": "Alas kaki yang menutupi seluruh kaki"},
    {"word": "handphone", "clue": "Telepon genggam nirkabel"},
    {"word": "meja", "clue": "Mebel dengan permukaan datar dan kaki"},
    {"word": "kursi", "clue": "Tempat duduk dengan sandaran"},
    {"word": "lampu", "clue": "Alat penghasil cahaya"},
    {"word": "pintu", "clue": "Jalan masuk atau keluar dari ruangan"},
    {"word": "jendela", "clue": "Lubang udara dan cahaya di dinding"},
    {"word": "kertas", "clue": "Lembaran tipis untuk menulis atau mencetak"},
    {"word": "kamera", "clue": "Alat untuk mengambil foto atau video"},
    {"word": "sepeda", "clue": "Kendaraan roda dua yang dikayuh"},
    {"word": "motor", "clue": "Kendaraan roda dua bermesin"},
    {"word": "mobil", "clue": "Kendaraan roda empat bermesin"},
    {"word": "laptop", "clue": "Komputer jinjing yang bisa dibawa-bawa"},
    {"word": "mouse", "clue": "Alat penunjuk pada komputer"},
    {"word": "keyboard", "clue": "Papan ketik pada komputer"},
    {"word": "monitor", "clue": "Layar penampil gambar pada komputer"},
    {"word": "kabel", "clue": "Kawat penghantar listrik atau data"},
    {"word": "baterai", "clue": "Alat penyimpan energi listrik portable"},
    {"word": "tas", "clue": "Wadah untuk membawa barang-barang"},
    {"word": "dompet", "clue": "Wadah kecil untuk menyimpan uang dan kartu"},
    {"word": "payung", "clue": "Alat pelindung dari hujan atau panas matahari"},
    {"word": "kunci", "clue": "Alat untuk membuka gembok atau pintu"},
    {"word": "jam", "clue": "Alat penunjuk waktu"},
    {"word": "piring", "clue": "Wadah datar untuk makan"},
    # Geografi & Kota
    {"word": "jakarta", "clue": "Ibu kota Indonesia"},
    {"word": "bandung", "clue": "Ibu kota Provinsi Jawa Barat"},
    {"word": "surabaya", "clue": "Kota Pahlawan di Jawa Timur"},
    {"word": "medan", "clue": "Kota terbesar di Pulau Sumatera"},
    {"word": "bali", "clue": "Pulau Dewata yang terkenal dengan wisatanya"},
    {"word": "papua", "clue": "Provinsi paling timur di Indonesia"},
    {"word": "gunung", "clue": "Bagian bumi yang menonjol tinggi"},
    {"word": "pantai", "clue": "Wilayah perbatasan daratan dan lautan"},
    {"word": "sungai", "clue": "Aliran air tawar yang panjang di daratan"},
    {"word": "laut", "clue": "Kumpulan air asin yang sangat luas"},
    {"word": "pulau", "clue": "Daratan yang dikelilingi oleh air"},
    {"word": "hutan", "clue": "Wilayah luas yang ditumbuhi banyak pohon"},
    {"word": "langit", "clue": "Ruang luas di atas bumi"},
    {"word": "bintang", "clue": "Benda langit yang memancarkan cahaya sendiri"},
    {"word": "matahari", "clue": "Pusat tata surya kita"},
    {"word": "bulan", "clue": "Satelit alami bumi"},
    {"word": "awan", "clue": "Kumpulan uap air yang mengapung di langit"},
    {"word": "hujan", "clue": "Titik-titik air yang jatuh dari langit"},
    {"word": "pelangi", "clue": "Lengkungan warna di langit setelah hujan"},
    {"word": "desa", "clue": "Wilayah pemukiman di luar kota"},
    # Makanan & Buah
    {"word": "makanan", "clue": "Segala sesuatu yang dapat dimakan"},
    {"word": "minuman", "clue": "Segala sesuatu yang dapat diminum"},
    {"word": "apel", "clue": "Buah bulat berwarna merah atau hijau"},
    {"word": "jeruk", "clue": "Buah yang kaya vitamin C dan rasanya asam manis"},
    {"word": "mangga", "clue": "Buah musiman dengan daging berwarna kuning"},
    {"word": "pisang", "clue": "Buah lonjong berwarna kuning kesukaan monyet"},
    {"word": "semangka", "clue": "Buah besar dengan isi merah dan banyak air"},
    {"word": "nasi", "clue": "Makanan pokok orang Indonesia"},
    {"word": "sate", "clue": "Daging tusuk yang dibakar"},
    {"word": "bakso", "clue": "Bola daging yang disajikan dengan kuah"},
    {"word": "rendang", "clue": "Masakan daging berbumbu santan khas Minang"},
    {"word": "tempe", "clue": "Makanan khas Indonesia dari kedelai fermentasi"},
    {"word": "tahu", "clue": "Makanan dari endapan sari kedelai"},
    {"word": "durian", "clue": "Raja buah yang kulitnya berduri tajam"},
    {"word": "anggur", "clue": "Buah kecil bulat yang tumbuh merambat"},
    {"word": "melon", "clue": "Buah bulat besar dengan kulit bertekstur jala"},
    {"word": "kelapa", "clue": "Pohon yang semua bagiannya bermanfaat"},
    {"word": "cokelat", "clue": "Makanan manis dari biji kakao"},
    {"word": "susu", "clue": "Cairan bergizi tinggi dari sapi atau kambing"},
    {"word": "kopi", "clue": "Minuman berkafein dari biji yang dipanggang"},
    # Kata Kerja & Sifat
    {"word": "sekolah", "clue": "Tempat untuk menuntut ilmu"},
    {"word": "belajar", "clue": "Berusaha memperoleh kepandaian atau ilmu"},
    {"word": "pintar", "clue": "Pandai atau cerdas"},
    {"word": "cerdas", "clue": "Tajam pikiran dan cepat mengerti"},
    {"word": "bahagia", "clue": "Perasaan senang dan tenteram"},
    {"word": "semangat", "clue": "Kemauan atau gairah yang kuat"},
    {"word": "bekerja", "clue": "Melakukan suatu perbuatan untuk nafkah"},
    {"word": "bermain", "clue": "Melakukan sesuatu untuk bersenang-senang"},
    {"word": "tidur", "clue": "Mengistirahatkan badan dan kesadaran"},
    {"word": "lari", "clue": "Melangkah dengan kecepatan tinggi"},
    {"word": "senang", "clue": "Perasaan gembira"},
    {"word": "sedih", "clue": "Perasaan duka atau susah hati"},
    {"word": "marah", "clue": "Perasaan sangat tidak senang"},
    {"word": "takut", "clue": "Merasa gentar menghadapi sesuatu"},
    {"word": "berani", "clue": "Mempunyai hati yang mantap menghadapi bahaya"},
    {"word": "kuat", "clue": "Mempunyai tenaga besar"},
    {"word": "lemah", "clue": "Tidak mempunyai tenaga atau daya"},
    {"word": "cepat", "clue": "Dalam waktu singkat atau lari kencang"},
    {"word": "lambat", "clue": "Tidak cepat atau memerlukan waktu lama"},
    {"word": "tinggi", "clue": "Jauh jaraknya dari posisi bawah"},
    # Lain-lain
    {"word": "keluarga", "clue": "Satuan terkecil dalam masyarakat"},
    {"word": "teman", "clue": "Orang yang dikenal dan sering bergaul"},
    {"word": "sahabat", "clue": "Teman yang sangat dekat"},
    {"word": "cinta", "clue": "Perasaan kasih sayang yang kuat"},
    {"word": "mimpi", "clue": "Kejadian yang dialami saat tidur"},
    {"word": "cerita", "clue": "Tuturan yang membentangkan terjadinya hal"},
    {"word": "musik", "clue": "Seni menyusun bunyi atau suara"},
    {"word": "gambar", "clue": "Tiruan barang, orang, atau pemandangan"},
    {"word": "warna", "clue": "Kesan yang ditimbulkan oleh cahaya pada mata"},
    {"word": "angka", "clue": "Simbol yang digunakan untuk menghitung"},
    {"word": "hari", "clue": "Waktu selama 24 jam"},
    {"word": "minggu", "clue": "Jangka waktu tujuh hari"},
    {"word": "bulan", "clue": "Jangka waktu tiga puluh hari"},
    {"word": "tahun", "clue": "Jangka waktu dua belas bulan"},
    {"word": "waktu", "clue": "Seluruh rangkaian saat ketika proses berlangsung"},
    {"word": "dunia", "clue": "Bumi dengan segala isinya"},
    {"word": "negara", "clue": "Organisasi dalam suatu wilayah yang memiliki kekuasaan"},
    {"word": "pahlawan", "clue": "Orang yang menonjol karena keberaniannya"},
    {"word": "sejarah", "clue": "Kejadian dan peristiwa di masa lampau"},
    {"word": "budaya", "clue": "Hasil cipta, rasa, dan karsa manusia"},
    # Tambahan 100+ kata baru
    {"word": "kacamata", "clue": "Lensa tipis untuk mata untuk membantu penglihatan"},
    {"word": "topi", "clue": "Penutup kepala"},
    {"word": "sarung", "clue": "Kain panjang yang kedua ujungnya dijahit"},
    {"word": "jaket", "clue": "Baju luar yang tebal untuk menahan dingin"},
    {"word": "kaos", "clue": "Baju dari bahan katun yang santai"},
    {"word": "celana", "clue": "Pakaian untuk menutupi bagian pinggang ke bawah"},
    {"word": "sabun", "clue": "Bahan untuk membersihkan badan saat mandi"},
    {"word": "handuk", "clue": "Kain untuk mengeringkan badan setelah mandi"},
    {"word": "sisir", "clue": "Alat untuk merapikan rambut"},
    {"word": "pasta", "clue": "Cairan kental untuk membersihkan gigi"},
    {"word": "ember", "clue": "Wadah air berbentuk tabung dengan pegangan"},
    {"word": "gayung", "clue": "Alat untuk mengambil air dalam bak mandi"},
    {"word": "kasur", "clue": "Tempat tidur yang empuk"},
    {"word": "bantal", "clue": "Pengalas kepala saat tidur"},
    {"word": "guling", "clue": "Bantal panjang lonjong untuk dipeluk saat tidur"},
    {"word": "selimut", "clue": "Kain tebal pengamat badan saat tidur"},
    {"word": "sprei", "clue": "Kain pelapis kasur"},
    {"word": "piring", "clue": "Wadah makanan yang rata"},
    {"word": "sendok", "clue": "Alat untuk mengambil makanan"},
    {"word": "garpu", "clue": "Alat makan dengan ujung runcing"},
    {"word": "gelas", "clue": "Wadah air untuk minum"},
    {"word": "botol", "clue": "Wadah cairan dari kaca atau plastik dengan leher sempit"},
    {"word": "wajan", "clue": "Alat untuk menggoreng makanan"},
    {"word": "panci", "clue": "Alat untuk merebus air atau memasak sayur"},
    {"word": "pisau", "clue": "Alat tajam untuk memotong"},
    {"word": "parutan", "clue": "Alat untuk menghaluskan kelapa atau keju"},
    {"word": "kompor", "clue": "Alat untuk memasak yang mengeluarkan api"},
    {"word": "kulkas", "clue": "Lemari pendingin makanan"},
    {"word": "blender", "clue": "Alat elektronik untuk menghaluskan buah"},
    {"word": "setrika", "clue": "Alat untuk merapikan pakaian yang kusut"},
    {"word": "televisi", "clue": "Alat elektronik penampil gambar dan suara"},
    {"word": "radio", "clue": "Alat elektronik penyiar suara"},
    {"word": "kipas", "clue": "Alat untuk menggerakkan udara agar sejuk"},
    {"word": "telepon", "clue": "Alat komunikasi jarak jauh"},
    {"word": "kamera", "clue": "Alat untuk memotret"},
    {"word": "obeng", "clue": "Alat untuk memutar sekrup"},
    {"word": "palu", "clue": "Alat untuk memukul paku"},
    {"word": "gergaji", "clue": "Alat untuk memotong kayu atau besi"},
    {"word": "tang", "clue": "Alat untuk menjepit atau memotong kawat"},
    {"word": "sapu", "clue": "Alat untuk membersihkan lantai"},
    {"word": "pelan", "clue": "Alat untuk membersihkan lantai dengan air"},
    {"word": "kemoceng", "clue": "Alat pembersih debu dari bulu ayam"},
    {"word": "payung", "clue": "Pelindung dari hujan"},
    {"word": "koper", "clue": "Tas besar untuk bepergian jauh"},
    {"word": "dompet", "clue": "Tempat menyimpan uang"},
    {"word": "cermin", "clue": "Kaca bening yang memperlihatkan bayangan"},
    {"word": "sisir", "clue": "Alat perapi rambut"},
    {"word": "bedak", "clue": "Serbuk untuk kecantikan wajah"},
    {"word": "lipstik", "clue": "Pewarna bibir"},
    {"word": "parfum", "clue": "Cairan wangi untuk tubuh"},
    {"word": "gelang", "clue": "Perhiasan di pergelangan tangan"},
    {"word": "kalung", "clue": "Perhiasan di leher"},
    {"word": "cincin", "clue": "Perhiasan di jari tangan"},
    {"word": "anting", "clue": "Perhiasan di telinga"},
    {"word": "sepatu", "clue": "Alas kaki tertutup"},
    {"word": "sandal", "clue": "Alas kaki terbuka"},
    {"word": "kaos", "clue": "Pakaian kaki sebelum memakai sepatu"},
    {"word": "dasi", "clue": "Perhiasan leher pada kemeja"},
    {"word": "sabuk", "clue": "Ikat pinggang"},
    {"word": "topi", "clue": "Pelindung kepala dari panas"},
    {"word": "helm", "clue": "Pelindung kepala saat berkendara"},
    {"word": "masker", "clue": "Penutup hidung dan mulut"},
    {"word": "sarung", "clue": "Pelindung tangan dari panas atau dingin"},
    {"word": "jam", "clue": "Penunjuk waktu di tangan"},
    {"word": "pena", "clue": "Alat tulis bertinta"},
    {"word": "buku", "clue": "Media tulis dari kertas"},
    {"word": "penghapus", "clue": "Alat pembersih tulisan pensil"},
    {"word": "penggaris", "clue": "Alat untuk membuat garis lurus"},
    {"word": "map", "clue": "Wadah untuk menyimpan dokumen"},
    {"word": "lem", "clue": "Bahan perekat kertas"},
    {"word": "gunting", "clue": "Alat pemotong kertas atau kain"},
    {"word": "stapler", "clue": "Alat untuk menyatukan kertas"},
    {"word": "klip", "clue": "Penjepit kertas kecil"},
    {"word": "amplop", "clue": "Bungkus surat"},
    {"word": "perangko", "clue": "Bukti pembayaran biaya pos"},
    {"word": "tinta", "clue": "Cairan berwarna untuk menulis"},
    {"word": "kertas", "clue": "Lembaran untuk menulis"},
    {"word": "papan", "clue": "Media tulis besar di kelas"},
    {"word": "kapur", "clue": "Alat tulis untuk papan tulis hitam"},
    {"word": "spidol", "clue": "Alat tulis untuk papan tulis putih"},
    {"word": "bangku", "clue": "Tempat duduk panjang"},
    {"word": "meja", "clue": "Alas untuk menulis di sekolah"},
    {"word": "tas", "clue": "Wadah membawa buku sekolah"},
    {"word": "seragam", "clue": "Pakaian sekolah yang sama"},
    {"word": "bendera", "clue": "Lambang negara yang dikibarkan"},
    {"word": "guru", "clue": "Orang yang mengajar di sekolah"},
    {"word": "murid", "clue": "Orang yang belajar di sekolah"},
    {"word": "kelas", "clue": "Ruang belajar di sekolah"},
    {"word": "kantin", "clue": "Tempat jajan di sekolah"},
    {"word": "perpustakaan", "clue": "Tempat meminjam buku"},
    {"word": "lapangan", "clue": "Tempat berolahraga di sekolah"},
    {"word": "aula", "clue": "Ruang pertemuan besar"},
    {"word": "laboratorium", "clue": "Ruang praktik sains"},
    {"word": "kantor", "clue": "Ruang kerja administrasi"},
    {"word": "taman", "clue": "Tempat banyak bunga di sekolah"},
    {"word": "gerbang", "clue": "Pintu masuk halaman sekolah"},
    {"word": "satpam", "clue": "Penjaga keamanan sekolah"},
    {"word": "bel", "clue": "Penanda waktu masuk atau istirahat"},
    {"word": "upacara", "clue": "Kegiatan rutin Senin pagi di sekolah"},
    {"word": "pramuka", "clue": "Kegiatan kepanduan di sekolah"},
    {"word": "ujian", "clue": "Tes untuk mengukur kemampuan belajar"},
    {"word": "rapor", "clue": "Buku hasil belajar siswa"},
    {"word": "ijazah", "clue": "Surat tanda tamat belajar"},
    {"word": "wisuda", "clue": "Upacara kelulusan"},
    {"word": "bola", "clue": "Benda bulat untuk olahraga sepak"},
    {"word": "raket", "clue": "Alat pemukul bola bulu tangkis"},
    {"word": "net", "clue": "Jaring pembatas di tengah lapangan voli"},
    {"word": "gawang", "clue": "Tempat memasukkan bola sepak"},
    {"word": "ring", "clue": "Keranjang bola basket"},
    {"word": "kolam", "clue": "Tempat untuk olahraga renang"},
    {"word": "sepeda", "clue": "Kendaraan kayuh untuk olahraga"},
    {"word": "lomba", "clue": "Kegiatan kompetisi olahraga"},
    {"word": "juara", "clue": "Pemenang dalam kompetisi"},
    {"word": "medali", "clue": "Tanda penghargaan kemenangan"},
    {"word": "piala", "clue": "Trofi kemenangan"},
    {"word": "wasit", "clue": "Pemimpin pertandingan olahraga"},
    {"word": "pelatih", "clue": "Orang yang membimbing atlet"},
    {"word": "atlet", "clue": "Olahragawan profesional"},
    {"word": "suporter", "clue": "Pendukung tim olahraga"},
    {"word": "skor", "clue": "Angka perolehan dalam permainan"},
    {"word": "senam", "clue": "Gerakan badan untuk kesehatan"},
    {"word": "yoga", "clue": "Latihan pernapasan dan tubuh"},
    {"word": "lari", "clue": "Olahraga atletik paling dasar"},
    {"word": "lompat", "clue": "Gerakan mengangkat kaki ke atas"},
    {"word": "lempar", "clue": "Gerakan membuang benda jauh-jauh"},
    {"word": "tendang", "clue": "Gerakan memukul dengan kaki"},
    {"word": "pukul", "clue": "Gerakan menghantam dengan tangan"},
    {"word": "tangkis", "clue": "Gerakan menghalau serangan"},
    {"word": "smash", "clue": "Pukulan keras menukik dalam voli"},
    {"word": "servis", "clue": "Pukulan pertama dalam permainan voli"},
    {"word": "dribel", "clue": "Membawa bola dengan tangan di basket"},
    {"word": "kiper", "clue": "Penjaga gawang"},
    {"word": "bek", "clue": "Pemain bertahan dalam sepak bola"},
    {"word": "striker", "clue": "Penyerang dalam sepak bola"},
    {"word": "kapten", "clue": "Pemimpin tim di lapangan"},
    {"word": "peluit", "clue": "Alat bunyi yang ditiup wasit"},
    {"word": "matras", "clue": "Alas untuk olahraga gulat"},
    {"word": "sarung", "clue": "Alat pelindung tangan petinju"},
    {"word": "shuttlecock", "clue": "Bola bulu tangkis"},
    {"word": "papan", "clue": "Alat untuk olahraga seluncur"},
    {"word": "ombak", "clue": "Media untuk olahraga selancar"},
    {"word": "salju", "clue": "Media untuk olahraga ski"},
    {"word": "es", "clue": "Media untuk olahraga seluncur indah"},
    {"word": "mobil", "clue": "Kendaraan balap formula"},
    {"word": "motor", "clue": "Kendaraan balap motogp"},
    {"word": "helm", "clue": "Keamanan wajib pembalap"},
    {"word": "sirkuit", "clue": "Lintasan balap mobil atau motor"},
    {"word": "start", "clue": "Garis awal perlombaan"},
    {"word": "finish", "clue": "Garis akhir perlombaan"},
    {"word": "bendera", "clue": "Tanda akhir balapan kotak hitam putih"},
    {"word": "pitstop", "clue": "Tempat perbaikan kendaraan balap"},
    {"word": "mekanik", "clue": "Orang yang memperbaiki mesin balap"},
    {"word": "bensin", "clue": "Bahan bakar kendaraan"},
    {"word": "oli", "clue": "Pelumas mesin kendaraan"},
    {"word": "ban", "clue": "Karet bundar pada kendaraan"},
    {"word": "rem", "clue": "Alat untuk menghentikan laju kendaraan"},
    {"word": "gas", "clue": "Alat untuk mempercepat laju kendaraan"},
    {"word": "setir", "clue": "Alat pengemudi arah kendaraan"},
    {"word": "spion", "clue": "Kaca melihat ke belakang pada kendaraan"},
    {"word": "lampu", "clue": "Penerangan jalan saat malam hari"},
    {"word": "klakson", "clue": "Alat bunyi penanda keberadaan kendaraan"},
    {"word": "bagasi", "clue": "Tempat menyimpan barang di mobil"},
    {"word": "atap", "clue": "Penutup bagian atas kendaraan"},
    {"word": "jendela", "clue": "Kaca samping kendaraan"},
    {"word": "pintu", "clue": "Akses masuk ke dalam kendaraan"},
    {"word": "sabuk", "clue": "Pengaman penumpang di mobil"},
    {"word": "dashboard", "clue": "Panel instrumen di depan pengemudi"},
    {"word": "radiator", "clue": "Pendingin mesin kendaraan"},
    {"word": "aki", "clue": "Sumber listrik pada kendaraan"},
    {"word": "knalpot", "clue": "Saluran pembuangan gas mesin"},
    {"word": "piston", "clue": "Komponen penggerak dalam mesin"},
    {"word": "busi", "clue": "Pemantik api dalam mesin bensin"},
    {"word": "karburator", "clue": "Pencampur udara dan bahan bakar"},
    {"word": "transmisi", "clue": "Sistem pemindah tenaga mesin"},
    {"word": "kopling", "clue": "Pemutus hubungan mesin dan transmisi"},
    {"word": "pedal", "clue": "Tuas yang diinjak kaki di mobil"},
    {"word": "wiper", "clue": "Pembersih kaca mobil saat hujan"},
    {"word": "dongkrak", "clue": "Alat pengangkat mobil saat ganti ban"},
    {"word": "kunci", "clue": "Alat pembuka baut ban"},
    {"word": "pompa", "clue": "Alat pengisi angin pada ban"},
    {"word": "bengkel", "clue": "Tempat servis kendaraan"},
    {"word": "montir", "clue": "Tukang servis kendaraan"},
    {"word": "jalan", "clue": "Sarana transportasi darat"},
    {"word": "aspal", "clue": "Bahan pelapis permukaan jalan"},
    {"word": "trotoar", "clue": "Jalan khusus pejalan kaki"},
    {"word": "jembatan", "clue": "Penghubung jalan yang terputus sungai"},
    {"word": "terowongan", "clue": "Jalan di bawah tanah atau gunung"},
    {"word": "lampu", "clue": "Penanda lalu lintas merah kuning hijau"},
    {"word": "rambu", "clue": "Tanda peringatan di pinggir jalan"},
    {"word": "polisi", "clue": "Petugas pengatur lalu lintas"},
    {"word": "tilang", "clue": "Sanksi pelanggaran lalu lintas"},
    {"word": "sim", "clue": "Izin mengemudikan kendaraan"},
    {"word": "stnk", "clue": "Surat tanda nomor kendaraan"},
    {"word": "plat", "clue": "Nomor identitas kendaraan"},
    {"word": "macet", "clue": "Kondisi jalan yang sangat padat"},
    {"word": "parkir", "clue": "Tempat berhenti kendaraan"},
    {"word": "terminal", "clue": "Tempat pemberangkatan bus"},
    {"word": "stasiun", "clue": "Tempat pemberangkatan kereta api"},
    {"word": "bandara", "clue": "Tempat pemberangkatan pesawat"},
    {"word": "pelabuhan", "clue": "Tempat pemberangkatan kapal laut"},
    {"word": "tiket", "clue": "Bukti pembayaran jasa transportasi"},
    {"word": "penumpang", "clue": "Orang yang naik kendaraan umum"},
    {"word": "sopir", "clue": "Pengemudi bus atau mobil"},
    {"word": "masinis", "clue": "Pengemudi kereta api"},
    {"word": "pilot", "clue": "Pengemudi pesawat terbang"},
    {"word": "nakhoda", "clue": "Pengemudi kapal laut"},
    {"word": "pramugari", "clue": "Pelayan penumpang di pesawat"},
    {"word": "kondektur", "clue": "Penarik tiket di bus atau kereta"},
    {"word": "navigasi", "clue": "Penentu arah perjalanan"},
    {"word": "peta", "clue": "Gambaran wilayah untuk navigasi"},
    {"word": "kompas", "clue": "Alat penunjuk arah mata angin"},
    {"word": "gps", "clue": "Sistem navigasi berbasis satelit"},
    {"word": "tujuan", "clue": "Tempat akhir perjalanan"},
    {"word": "asal", "clue": "Tempat awal perjalanan"},
    {"word": "transit", "clue": "Pemberhentian sementara dalam perjalanan"},
    {"word": "delay", "clue": "Keterlambatan keberangkatan"},
    {"word": "bagasi", "clue": "Barang bawaan penumpang"},
    {"word": "paspor", "clue": "Identitas diri untuk ke luar negeri"},
    {"word": "visa", "clue": "Izin masuk ke suatu negara"},
    {"word": "imigrasi", "clue": "Pemeriksaan dokumen di perbatasan"},
    {"word": "beacukai", "clue": "Pemeriksaan barang bawaan dari luar negeri"},
    {"word": "valas", "clue": "Mata uang asing"},
    {"word": "kurs", "clue": "Nilai tukar mata uang"},
    {"word": "turis", "clue": "Orang yang sedang berwisata"},
    {"word": "hotel", "clue": "Tempat menginap saat wisata"},
    {"word": "villa", "clue": "Rumah peristirahatan di pegunungan"},
    {"word": "pantai", "clue": "Destinasi wisata tepi laut"},
    {"word": "gunung", "clue": "Destinasi wisata pendakian"},
    {"word": "museum", "clue": "Tempat menyimpan benda bersejarah"},
    {"word": "kebun", "clue": "Tempat melihat berbagai hewan"},
    {"word": "candhi", "clue": "Bangunan kuno tempat ibadah zaman dahulu"},
    {"word": "curug", "clue": "Air terjun dalam bahasa sunda"},
    {"word": "gua", "clue": "Lubang alami di perut bumi"},
    {"word": "waduk", "clue": "Bendungan air buatan manusia"},
    {"word": "alun", "clue": "Lapangan luas di tengah kota"},
    {"word": "pasar", "clue": "Tempat transaksi jual beli"},
    {"word": "mall", "clue": "Pusat perbelanjaan modern"},
    {"word": "swalayan", "clue": "Toko yang melayani diri sendiri"},
    {"word": "warung", "clue": "Toko kecil di pinggir jalan"},
    {"word": "toko", "clue": "Tempat menjual barang tertentu"},
    {"word": "harga", "clue": "Nilai uang dari suatu barang"},
    {"word": "diskon", "clue": "Potongan harga barang"},
    {"word": "murah", "clue": "Harga yang rendah"},
    {"word": "mahal", "clue": "Harga yang tinggi"},
    {"word": "bayar", "clue": "Kegiatan memberikan uang untuk barang"},
    {"word": "tunai", "clue": "Pembayaran dengan uang kertas atau logam"},
    {"word": "debit", "clue": "Pembayaran dengan kartu bank"},
    {"word": "kredit", "clue": "Pembayaran dengan cicilan"},
    {"word": "struk", "clue": "Bukti pembayaran belanja"},
    {"word": "kasir", "clue": "Orang yang melayani pembayaran"},
    {"word": "dompet", "clue": "Tempat menyimpan uang kertas"},
    {"word": "celengan", "clue": "Tempat menabung uang receh"},
    {"word": "bank", "clue": "Lembaga keuangan tempat menabung"},
    {"word": "atm", "clue": "Mesin untuk mengambil uang tunai"},
    {"word": "saham", "clue": "Bukti kepemilikan nilai perusahaan"},
    {"word": "emas", "clue": "Logam mulia untuk investasi"},
    {"word": "tanah", "clue": "Properti dalam bentuk lahan"},
    {"word": "rumah", "clue": "Properti tempat tinggal"},
    {"word": "pajak", "clue": "Iuran wajib kepada negara"},
    {"word": "inflasi", "clue": "Kenaikan harga barang secara umum"},
    {"word": "ekonomi", "clue": "Sistem pengelolaan sumber daya dan uang"}
]

def scramble_word(word):
    l = list(word)
    random.shuffle(l)
    res = "".join(l)
    if res == word and len(word) > 1:
        return scramble_word(word)
    return res

@bot.message_handler(commands=['roulette', 'dor'])
async def roulette_start(message):
    chat_id = message.chat.id
    if chat_id in roulette_games:
        return await safe_reply(message, "Game sudah berjalan! Tarik pelatuknya!")

    bullet = random.randint(1, 6)
    roulette_games[chat_id] = {
        "slots": 6,
        "bullet": bullet,
        "status": "active"
    }
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Tarik Pelatuk 🔫", callback_data=f"roulette_fire_{chat_id}"))
    
    msg = (
        "🔫 *RUSSIAN ROULETTE*\n\n"
        "Ada 6 slot di revolver ini, 1 berisi peluru tajam.\n"
        "Siapa yang berani menarik pelatuknya?\n\n"
        "Slot tersedia: 6"
    )
    await bot.send_message(chat_id, msg, parse_mode='Markdown', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('roulette_'))
async def roulette_callback(call):
    data = call.data.split('_')
    action = data[1]
    chat_id = int(data[2])

    if chat_id not in roulette_games:
        return await bot.answer_callback_query(call.id, "Game sudah selesai.")

    game = roulette_games[chat_id]
    user_name = call.from_user.first_name

    if action == 'fire':
        current_slot = random.randint(1, game['slots'])
        
        if current_slot == 1:
            # PENALTY
            user_data = db.get_user(call.from_user.id)
            user_data["coins"] = max(0, user_data.get("coins", 0) - 50)
            db.update_user(call.from_user.id, user_data)
            
            msg = f"💥 *BOOOOOOOMM!*\n\n{user_name} menarik pelatuk dan kepalanya meledak! 💀\nGame Berakhir. (💸 Kehilangan 50 koin)"
            await bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=None)
            del roulette_games[chat_id]
            await bot.answer_callback_query(call.id, "💀 BOOM!")
        else:
            game['slots'] -= 1
            if game['slots'] <= 1:
                 msg = f"🔫 *KLIK!* (Aman)\n\n{user_name} selamat. Slot tersisa tinggal 1, dan itu pasti peluru tajam! 😱\nGame Berakhir."
                 await bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=None)
                 del roulette_games[chat_id]
            else:
                 msg = (
                    "🔫 *RUSSIAN ROULETTE*\n\n"
                    f"*{user_name}* menarik pelatuk... *KLIK!* Aman.\n\n"
                    f"Slot tersisa: {game['slots']}"
                 )
                 await bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=call.message.reply_markup)
            
            await bot.answer_callback_query(call.id, "😅 Aman...")

@bot.message_handler(commands=['tebakkata', 'susunkata'])
async def tebak_kata_start(message):
    chat_id = message.chat.id
    if chat_id in tebak_kata_games:
        game = tebak_kata_games[chat_id]
        return await safe_reply(message, f"Game sudah berjalan!\n\n🧩 *{game['scrambled']}*\n💡 Clue: {game['clue']}", parse_mode='Markdown')

    item = random.choice(WORD_LIST)
    word = item['word']
    clue = item['clue']
    scrambled = scramble_word(word)
    
    tebak_kata_games[chat_id] = {
        "word": word,
        "clue": clue,
        "scrambled": scrambled
    }
    
    msg = (
        "🧩 *TEBAK KATA (SUSUN KATA)*\n\n"
        f"Susun kata ini: *{scrambled.upper()}*\n"
        f"💡 Clue: Mikir sendiri\n\n"
        "Waktu: 60 detik!\n"
        "Ketik jawabanmu langsung di chat!"
    )
    await bot.send_message(chat_id, msg, parse_mode='Markdown')
    
    asyncio.create_task(tebak_kata_timeout(chat_id, word))

async def tebak_kata_timeout(chat_id, word):
    await asyncio.sleep(60)
    if chat_id in tebak_kata_games and tebak_kata_games[chat_id]['word'] == word:
        game = tebak_kata_games[chat_id]
        del tebak_kata_games[chat_id]
        await bot.send_message(chat_id, f"⏰ *WAKTU HABIS!*\n\nJawaban yang benar adalah: *{word.upper()}*", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.chat.id in tebak_kata_games and m.text and not m.text.startswith('/'))
async def handle_tebak_kata_answer(message):
    chat_id = message.chat.id
    
    if chat_id not in tebak_kata_games:
        return
        
    game = tebak_kata_games[chat_id]
    
    words = message.text.lower().split()
    if game['word'].lower() in words:
        user_name = message.from_user.first_name
        user_id = message.from_user.id
        
        # ECONOMY
        user_data = db.get_user(user_id)
        user_data["coins"] = user_data.get("coins", 0) + 10
        user_data["xp"] = user_data.get("xp", 0) + 50
        db.update_user(user_id, user_data)
        
        msg = f"🎉 *SELAMAT!* {user_name} menebak dengan benar!\n\nJawaban: *{game['word'].upper()}*\n🎁 Hadiah: +10 Koin & +50 XP"
        await safe_reply(message, msg, parse_mode='Markdown')
        del tebak_kata_games[chat_id]

def get_ttt_keyboard(board, game_id):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i in range(9):
        text = board[i] if board[i] else " "
        buttons.append(types.InlineKeyboardButton(text, callback_data=f"ttt_move_{game_id}_{i}"))
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['tictactoe', 'ttt'])
async def ttt_start(message):
    chat_id = message.chat.id
    if chat_id in active_games and active_games[chat_id]['status'] != 'finished':
        return await safe_reply(message, "Game sedang berjalan di grup ini!")

    active_games[chat_id] = {
        "players": [],
        "board": [""] * 9,
        "turn": 0,
        "status": "waiting",
        "msg_id": None,
        "names": []
    }

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Gabung Game", callback_data=f"ttt_join_{chat_id}"))
    
    msg = await bot.send_message(chat_id, "🎮 *TIC TAC TOE*\n\nMenunggu pemain bergabung (0/2)...", 
                               reply_to_message_id=message.message_id, parse_mode='Markdown', reply_markup=keyboard)
    active_games[chat_id]['msg_id'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data.startswith('ttt_'))
async def ttt_callback(call):
    data = call.data.split('_')
    action = data[1]
    chat_id = int(data[2])

    if chat_id not in active_games:
        return await bot.answer_callback_query(call.id, "Game sudah kadaluarsa.")

    game = active_games[chat_id]

    if action == 'join':
        user_id = call.from_user.id
        user_name = call.from_user.first_name

        if user_id in game['players']:
            return await bot.answer_callback_query(call.id, "Kamu sudah bergabung!")
        
        if len(game['players']) >= 2:
            return await bot.answer_callback_query(call.id, "Game sudah penuh.")

        game['players'].append(user_id)
        game['names'].append(user_name)
        
        count = len(game['players'])
        if count == 1:
            await bot.edit_message_text(f"🎮 *TIC TAC TOE*\n\nMenunggu pemain bergabung (1/2)...\n1. {user_name}", 
                                      chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=call.message.reply_markup)
            await bot.answer_callback_query(call.id, "Berhasil bergabung!")
        else:
            game['status'] = 'playing'
            if random.choice([True, False]):
                game['players'].reverse()
                game['names'].reverse()
            
            p1, p2 = game['names']
            msg = f"🎮 *GAME DIMULAI!*\n\n❌: {p1}\n⭕: {p2}\n\nGiliran: {p1}"
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', 
                                      reply_markup=get_ttt_keyboard(game['board'], chat_id))
            await bot.answer_callback_query(call.id, "Game dimulai!")

    elif action == 'move':
        user_id = call.from_user.id
        index = int(data[3])

        if game['status'] != 'playing':
            return await bot.answer_callback_query(call.id, "Game belum dimulai atau sudah selesai.")

        if user_id not in game['players']:
            return await bot.answer_callback_query(call.id, "Kamu bukan pemain di game ini!")

        current_player_idx = game['turn'] % 2
        if user_id != game['players'][current_player_idx]:
            return await bot.answer_callback_query(call.id, "Bukan giliranmu!")

        if game['board'][index] != "":
            return await bot.answer_callback_query(call.id, "Kotak sudah terisi!")

        symbol = "❌" if current_player_idx == 0 else "⭕"
        game['board'][index] = symbol
        game['turn'] += 1

        winner_idx = check_winner(game['board'])
        if winner_idx is not None:
            game['status'] = 'finished'
            winner_name = game['names'][winner_idx]
            winner_id = game['players'][winner_idx]
            
            loser_idx = 1 - winner_idx
            loser_id = game['players'][loser_idx]
            
            # ECONOMY - Winner
            user_data = db.get_user(winner_id)
            user_data["coins"] = user_data.get("coins", 0) + 20
            user_data["xp"] = user_data.get("xp", 0) + 100
            db.update_user(winner_id, user_data)
            
            # ECONOMY - Loser
            loser_data = db.get_user(loser_id)
            loser_data["coins"] = max(0, loser_data.get("coins", 0) - 20)
            db.update_user(loser_id, loser_data)
            
            msg = f"🎮 *GAME SELESAI!*\n\n🏆 Pemenang: {winner_name} (+20 koin)\n💀 Pecundang: {game['names'][loser_idx]} (-20 koin)\n\n" + render_board_text(game['board'])
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=None)
            del active_games[chat_id]
        elif "" not in game['board']:
            game['status'] = 'finished'
            msg = "🎮 *GAME SELESAI!*\n\n🤝 Hasil: Seri!\n\n" + render_board_text(game['board'])
            await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', reply_markup=None)
            del active_games[chat_id]
        else:
            next_player_idx = game['turn'] % 2
            next_name = game['names'][next_player_idx]
            p1, p2 = game['names']
            msg = f"🎮 *TIC TAC TOE*\n\n❌: {p1}\n⭕: {p2}\n\nGiliran: {next_name}"
            try:
                await bot.edit_message_text(msg, chat_id, game['msg_id'], parse_mode='Markdown', 
                                          reply_markup=get_ttt_keyboard(game['board'], chat_id))
            except Exception as e:
                if "message is not modified" not in str(e).lower():
                    logging.error(f"TTT Move Error: {e}")
        
        await bot.answer_callback_query(call.id)

def check_winner(b):
    win_coords = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    for c in win_coords:
        if b[c[0]] == b[c[1]] == b[c[2]] != "":
            return 0 if b[c[0]] == "❌" else 1
    return None

def render_board_text(b):
    res = ""
    for i in range(0, 9, 3):
        row = [b[j] if b[j] else "⬜" for j in range(i, i+3)]
        res += "".join(row) + "\n"
    return res.strip()


@bot.message_handler(commands=['stopttt'])
async def stop_ttt(message):
    chat_id = message.chat.id
    if chat_id in active_games:
        del active_games[chat_id]
        await safe_reply(message, "Game Tic Tac Toe telah dihentikan.")
    else:
        await safe_reply(message, "Tidak ada game Tic Tac Toe yang berjalan.")

@bot.message_handler(commands=['stoptebak'])
async def stop_tebak(message):
    chat_id = message.chat.id
    if chat_id in tebak_kata_games:
        del tebak_kata_games[chat_id]
        await safe_reply(message, "Game Tebak Kata telah dihentikan.")
    else:
        await safe_reply(message, "Tidak ada game Tebak Kata yang berjalan.")

@bot.message_handler(commands=['stoproulette'])
async def stop_roulette(message):
    chat_id = message.chat.id
    if chat_id in roulette_games:
        del roulette_games[chat_id]
        await safe_reply(message, "Sesi Russian Roulette telah dihentikan.")
    else:
        await safe_reply(message, "Tidak ada sesi Roulette yang berjalan.")
