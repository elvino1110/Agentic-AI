# Import necessary libraries
import sqlite3
from datetime import datetime
from langchain_community.vectorstores import Qdrant
import os


class BroomBotDatabase:
    """Database handler for BroomBot motorcycle service booking system."""

    def __init__(self, db_name: str = "broombot.sqlite"):
        """
        Initialize the BroomBot Database.

        Args:
            db_name: Name of the SQLite database file (default: "broombot.sqlite")
        """
        # Get the path to the same folder as this file (broom-bot folder)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_name = os.path.join(current_dir, db_name)
        self.create_table()

    def create_table(self):
        """Create necessary database tables if they don't exist."""
        # Connect to SQLite database (it will create the file if it doesn't exist)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Create 'dealers' table
        create_table_dealers = '''
            CREATE TABLE IF NOT EXISTS DEALERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                post_code INTEGER NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                province TEXT NOT NULL,
                city TEXT NOT NULL,
                district TEXT NOT NULL,
                village TEXT NOT NULL,
                latitude TEXT NOT NULL,
                longitude TEXT NOT NULL
            )
        '''
        cursor.execute(create_table_dealers)
        conn.commit()

        # Create 'techincians' table
        create_table_technicians = '''
            CREATE TABLE IF NOT EXISTS TECHNICIANS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                id_dealer INTEGER NOT NULL,
                FOREIGN KEY (id_dealer) REFERENCES DEALERS(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
        '''
        cursor.execute(create_table_technicians)
        conn.commit()

        # Create 'bookings' table
        create_table_boookings = '''
            CREATE TABLE IF NOT EXISTS BOOKINGS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_code TEXT UNIQUE,
                customer_name TEXT NOT NULL,
                customer_plate_number TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                status TEXT NOT NULL,
                id_technician INTEGER NOT NULL,
                id_dealer INTEGER NOT NULL,
                FOREIGN KEY (id_technician) REFERENCES TECHNICIANS(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE,
                FOREIGN KEY (id_dealer) REFERENCES DEALERS(id)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE
            )
        '''
        cursor.execute(create_table_boookings)
        conn.commit()

        conn.close()

        print("Table created")

    def insert_dealer(self, name, address, post_code, phone, service, province, city, district, village, latitude, longitude):
        """Insert a new dealer into the database."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        insert_dealer_sql = 'INSERT INTO dealers (name, address, post_code, phone, service, province, city, district, village, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cursor.execute(insert_dealer_sql, (name, address, post_code, phone, service, province, city, district, village, latitude, longitude))
        connection.commit()
        connection.close()
        print("Dealer successfully added")

    def insert_technician(self, name, status, id_dealer):
        """Insert a new technician into the database."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Enable foreign key constraint
        connection.execute("PRAGMA foreign_keys = ON")
        insert_dealers_sql = 'INSERT INTO technicians (name, status, id_dealer) VALUES (?, ?, ?)'
        cursor.execute(insert_dealers_sql, (name, status, id_dealer,))
        connection.commit()
        connection.close()
        print("Technician successfully added")

    def insert_booking(self, customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer):
        """Insert a new booking into the database."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Enable foreign key constraint
        connection.execute("PRAGMA foreign_keys = ON")
        insert_booking_sql = 'INSERT INTO bookings (customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer) VALUES (?, ?, ?, ?, ?, ?, ?)'
        cursor.execute(insert_booking_sql, (customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer))
        booking_id = cursor.lastrowid
        booking_code = self.generate_booking_code(customer_plate_number, booking_id)
        cursor.execute("UPDATE bookings SET booking_code = ? WHERE id = ?", (booking_code, booking_id,))
        connection.commit()
        connection.close()
        print(f"Booking successfully added with booking code {booking_code}")
        return f"Booking successfully added with booking code {booking_code}"

    def insert_booking_from_tool(self, customer_name, customer_plate_number, technician_name, dealer_name, start_time, end_time):
        """Insert a booking from tool with dealer and technician names."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Cari dealer_id berdasarkan nama dealer
        id_dealer = self.get_dealer_id_by_name(dealer_name)

        if not id_dealer:
            return f"Dealer '{dealer_name}' not found"

        # Cari id_technician
        id_technician = self.get_technician_id_by_name(id_dealer, technician_name)

        if not id_technician:
            return f"Technician '{technician_name}' not found"

        # Enable foreign key constraint
        connection.execute("PRAGMA foreign_keys = ON")
        insert_booking_sql = 'INSERT INTO bookings (customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer) VALUES (?, ?, ?, ?, ?, ?, ?)'
        status = "Scheduled"
        cursor.execute(insert_booking_sql, (customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer))
        booking_id = cursor.lastrowid
        booking_code = self.generate_booking_code(customer_plate_number, booking_id)
        cursor.execute("UPDATE bookings SET booking_code = ? WHERE id = ?", (booking_code, booking_id,))
        connection.commit()
        connection.close()
        print(f"Booking successfully added with booking code {booking_code}")
        return f"Booking successfully added with booking code {booking_code}"

    def get_dealer_id_by_name(self, dealer_name):
        """Get dealer ID by dealer name."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Query untuk mencari dealer_id berdasarkan nama dealer
        cursor.execute("SELECT id FROM DEALERS WHERE name = ?", (dealer_name,))
        dealer_id = cursor.fetchone()

        conn.close()

        if dealer_id:
            return dealer_id[0]
        else:
            return None  # Jika dealer tidak ditemukan

    def get_technician_id_by_name(self, id_dealer, technician_name):
        """Get technician ID by name and dealer ID."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Query untuk mencari dealer_id berdasarkan nama dealer
        cursor.execute("SELECT id FROM TECHNICIANS WHERE name = ? AND id_dealer = ?", (technician_name, id_dealer,))
        technician_id = cursor.fetchone()

        conn.close()

        if technician_id:
            return technician_id[0]
        else:
            return None  # Jika dealer tidak ditemukan

    def check_available_technicians(self, dealer_name, start_time, end_time):
        """Check available technicians for a given time slot."""
        # Cari dealer_id berdasarkan nama dealer
        dealer_id = self.get_dealer_id_by_name(dealer_name)

        if not dealer_id:
            return f"Dealer '{dealer_name}' not found"

        # Konversi waktu string ke format datetime
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        # Koneksi ke database SQLite
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Query untuk mencari teknisi yang tidak terjadwal pada waktu yang dipilih
        query = '''
            SELECT t.id, t.name
            FROM TECHNICIANS t
            WHERE t.id NOT IN (
                SELECT b.id_technician
                FROM BOOKINGS b
                WHERE b.id_dealer = ?
                AND (
                    (b.start_time < ? AND b.end_time > ?)   -- Tumpang tindih 1: Booking dimulai sebelum dan berakhir setelah
                    OR (b.start_time < ? AND b.end_time > ?) -- Tumpang tindih 2: Booking dimulai sebelum dan berakhir setelah
                    OR (b.start_time >= ? AND b.end_time <= ?) -- Tumpang tindih 3: Booking dimulai dan berakhir di dalam rentang waktu
                    OR (b.start_time <= ? AND b.end_time >= ?)   -- Tumpang tindih 4: Booking dimulai sebelum dan berakhir di dalam rentang waktu
                )
            )
        '''

        # Eksekusi query untuk mencari teknisi yang tersedia
        cursor.execute(query, (dealer_id, start_time, start_time, end_time, end_time, start_time, end_time, start_time, end_time))
        available_technicians = cursor.fetchall()

        conn.close()

        # Menyusun hasil dalam satu teks
        if available_technicians:
            technician_names = [technician[1] for technician in available_technicians]
            return "Available Technicians: " + ", ".join(technician_names)  # Gabungkan nama teknisi dalam satu teks
        else:
            return "No technicians available"  # Tidak ada teknisi yang tersedia

    def get_booking(self, booking_code):
        """Get booking details by booking code."""
        # booking code upper
        booking_code = booking_code.upper()

        # Koneksi ke database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Query untuk mendapatkan booking terbaru berdasarkan parameter dengan case-insensitive comparison
        query = '''
            SELECT id, customer_name, customer_plate_number, start_time, end_time, status, id_technician, id_dealer, booking_code
            FROM BOOKINGS
            WHERE UPPER(booking_code) = ?
            ORDER BY id DESC
            LIMIT 1
        '''

        # Eksekusi query
        cursor.execute(query, (booking_code,))
        booking = cursor.fetchone()

        conn.close()

        # Return hasil booking
        if booking:
            return {
                "id": booking[0],
                "customer_name": booking[1],
                "customer_plate_number": booking[2],
                "start_time": booking[3],
                "end_time": booking[4],
                "status": booking[5],
                "id_technician": booking[6],
                "id_dealer": booking[7],
            }
        else:
            return "No booking found"

    def drop_all_tables(self):
        """Drop all tables from the database."""
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        # Menjalankan perintah DROP TABLE untuk setiap tabel
        cursor.execute("DROP TABLE IF EXISTS BOOKINGS")
        cursor.execute("DROP TABLE IF EXISTS TECHNICIANS")
        cursor.execute("DROP TABLE IF EXISTS DEALERS")

        connection.commit()
        connection.close()

        print("All tables have been dropped.")

    @staticmethod
    def int_to_base36(num):
        """Convert integer to base36 string."""
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        base36 = ''
        while num > 0:
            num, i = divmod(num, 36)
            base36 = chars[i] + base36
        return base36 or '0'

    @staticmethod
    def sanitize_plate(plate_number):
        """Sanitize plate number by removing spaces and special characters."""
        # Hapus spasi dan karakter asing, kapital semua
        return ''.join(filter(str.isalnum, plate_number)).upper()

    def generate_booking_code(self, plate_number, id_booking):
        """Generate a unique booking code."""
        prefix = "BRMB"
        tanggal = datetime.now().strftime("%m%d")  # Misal: 0801
        plate = self.sanitize_plate(plate_number)
        base36_id = self.int_to_base36(id_booking)

        return f"{prefix}-{tanggal}-{plate}-{base36_id}"


# For backward compatibility and initialization
if __name__ == "__main__":
    db = BroomBotDatabase()

    # Insert sample data
    db.insert_dealer("Herry Motorindo Mandiri", "JL. NARASINGA NO. 9 A-B", 29312, "0811769667", "bengkel-dan-penjualan", "Riau", "Kabupaten Indragiri Hulu", "Rengat", "Pematang Kandis", "-0.371135", " 102.543393")
    db.insert_dealer("Cv Herry Motorindo Mandiri", "JL. LINTAS TIMUR RT.001 RW.01", 29351, "085271123295", "bengkel-dan-penjualan", "Riau", "Kabupaten Indragiri Hulu", "Rengat Barat", "Pematang Reba", "-0.392028", " 102.442611")
    db.insert_technician("John Doe", "Available", 1)
    db.insert_technician("Jane Smith", "Available", 1)
    db.insert_technician("Robert Brown", "Available", 1)
    db.insert_technician("Dominic Parker", "Available", 1)
    db.insert_technician("Harry Larry", "Available", 1)
