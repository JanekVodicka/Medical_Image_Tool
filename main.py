#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Medical Tool
python -m PyInstaller --onefile -w -F --add-binary "ProSpon.ico;." main.py
python -m PyInstaller main.spec

Created on 22/07/2025
@autor: jan vodicka
"""

import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
from pathlib import Path
from tkinter.constants import DISABLED, NORMAL

from pydicom import dcmread
from pydicom.misc import is_dicom
import os
import sys
import trimesh
import numpy as np

def getAbsoluteResourcePath(relativePath):
    try:
        # Tento atribut vytvoří PyInstaller pouze za běhu .exe
        basepath = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        # Pokud je spuštěno jako .py (běžný skript)
        try:
            basepath = os.path.abspath(".")
        except AttributeError:
            basepath = ''

    abs_path = os.path.join(basepath, relativePath)

    # If the path still doesn't exist, this function won't help you
    if not os.path.exists(abs_path):
        print(f"Soubor '{relativePath}' nebyl nalezen v: {basepath}")
        return None

    return abs_path



class MedicalToolWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medical Tool")
        self.geometry("400x500")
        self.resizable(False, False)

        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill="both")

        # Záložky
        self.crop_tab = CropTab(notebook)
        self.registration_tab = RegAladinTab(notebook)
        self.rotation_tab = RotationTab(notebook)
        self.stl_tab = STLTab(notebook)
        self.dicom_tab = DICOMTab(notebook)

        # Přidání záložek do notebooku
        notebook.add(self.crop_tab, text="Crop Image")
        notebook.add(self.registration_tab, text="Reg Aladin")
        notebook.add(self.dicom_tab, text="DICOM Data")
        notebook.add(self.stl_tab, text="STLs")
        notebook.add(self.rotation_tab, text="Rotace")



class CropTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Declaring int variable
        self.start_x = tk.IntVar()
        self.end_x = tk.IntVar()
        self.start_y = tk.IntVar()
        self.end_y = tk.IntVar()
        self.start_z = tk.IntVar()
        self.end_z = tk.IntVar()
        # Default set to 1
        self.start_x.set(1)
        self.end_x.set(1)
        self.start_y.set(1)
        self.end_y.set(1)
        self.start_z.set(1)
        self.end_z.set(1)

        # Declaring string variable
        self.path_ct = tk.StringVar()
        self.path_ct_cropped = tk.StringVar()
        # Default set to none
        self.path_ct.set("None")
        self.path_ct_cropped.set("None")

        # Widgety
        self.frame_crop = tk.LabelFrame(self, text="Crop Image")
        self.frame_crop.pack(side="top", fill="x", padx=10, pady=10)

        self.tlacitko_browse = tk.Button(self.frame_crop, text="Browse", command=self.browse_files_ct, width=8)
        self.tlacitko_browse.grid(column=0, row=0, padx=10, pady=10)

        self.label_chosen_ct = tk.Label(self.frame_crop, text="Není vybraný soubor")
        self.label_chosen_ct.grid(column=1, row=0)

        self.label_x_coordinate = tk.Label(self.frame_crop, text="X:")
        self.label_x_coordinate.grid(column=0, row=1)

        self.x_coordinate = tk.Entry(self.frame_crop, textvariable=self.start_x, width=7)
        self.x_coordinate.grid(column=1, row=1)

        self.label_x_coordinate_add = tk.Label(self.frame_crop, text="X add:")
        self.label_x_coordinate_add.grid(column=2, row=1)

        self.x_coordinate_add = tk.Entry(self.frame_crop, textvariable=self.end_x, width=7)
        self.x_coordinate_add.grid(column=3, row=1)

        self.label_y_coordinate = tk.Label(self.frame_crop, text="Y:")
        self.label_y_coordinate.grid(column=0, row=2)

        self.y_coordinate = tk.Entry(self.frame_crop, textvariable=self.start_y, width=7)
        self.y_coordinate.grid(column=1, row=2)

        self.label_y_coordinate_add = tk.Label(self.frame_crop, text="Y add:")
        self.label_y_coordinate_add.grid(column=2, row=2)

        self.y_coordinate_add = tk.Entry(self.frame_crop, textvariable=self.end_y, width=7)
        self.y_coordinate_add.grid(column=3, row=2)

        self.label_z_coordinate = tk.Label(self.frame_crop, text="Z:")
        self.label_z_coordinate.grid(column=0, row=3)

        self.z_coordinate = tk.Entry(self.frame_crop, textvariable=self.start_z, width=7)
        self.z_coordinate.grid(column=1, row=3)

        self.label_z_coordinate_add = tk.Label(self.frame_crop, text="Z add:")
        self.label_z_coordinate_add.grid(column=2, row=3)

        self.z_coordinate_add = tk.Entry(self.frame_crop, textvariable=self.end_z, width=7)
        self.z_coordinate_add.grid(column=3, row=3)

        self.button_crop = tk.Button(self.frame_crop, text="Crop", command=self.crop, state=tk.DISABLED, width=8)
        self.button_crop.grid(column=0, row=4, pady=10)

        self.label_cropped_ct = tk.Label(self.frame_crop, text="Soubor ještě není vygenerován")
        self.label_cropped_ct.grid(column=1, row=4)

        self.button_open_cropped = tk.Button(self.frame_crop, text="Open cropped", command=self.open_cropped, state=tk.DISABLED)
        self.button_open_cropped.grid(column=0, row=5, columnspan=4, pady=(0,10))

    def browse_files_ct(self):
        img_path = filedialog.askopenfilename(initialdir="/",
                                                  title="Select a File",
                                                  filetypes=(("NII NRRD files",
                                                              ".nrrd .nii .nii.gz"),
                                                             ("all files",
                                                              "*.*")))
        if img_path:
            img_filename = Path(img_path).name
            self.path_ct.set(img_path)
            self.label_chosen_ct.configure(text=img_filename)
            self.button_crop.configure(state=tk.NORMAL)


    def crop(self):
        img_path = self.path_ct.get()

        crop_file_path = getAbsoluteResourcePath("crop.exe")

        img_filename = Path(self.path_ct.get()).name
        img_extension = Path(self.path_ct.get()).suffixes
        img_extension = ''.join(img_extension[-1])
        output_img_filename = img_filename.replace(img_extension, '_crop' + img_extension)
        output_img_path = str(Path(self.path_ct.get()).parent / output_img_filename)
        self.path_ct_cropped.set(output_img_path)
        # output_image_path = uniquify(output_image_path)

        x1 = self.start_x.get() - 1
        x_add = self.end_x.get()
        x2 = x1 + x_add

        y1 = self.start_y.get() - 1
        y_add = self.end_y.get()
        y2 = y1 + y_add

        z1 = self.start_z.get() - 1
        z_add = self.end_z.get()
        z2 = z1 + z_add

        cmd_str = f'{crop_file_path} "{img_path}" "{output_img_path}" {x1} {x2} {y1} {y2} {z1} {z2}'
        subprocess.run(cmd_str, shell=True)

        self.label_cropped_ct.configure(text=output_img_filename)
        self.button_open_cropped.configure(state=tk.NORMAL)

    def open_cropped(self):
        cmd_str = f'ITK-SNAP.exe "{self.path_ct_cropped.get()}"'
        subprocess.run(cmd_str, shell=True)



class RegAladinTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.frame_regaladin = tk.LabelFrame(self, text="Reg Aladin")
        self.frame_regaladin.pack(side="top", fill="x", padx=10, pady=10)
        self.initial_reference_dir = "/"
        self.path_reference = None
        self.path_floating = None
        self.path_tumor = None

        self.label_ref_ct = tk.Label(self.frame_regaladin, text="CT soubor:")
        self.label_ref_ct.grid(column=0, row=0, padx=10, pady=10)

        self.button_ref_ct = tk.Button(self.frame_regaladin, text="Browse", command=lambda: self.browse_files(selection_mode="reference"))
        self.button_ref_ct.grid(column=1, row=0)

        self.label_chosen_reference = tk.Label(self.frame_regaladin, text="")
        self.label_chosen_reference.grid(column=2, row=0)

        self.label_ref_mri = tk.Label(self.frame_regaladin, text="MRI soubor:")
        self.label_ref_mri.grid(column=0, row=1, padx=10, pady=10)

        self.button_ref_mri = tk.Button(self.frame_regaladin, text="Browse", command=lambda: self.browse_files(selection_mode="floating"))
        self.button_ref_mri.grid(column=1, row=1)

        self.label_chosen_floating = tk.Label(self.frame_regaladin, text="")
        self.label_chosen_floating.grid(column=2, row=1)

        self.label_ref_tum = tk.Label(self.frame_regaladin, text="Tumor soubor:")
        self.label_ref_tum.grid(column=0, row=2, padx=10, pady=10)

        self.button_ref_tum = tk.Button(self.frame_regaladin, text="Browse", command=lambda: self.browse_files(selection_mode="tumor"))
        self.button_ref_tum.grid(column=1, row=2)

        self.label_chosen_tumor = tk.Label(self.frame_regaladin, text="")
        self.label_chosen_tumor.grid(column=2, row=2)

        self.button_run_reg_aladin = tk.Button(self.frame_regaladin, text="Run Reg Aladin", command=self.run_reg_aladin, state=tk.DISABLED, width=15)
        self.button_run_reg_aladin.grid(column=1, row=3, pady=10)

        self.button_show_results = tk.Button(self.frame_regaladin, text="Show results", command=self.open_results, state=tk.DISABLED, width=15)
        self.button_show_results.grid(column=1, row=4, pady=(0,10))

    def browse_files(self, selection_mode):
        img_path = filedialog.askopenfilename(initialdir=self.initial_reference_dir,
                                                  title="Select a File",
                                                  filetypes=(("NII NRRD files",
                                                              ".nrrd .nii .nii.gz"),
                                                             ("all files",
                                                              "*.*")))
        if img_path:
            if selection_mode == "reference":
                self.initial_reference_dir = str(Path(img_path).parent)
                self.path_reference = img_path
                self.label_chosen_reference.configure(text=Path(img_path).name)
            elif selection_mode == "floating":
                self.path_floating = img_path
                self.label_chosen_floating.configure(text=Path(img_path).name)
            elif selection_mode == "tumor":
                self.path_tumor = img_path
                self.label_chosen_tumor.configure(text=Path(img_path).name)
            if self.path_reference is not None and self.path_floating is not None and self.path_tumor is not None:
                self.button_run_reg_aladin.configure(state=tk.NORMAL)

    def run_reg_aladin(self):
        working_dir = Path(self.path_reference).parent
        ct_img_path = Path(self.path_reference)
        mri_img_path = Path(self.path_floating)
        tum_img_path = Path(self.path_tumor)

        reg_aladin_path = getAbsoluteResourcePath("reg_aladin.exe")
        cmd_str = f'{reg_aladin_path} -ref "{Path(ct_img_path).name}" -flo "{Path(mri_img_path).name}" -tum "{Path(tum_img_path).name}" -rigOnly -ln 4'
        subprocess.run(cmd_str, cwd=working_dir, shell=True)
        self.button_show_results.configure(state=tk.NORMAL)

    def open_results(self):

        ref_path = Path(self.path_reference)
        float_path = Path(self.path_floating)

        float_stem = float_path.stem

        seg_path = ref_path.parent / f"Tumor_to_{ref_path.name}"
        overlay_path = ref_path.parent / f"{float_stem}_to_{ref_path.name}"

        cmd_str = f'ITK-SNAP.exe -g "{ref_path}" -s "{seg_path}" -o "{overlay_path}"'
        subprocess.run(cmd_str, shell=True)


class DICOMTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.dicom_reference = "/"
        self.nazev_serie = ""

        self.frame_convert = tk.LabelFrame(self, text="Convert")
        self.frame_convert.pack(side="top", fill="x", padx=10, pady=10)

        self.label_adresar_dicom = tk.Label(self.frame_convert, text="Adresář DICOM:")
        self.label_adresar_dicom.pack()

        self.button_browse_dicom_dir = tk.Button(self.frame_convert, text="Browse DICOM", command=self.browse_dicom_dir)
        self.button_browse_dicom_dir.pack()

        self.label_adresar_dicom_selected = tk.Label(self.frame_convert, text="")
        self.label_adresar_dicom_selected.pack(padx=10, pady=5)

        self.button_convert = tk.Button(self.frame_convert, text="Convert", width=8, state=tk.DISABLED, command=self.convert_dicoms)
        self.button_convert.pack(pady=(0,10))

        self.button_open_nii = tk.Button(self.frame_convert, text="Open nii", width=8, state=tk.DISABLED, command=self.open_nii)
        self.button_open_nii.pack(pady=(0, 10))

        self.frame_dicom_data = tk.LabelFrame(self, text="DICOM Data")
        self.frame_dicom_data.pack(side="top", fill="x", padx=10, pady=10)

        # Treeview pro zobrazení tagů
        self.tree = ttk.Treeview(self.frame_dicom_data, columns=("Tag", "Hodnota"), show="headings")
        self.tree.heading("Tag", text="Tag")
        self.tree.heading("Hodnota", text="Hodnota")
        self.tree.column("Tag")
        self.tree.column("Hodnota")
        self.tree.pack(padx=5, pady=5)

    def browse_dicom_dir(self):
        dicom_dir = filedialog.askdirectory()

        if dicom_dir:
            # Projdi všechny soubory a hledej první skutečný DICOM
            for nazev_souboru in os.listdir(dicom_dir):
                cesta = os.path.join(dicom_dir, nazev_souboru)
                if os.path.isfile(cesta) and is_dicom(cesta):
                    try:
                        ds = dcmread(cesta)
                        self.nazev_serie = f'{ds.get((0x0020, 0x0011)).value if (0x0020, 0x0011) in ds else "N/A"}-{ds.get((0x0008, 0x103E)).value if (0x0008, 0x103E) in ds else "N/A"}'
                        self.label_adresar_dicom_selected.configure(text=self.nazev_serie)
                        self.dicom_reference = dicom_dir
                        self.button_convert.configure(state=tk.NORMAL)
                        tags = {
                            "Description (0008,103E)": ds.get((0x0008, 0x103E)).value if (0x0008, 0x103E) in ds else "N/A",
                            "Series Number (0020,0011)": ds.get((0x0020, 0x0011)).value if (0x0020, 0x0011) in ds else "N/A",
                            "Patient's Name (0010,0010)": ds.get((0x0010, 0x0010)).value if (0x0010, 0x0010) in ds else "N/A",
                            "Patient ID (0010,0020)": ds.get((0x0010, 0x0020)).value if (0x0010, 0x0020) in ds else "N/A",
                            "Coordinates (0020,0032)": ds.get((0x0020, 0x0032)).value if (0x0020, 0x0032) in ds else "N/A",
                            "Image Number (0020,0013)": ds.get((0x0020, 0x0013)).value if (0x0020, 0x0013) in ds else "N/A",
                            "Age (0010,1010)": ds.get((0x0010, 0x1010)).value if (0x0010, 0x1010) in ds else "N/A",
                            "Birthday (0010,0030)": ds.get((0x0010, 0x0030)).value if (0x0010, 0x0030) in ds else "N/A",
                            "Sex (0010,0040)": ds.get((0x0010, 0x0040)).value if (0x0010, 0x0040) in ds else "N/A"
                        }

                        for tag_name, value in tags.items():
                            self.tree.insert("", tk.END, values=(tag_name, str(value)))
                        return

                    except Exception as e:
                        print(f"Chyba při čtení DICOMu: {e}")
                    #except InvalidDicomError:
                        #self.show_error("Soubor není platný DICOM.")


            print("Ve složce nebyl nalezen žádný validní DICOM soubor.")

    def convert_dicoms(self):
        working_dir = Path(self.dicom_reference).parent
        dicom2file_path = getAbsoluteResourcePath("dicom2file.exe")
        cmd_convert = f'{dicom2file_path} "{self.dicom_reference}" "{self.nazev_serie}.nii"  1'
        subprocess.run(cmd_convert, cwd=working_dir, shell=True)
        self.button_open_nii.configure(state=tk.NORMAL)

    def open_nii(self):
        cmd_str = f'ITK-SNAP.exe "{os.path.dirname(self.dicom_reference)}/{self.nazev_serie}.nii"'
        print(cmd_str)
        subprocess.run(cmd_str, shell=True)



class STLTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.stl_file_path = ""

        self.button_open_stl = tk.Button(self, text="Open STL", command=self.open_stl, width=20)
        self.button_open_stl.pack(pady=10)

        self.button_export_stl_for_mimics = tk.Button(self, text="Export STL for Mimics", state=tk.DISABLED, command=self.export_stl_for_mimics, width=20)
        self.button_export_stl_for_mimics.pack()

    def open_stl(self):
        self.stl_file_path = filedialog.askopenfilename(filetypes=(("STL files", "*.stl"), ("all files", "*.*")))

        if self.stl_file_path:
            self.button_export_stl_for_mimics.configure(state=NORMAL)
            return

    def export_stl_for_mimics(self):
        # Načti STL
        path = Path(self.stl_file_path)
        mesh = trimesh.load(path)

        # Matice pro škálování
        scale_matrix = np.array([
            [-1, 0, 0, 0],
            [0, -1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        # Aplikuj transformaci
        mesh.apply_transform(scale_matrix)

        new_path = path.with_name(f"{path.stem}_for_Mimics.stl")
        new_path_export = new_path.as_posix()
        # Uložit výstup
        mesh.export(new_path_export)



class RotationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        ttk.Label(self, text="Zadejte úhel rotace").pack(pady=10)



# vytvoření hlavního okna a spuštění aplikace
if __name__ == "__main__":
    app = MedicalToolWindow()
    app.mainloop()



