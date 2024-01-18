import csv
import tkinter as tk
from tkinter import filedialog

from src.ansys.speos.workflow.create_speos_bsdf.create_spectral_bsdf import (
    BrdfStructure,
    BsdfMeasurementPoint,
)


def getfilename(extension, save=False):
    """
    Parameters
    ----------
    extension : str
        containing the which file extension in *.ending format
    save : Bool
        option to define to open(default) or save. The default is False.

    Returns
    -------
    str
        string containing the selected file path
    """
    root = tk.Tk()
    root.withdraw()
    if not save:
        file_path = filedialog.askopenfilename(filetypes=[("Excel", extension)])
    else:
        file_path = filedialog.asksaveasfilename(filetypes=[("Excel", extension)])
        if not file_path.endswith(extension.strip("*")):
            file_path += extension.strip("*")
    return file_path


def convert_export(input_csv, output_path):
    """
    main function to convert 2d data into brdf and export.

    Parameters
    ----------
    input_csv : str
        path of csv file recording the 2d data.
    output_path : str
        path for the brdf to be exported.

    Returns
    -------


    """
    wavelength_list = []
    brdf_data = None
    with open(input_csv) as file:
        content = csv.reader(file, delimiter=",")
        FirstRow = True
        for row in content:
            if FirstRow:
                wavelength_list = [item.split("nm")[0] for item in row][2:]
                wavelength_list = [float(item) for item in wavelength_list]
                brdf_data = BrdfStructure(wavelength_list)
            else:
                for wavelength_idx, wavelength in enumerate(wavelength_list):
                    brdf_data.measurement_2d_bsdf.append(
                        BsdfMeasurementPoint(float(row[0]), wavelength, float(row[1]), float(row[2 + wavelength_idx]))
                    )
            FirstRow = False
        brdf_data.convert_2D_3D(sampling=1)
        brdf_data.export_to_speos(output_path, debug=True)


def main():
    """
    main function to run conversion.

    Returns
    -------

    """
    path_to_csv = getfilename("*.csv")
    if path_to_csv != "":
        convert_export(path_to_csv, r"D:\\")


main()
