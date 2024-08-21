import os
import sys
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import pydicom
import numpy as np

def crop_dicom(file_path):
    # Leer archivo DICOM seleccionado
    dicom_info = pydicom.dcmread(file_path)

    # Extraer la matriz de píxeles
    pixel_array = dicom_info.pixel_array

    # Quedarse solo con las filas de la 550 a la 1500
    pixel_array = pixel_array[550:1500, :]

    # Seleccionar la columna central
    central_column = pixel_array[:, pixel_array.shape[1] // 2]

    # Filtrar las filas cuyos píxeles sean menores a 1000 o iguales a 4095
    filtered_indices = np.where((central_column != 4095))[0]

    # Crear una nueva imagen recortada
    cropped_image = pixel_array[filtered_indices, :]

    # Crear un nuevo objeto FileDataset para la imagen recortada
    cropped_dicom_info = dicom_info.copy()
    cropped_dicom_info.PixelData = cropped_image.tobytes()
    cropped_dicom_info.Rows, cropped_dicom_info.Columns = cropped_image.shape

    # Devolver el objeto DICOM recortado
    return cropped_dicom_info

def CR2DCM_v2(dicom_info, output_dir, original_filename):
    """
    Modifica el archivo DICOM según las especificaciones dadas y lo guarda.

    Args:
        dicom_info (pydicom.dataset.FileDataset): El objeto DICOM que contiene la información.
        output_dir (str): El directorio donde se guardará el archivo modificado.
        original_filename (str): El nombre del archivo original.
    """
    # Localizar PF-noborrar.dcm en el directorio correcto
    base_path = os.path.join(get_resource_path(), 'PF-noborrar.dcm')
    Base = pydicom.dcmread(base_path)

    # Pedir al usuario la distancia de la placa CR
    root = tk.Tk()
    root.withdraw()
    SID = simpledialog.askstring("Distancia CR", "Ingrese la distancia de la placa CR (cm):", initialvalue="153")
    if not SID:
        print('User pressed cancel')
        return
    SID = float(SID) * 10

    # Actualizar los atributos en el objeto Base
    Base.ImagePlanePixelSpacing = dicom_info.PixelSpacing
    Base.RTImageSID = SID
    H, W = dicom_info.Rows, dicom_info.Columns
    spacing = dicom_info.PixelSpacing
    Basen = Base
    Hn = int(220 * (SID / 100) / spacing[0])
    Wn = int(220 * (SID / 100) / spacing[1])

    try:
        CRn = dicom_info.pixel_array[int(0.5 * (H - Hn)) + 1 : int(0.5 * (H + Hn)) : 2, int(0.5 * (W - Wn)) + 1 : int(0.5 * (W + Wn)) : 2]
    except:
        CRn = dicom_info.pixel_array[0:H:2, 0:W:2]

    Basen.Rows, Basen.Columns = CRn.shape
    Basen.ImagePlanePixelSpacing = [spacing[0] * 2, spacing[1] * 2]  # Asignar una lista de dos floats

    # Guardar el archivo DICOM modificado en el directorio especificado
    modified_filename = os.path.splitext(original_filename)[0] + '-a_QATrack.dcm'
    output_file = os.path.join(output_dir, modified_filename)
    Basen.PixelData = CRn.tobytes()
    Basen.save_as(output_file)
    print(f"Archivo DICOM modificado guardado en {output_file}")

def get_resource_path():
    """ Devuelve la ruta del directorio de recursos dependiendo si está empaquetado o no """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def main():
    # Primero recortar la imagen
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[('DICOM Files', '*.dcm')])
    if file_path:
        directory, original_filename = os.path.split(file_path)
        cropped_dicom = crop_dicom(file_path)
        if cropped_dicom:
            # Especificar el directorio de salida
            output_dir = directory
            # Luego modificar el archivo recortado y guardarlo en el directorio especificado
            CR2DCM_v2(cropped_dicom, output_dir, original_filename)
            messagebox.showinfo("Éxito", f"Archivo DICOM modificado guardado en {directory}")


if __name__ == "__main__":
    main()

