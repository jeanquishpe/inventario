from flask import Flask, render_template, jsonify, request
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_PATH = 'C:/bienes/123.xlsx'

def read_excel():
    """Lee el archivo Excel"""
    try:
        df = pd.read_excel(EXCEL_PATH)
        # Asegurar que todas las columnas sean string para evitar problemas de tipos
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        # Agregar columnas si no existen
        if 'Verificado' not in df.columns:
            df['Verificado'] = 'NO'
        if 'Usuario_Final' not in df.columns:
            df['Usuario_Final'] = ''
        if 'Ubicacion' not in df.columns:
            df['Ubicacion'] = ''
        if 'Estado' not in df.columns:
            df['Estado'] = ''
            
        return df
    except Exception as e:
        print(f"Error leyendo Excel: {str(e)}")
        raise

def save_excel(df):
    """Guarda el Excel de forma segura"""
    try:
        # Primero guardar en un archivo temporal
        temp_path = 'C:/bienes/temp_123.xlsx'
        df.to_excel(temp_path, index=False)
        
        # Si el guardado temporal fue exitoso, reemplazar el archivo original
        if os.path.exists(EXCEL_PATH):
            os.rename(EXCEL_PATH, f"{EXCEL_PATH}.bak")  # Crear backup
        os.rename(temp_path, EXCEL_PATH)
        
        # Eliminar backup anterior si todo fue bien
        if os.path.exists(f"{EXCEL_PATH}.bak"):
            os.remove(f"{EXCEL_PATH}.bak")
            
        return True
    except Exception as e:
        # Restaurar backup si algo salió mal
        if os.path.exists(f"{EXCEL_PATH}.bak"):
            os.rename(f"{EXCEL_PATH}.bak", EXCEL_PATH)
        print(f"Error guardando Excel: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bienes')
def get_bienes():
    try:
        filter_type = request.args.get('filter', 'all')
        df = read_excel()
        
        # Aplicar filtros según el tipo
        if filter_type == 'verified':
            df = df[df['Verificado'] == 'SI']
        elif filter_type == 'pending':
            df = df[df['Verificado'] == 'NO']
            
        return jsonify({'data': df.to_dict('records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verificar', methods=['POST'])
def verificar_bien():
    try:
        data = request.json
        df = read_excel()
        
        # Convertir ID a string para comparación segura
        id_buscar = str(data['id'])
        
        # Encontrar y actualizar el registro
        mask = df['IDENTIFICADOR'].astype(str) == id_buscar
        if not mask.any():
            return jsonify({'error': 'ID no encontrado'}), 404
            
        # Actualizar valores
        df.loc[mask, 'Verificado'] = 'SI'
        df.loc[mask, 'Usuario_Final'] = data['usuario_final']
        df.loc[mask, 'Ubicacion'] = data['ubicacion']
        df.loc[mask, 'Estado'] = data['estado']
        df.loc[mask, 'Fecha_Verificacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Guardar cambios
        if save_excel(df):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Error al guardar'}), 500
            
    except Exception as e:
        print(f"Error en verificación: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        df = read_excel()
        total = len(df)
        verificados = len(df[df['Verificado'] == 'SI'])
        return jsonify({
            'total': total,
            'verificados': verificados,
            'pendientes': total - verificados
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Asegurar que existe el directorio
    os.makedirs('C:/bienes', exist_ok=True)
    app.run(debug=True, port=5000)