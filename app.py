from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saw_karyawan_new.db'
db = SQLAlchemy(app)

# Models
class Karyawan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    nilai = db.relationship('NilaiKaryawan', backref='karyawan', lazy=True)

class Kriteria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    bobot = db.Column(db.Float, nullable=False)
    jenis = db.Column(db.String(10), nullable=False)  # 'benefit' or 'cost'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    nilai = db.relationship('NilaiKaryawan', backref='kriteria', lazy=True)

class NilaiKaryawan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    karyawan_id = db.Column(db.Integer, db.ForeignKey('karyawan.id'), nullable=False)
    kriteria_id = db.Column(db.Integer, db.ForeignKey('kriteria.id'), nullable=False)
    nilai = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    total_karyawan = Karyawan.query.count()
    total_kriteria = Kriteria.query.count()
    total_nilai = NilaiKaryawan.query.count()
    return render_template('index.html', 
                         total_karyawan=total_karyawan,
                         total_kriteria=total_kriteria,
                         total_nilai=total_nilai)

@app.route('/karyawan')
def karyawan():
    karyawan_list = Karyawan.query.all()
    return render_template('karyawan.html', karyawan_list=karyawan_list)

@app.route('/karyawan/tambah', methods=['GET', 'POST'])
def tambah_karyawan():
    if request.method == 'POST':
        nama = request.form['nama']
        karyawan = Karyawan(nama=nama)
        db.session.add(karyawan)
        db.session.commit()
        flash('Karyawan berhasil ditambahkan!', 'success')
        return redirect(url_for('karyawan'))
    return render_template('tambah_karyawan.html')

@app.route('/karyawan/edit/<int:id>', methods=['GET', 'POST'])
def edit_karyawan(id):
    karyawan = Karyawan.query.get_or_404(id)
    if request.method == 'POST':
        karyawan.nama = request.form['nama']
        db.session.commit()
        flash('Karyawan berhasil diperbarui!', 'success')
        return redirect(url_for('karyawan'))
    return render_template('edit_karyawan.html', karyawan=karyawan)

@app.route('/karyawan/hapus/<int:id>')
def hapus_karyawan(id):
    karyawan = Karyawan.query.get_or_404(id)
    # Hapus semua nilai karyawan terkait
    NilaiKaryawan.query.filter_by(karyawan_id=id).delete()
    db.session.delete(karyawan)
    db.session.commit()
    flash('Karyawan berhasil dihapus!', 'success')
    return redirect(url_for('karyawan'))

@app.route('/kriteria')
def kriteria():
    kriteria_list = Kriteria.query.all()
    return render_template('kriteria.html', kriteria_list=kriteria_list)

@app.route('/kriteria/tambah', methods=['GET', 'POST'])
def tambah_kriteria():
    if request.method == 'POST':
        nama = request.form['nama']
        bobot = float(request.form['bobot'])
        jenis = request.form['jenis']
        kriteria = Kriteria(nama=nama, bobot=bobot, jenis=jenis)
        db.session.add(kriteria)
        db.session.commit()
        flash('Kriteria berhasil ditambahkan!', 'success')
        return redirect(url_for('kriteria'))
    return render_template('tambah_kriteria.html')

@app.route('/kriteria/edit/<int:id>', methods=['GET', 'POST'])
def edit_kriteria(id):
    kriteria = Kriteria.query.get_or_404(id)
    if request.method == 'POST':
        kriteria.nama = request.form['nama']
        kriteria.bobot = float(request.form['bobot'])
        kriteria.jenis = request.form['jenis']
        db.session.commit()
        flash('Kriteria berhasil diperbarui!', 'success')
        return redirect(url_for('kriteria'))
    return render_template('edit_kriteria.html', kriteria=kriteria)

@app.route('/kriteria/hapus/<int:id>')
def hapus_kriteria(id):
    kriteria = Kriteria.query.get_or_404(id)
    # Hapus semua nilai terkait kriteria
    NilaiKaryawan.query.filter_by(kriteria_id=id).delete()
    db.session.delete(kriteria)
    db.session.commit()
    flash('Kriteria berhasil dihapus!', 'success')
    return redirect(url_for('kriteria'))

@app.route('/penilaian')
def penilaian():
    karyawan_list = Karyawan.query.all()
    kriteria_list = Kriteria.query.all()
    nilai_list = NilaiKaryawan.query.all()
    
    # Kelompokkan nilai berdasarkan karyawan
    nilai_per_karyawan = {}
    for nilai in nilai_list:
        if nilai.karyawan_id not in nilai_per_karyawan:
            nilai_per_karyawan[nilai.karyawan_id] = []
        nilai_per_karyawan[nilai.karyawan_id].append(nilai)
    
    return render_template('penilaian.html', 
                         karyawan_list=karyawan_list,
                         kriteria_list=kriteria_list,
                         nilai_per_karyawan=nilai_per_karyawan)

@app.route('/penilaian/tambah', methods=['POST'])
def tambah_penilaian():
    karyawan_id = request.form['karyawan_id']
    kriteria_ids = [
        request.form['kriteria1'],
        request.form['kriteria2'],
        request.form['kriteria3']
    ]
    nilai_list = [
        float(request.form['nilai1']),
        float(request.form['nilai2']),
        float(request.form['nilai3'])
    ]
    
    # Hapus penilaian lama untuk karyawan ini
    NilaiKaryawan.query.filter_by(karyawan_id=karyawan_id).delete()
    
    # Tambah penilaian baru
    for kriteria_id, nilai in zip(kriteria_ids, nilai_list):
        penilaian = NilaiKaryawan(
            karyawan_id=karyawan_id,
            kriteria_id=kriteria_id,
            nilai=nilai
        )
        db.session.add(penilaian)
    
    db.session.commit()
    flash('Penilaian berhasil ditambahkan!', 'success')
    return redirect(url_for('penilaian'))

@app.route('/penilaian/edit/<int:karyawan_id>', methods=['GET', 'POST'])
def edit_penilaian(karyawan_id):
    karyawan = Karyawan.query.get_or_404(karyawan_id)
    kriteria_list = Kriteria.query.all()
    
    if request.method == 'POST':
        kriteria_id = request.form['kriteria_id']
        nilai = float(request.form['nilai'])
        
        # Cek apakah penilaian sudah ada
        existing_nilai = NilaiKaryawan.query.filter_by(
            karyawan_id=karyawan_id,
            kriteria_id=kriteria_id
        ).first()
        
        if existing_nilai:
            existing_nilai.nilai = nilai
        else:
            penilaian = NilaiKaryawan(
                karyawan_id=karyawan_id,
                kriteria_id=kriteria_id,
                nilai=nilai
            )
            db.session.add(penilaian)
        
        db.session.commit()
        flash('Penilaian berhasil diperbarui!', 'success')
        return redirect(url_for('penilaian'))
    
    # Ambil nilai yang sudah ada
    nilai_dict = {}
    nilai_list = NilaiKaryawan.query.filter_by(karyawan_id=karyawan_id).all()
    for nilai in nilai_list:
        nilai_dict[nilai.kriteria_id] = nilai.nilai
    
    return render_template('edit_penilaian.html', 
                         karyawan=karyawan,
                         kriteria_list=kriteria_list,
                         nilai_dict=nilai_dict)

@app.route('/penilaian/hapus/<int:karyawan_id>')
def hapus_penilaian(karyawan_id):
    # Hapus semua nilai untuk karyawan ini
    NilaiKaryawan.query.filter_by(karyawan_id=karyawan_id).delete()
    db.session.commit()
    flash('Penilaian berhasil dihapus!', 'success')
    return redirect(url_for('penilaian'))

@app.route('/hasil')
def hasil():
    # Get all employees and their scores
    karyawan_list = Karyawan.query.all()
    kriteria_list = Kriteria.query.all()
    
    # Calculate SAW scores
    hasil_saw = []
    
    # Get all scores for each criteria
    nilai_per_kriteria = {}
    for kriteria in kriteria_list:
        nilai_list = NilaiKaryawan.query.filter_by(kriteria_id=kriteria.id).all()
        nilai_per_kriteria[kriteria.id] = [n.nilai for n in nilai_list]
    
    # Find maximum value for each criteria
    nilai_max = {}
    for kriteria in kriteria_list:
        if kriteria.id in nilai_per_kriteria and nilai_per_kriteria[kriteria.id]:
            nilai_max[kriteria.id] = max(nilai_per_kriteria[kriteria.id])
    
    for karyawan in karyawan_list:
        nilai_karyawan = {}
        total_score = 0
        
        # Get all scores for this employee
        nilai_list = NilaiKaryawan.query.filter_by(karyawan_id=karyawan.id).all()
        
        # Check if employee has all criteria scores
        if len(nilai_list) == len(kriteria_list):
            for kriteria in kriteria_list:
                nilai = next((n for n in nilai_list if n.kriteria_id == kriteria.id), None)
                
                if nilai and kriteria.id in nilai_max:
                    # Normalisasi nilai (nilai / nilai maksimum)
                    normalized = nilai.nilai / nilai_max[kriteria.id]
                    nilai_karyawan[kriteria.nama] = normalized
                    total_score += normalized * kriteria.bobot
            
            hasil_saw.append({
                'karyawan': karyawan,
                'nilai': nilai_karyawan,
                'total_score': round(total_score, 4)
            })
    
    # Sort by total score
    hasil_saw.sort(key=lambda x: x['total_score'], reverse=True)
    
    return render_template('hasil.html', hasil_saw=hasil_saw)

def init_db():
    with app.app_context():
        # Create new database
        db.create_all()
        
        # Check if criteria already exist
        if Kriteria.query.count() == 0:
            # Add default criteria only if none exist
            kriteria_list = [
                {'nama': 'Kedisiplinan', 'bobot': 0.35, 'jenis': 'benefit'},
                {'nama': 'Kualitas Kerja', 'bobot': 0.35, 'jenis': 'benefit'},
                {'nama': 'Kuantitas Kerja', 'bobot': 0.30, 'jenis': 'benefit'}
            ]
            for kriteria in kriteria_list:
                k = Kriteria(**kriteria)
                db.session.add(k)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 