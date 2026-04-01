import os
from flask import Flask, render_template, request, redirect, flash, send_file, url_for
from werkzeug.utils import secure_filename
# On importe la nouvelle fonction Gemini
from services import extract_text_from_file, process_with_gemini, generate_word_doc_from_template

app = Flask(__name__)
app.secret_key = "azerty1234"

# --- CONFIGURATION DES DOSSIERS ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Détection de l'environnement Vercel
if os.environ.get('VERCEL'):
    # Sur Vercel, on utilise impérativement le dossier /tmp
    app.config['UPLOAD_FOLDER'] = '/tmp'
    app.config['RESULT_FOLDER'] = '/tmp'
else:
    # En local sur votre PC
    app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
    app.config['RESULT_FOLDER'] = os.path.join(BASE_DIR, 'results')
    # On ne crée les dossiers QUE si on est en local (sur Vercel /tmp existe déjà)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None
    if request.method == 'POST':
        # Vérification fichiers
        if 'doc_source' not in request.files or 'doc_exemple' not in request.files:
            flash('Fichiers manquants', 'error')
            return redirect(request.url)
            
        f_src = request.files['doc_source']
        f_ex = request.files['doc_exemple']
        
        if f_src.filename == '' or f_ex.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)

        # Sauvegarde
        path_src = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f_src.filename))
        path_ex = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f_ex.filename))
        f_src.save(path_src)
        f_ex.save(path_ex)

        # Lecture
        txt_src = extract_text_from_file(path_src)
        txt_ex = extract_text_from_file(path_ex)
        
        if txt_src and txt_ex:
            # 2. Générer le contenu avec Gemini
            ai_output = process_with_gemini(txt_src, txt_ex)

            # 3. Créer le Word Final
            final_doc_name = generate_word_doc_from_template(
                ai_output, 
                app.config['RESULT_FOLDER'], 
                path_ex
            )
            
            download_link = final_doc_name
            flash('Succès ! Le document est prêt.', 'success')
        else:
            flash("Erreur de lecture des fichiers.", "error")

    return render_template('index.html', download_link=download_link)

@app.route('/download/<path:filename>')
def download(filename):
    # send_file ira chercher le fichier dans /tmp sur Vercel
    return send_file(os.path.join(app.config['RESULT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)