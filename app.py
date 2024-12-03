from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import cv2
import easyocr
import numpy as np
import re
import os
from PIL import Image

# Inicializar o leitor OCR
os.environ['EASYOCR_MODULE_PATH'] = os.path.join(os.getcwd(), '.EasyOCR')
reader = easyocr.Reader(['en'], gpu=False)

# Configuração do Flask
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Função para pré-processar e identificar o peso
def processar_imagem(imagem_caminho):
    imagem = cv2.imread(imagem_caminho)
    if imagem is None:
        return "Erro ao carregar imagem."

    # Pré-processamento
    imagem_gray = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    imagem_contraste_agressivo = clahe.apply(imagem_gray)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    imagem_nitida = cv2.filter2D(imagem_contraste_agressivo, -1, kernel)

    resultados = []
    for img in [imagem, imagem_contraste_agressivo, imagem_nitida]:
        resultado = reader.readtext(img, detail=0, paragraph=True)
        resultados.extend(resultado)

    numeros = []
    for resultado in resultados:
        numeros.extend(re.findall(r"\b\d+\b", resultado))

    candidatos = []
    for numero in numeros:
        if len(numero) > 4 and numero[0] == '1':
            candidatos.append(float(f"{numero[:3]}.{numero[3]}"))
        elif len(numero) == 4 or len(numero) == 3:
            candidatos.append(float(f"{numero[:2]}.{numero[2:3]}"))
        elif len(numero) == 2:
            candidatos.append(float(f"{numero[:2]}.0"))

    if candidatos:
        peso_valido = [peso for peso in candidatos if 40.0 <= peso <= 150.0]
        return f"{min(peso_valido, key=lambda x: abs(x - 70.0)):.1f} kg" if peso_valido else "Peso não identificado"
    else:
        return "Peso não identificado."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Processar a imagem
    resultado = processar_imagem(file_path)

    # Redimensionar a imagem para exibição
    imagem = cv2.imread(imagem_caminho)
    imagem = cv2.resize(imagem, (800, 800))
    img.save(file_path)

    return render_template('result.html', resultado=resultado, image_path=file.filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
    
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  
    app.run(host="0.0.0.0", port=port)
