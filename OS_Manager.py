from PySide6.QtWidgets import QApplication, QFileDialog, QTableWidgetItem, \
    QLabel, QSlider, QGraphicsView, QGraphicsScene, QMainWindow, \
        QGraphicsPixmapItem, QMessageBox, QSplashScreen
from PySide6.QtGui import QCloseEvent, QPixmap
import sys
from PySide6.QtCore import Qt
import time

app = QApplication(sys.argv)

# Charger l'image du splashscreen
splash_pix = QPixmap('OSlogo.ico')
splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
splash.setMask(splash_pix.mask())
splash.show()

# Afficher une étiquette de chargement
label = QLabel("Loading...", splash)
font = label.font()
font.setPointSize(15)
label.setFont(font)
label.adjustSize()
label.move(50, splash_pix.height() - 50)
splash.showMessage('Loading...', Qt.AlignBottom | Qt.AlignCenter, Qt.white)

import matplotlib
matplotlib.use("tkagg")
import os
from pathlib import Path
from OS_Window import OrganoSegmenterWindow, ProgressBarWindow
from process.fileManager import ImageFolderInfos
from PySide6.QtGui import QColor, QPalette, QPixmap, QImage, QIcon, QWheelEvent
from process.processManager import predict_file_global
from process.preprocessing import gaussianDifference, gaussianDivision, unsharpMask, correctBleaching,apply_preproc
from process.montage import createContourOverlay, createOverlay
import json
import time
import pandas as pd
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from tifffile import imread
import webbrowser
from process.visualizationVTK import numpyToVTK, getSurface, getVolumes
from process.fileManager import ImType

from cellpose.models import CellposeModel

my_window = OrganoSegmenterWindow()
selectedImage, dictPredicted, dictLayers, currentLayer, currentMask, currentDf, fileInfos = None, None, None, None, None, None, None

def create_dark_palette()->QPalette:
    palette = QPalette()

    # Couleurs principales
    palette.setColor(QPalette.Window, QColor(9, 9, 9))
    palette.setColor(QPalette.WindowText, QColor(250, 250, 250))
    palette.setColor(QPalette.Base, QColor(44, 44, 44))
    palette.setColor(QPalette.AlternateBase, QColor(18, 18, 18))
    palette.setColor(QPalette.ToolTipBase, QColor(250, 250, 250))
    palette.setColor(QPalette.ToolTipText, QColor(250, 250, 250))
    palette.setColor(QPalette.Text, QColor(200, 200, 200))
    palette.setColor(QPalette.Button, QColor(18, 18, 18))
    palette.setColor(QPalette.ButtonText, QColor(250, 250, 250))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(250, 250, 250))
    # Couleurs spécifiques aux états des widgets
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    return palette

def openFolder():
    global dictPredicted
    global fileInfos
    dictPredicted = None
    my_window.setMasksComboBox(dictPredicted)
    my_window.setStatisticsTableInit(dictPredicted)
    open_folder_name = QFileDialog.getExistingDirectory(None, "Select Image Folder")
    my_window.ImageFolder.setText(open_folder_name)
    fileInfos = ImageFolderInfos(open_folder_name, onlyHandeled=True) #get fileInfo without reading files + remove same name files
    if len(fileInfos) < 1:
        my_window.setFileList([])
        my_window.ImageFolder.setText(open_folder_name)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        error_msg = 'The images must be named according to the following format:'
        error_msg += ' "image_name" + "_C1", "_C2", "_C3", etc., '
        error_msg += 'corresponding to the number of channels. '
        error_msg += 'Please ensure each image file follows this naming convention before proceeding.'
        msg.setText(error_msg)
        msg.setWindowTitle('Error: Invalid Image Format')
        msg.exec()
        return
    fileListNames = [str(el) for el in fileInfos]
    my_window.setFileList(fileListNames)
    if len(fileListNames)>0:
        my_window.FileListWidget.setCurrentRow(0)
        imageSelected(my_window.FileListWidget.item(0))
    my_window.ExploreVolumesWindowButton.setEnabled(False)
    
def openDemoFolder():
    global dictPredicted
    global fileInfos
    dictPredicted = None
    my_window.setMasksComboBox(dictPredicted)
    my_window.setStatisticsTableInit(dictPredicted)
    open_folder_name = QFileDialog.getExistingDirectory(None, "Select Image Folder")
    my_window.ImageFolder.setText(open_folder_name)
    fileInfos = ImageFolderInfos(open_folder_name, onlyHandeled=True) #get fileInfo without reading files + remove same name files
    imPaths = list(Path(open_folder_name).glob("*.tif"),)
    infos = []
    for imPath in imPaths:
        name = imPath.name
        
        infos.append()
    infos = [ImInfo(imPath,channelTags) for imPath in imPaths]

    if len(fileInfos) < 1:
        my_window.setFileList([])
        my_window.ImageFolder.setText(open_folder_name)
        return
    fileListNames = [str(el) for el in fileInfos]
    my_window.setFileList(fileListNames)
    if len(fileListNames)>0:
        my_window.FileListWidget.setCurrentRow(0)
        imageSelected(my_window.FileListWidget.item(0))
    my_window.ExploreVolumesWindowButton.setEnabled(False)

def openJsonParameters():
    json_parameters_name = QFileDialog.getOpenFileName(None, "Select a file 'parameters.json'")
    f = open(json_parameters_name[0])
    data = json.load(f)
    my_window.setAllParameters(data)

def imageSelected(item):
    global selectedImage
    global dictPredicted
    global dictLayers
    global currentLayer
    global currentMask
    global currentDf
    
    my_window.spacingX, my_window.spacingY, my_window.spacingZ = None, None, None
    my_window.opacityValueSlider, my_window.ValuesList = None, None
    
    index = my_window.FileListWidget.row(item)
    FileInfo = fileInfos[index]
    enable_3D_tools = FileInfo.type is not ImType.Im2D
    my_window.ImageViewerSlider.setEnabled(enable_3D_tools)
    my_window.changeViewCheckBox.setEnabled(enable_3D_tools)
    my_window.View3DPushButton.setEnabled(enable_3D_tools)
    my_window.DeltaZLabel.setEnabled(enable_3D_tools)
    my_window.DeltaZLineEdit.setEnabled(enable_3D_tools)
    my_window.ZValueLabel.setEnabled(enable_3D_tools)
    my_window.ResampleZLabel.setEnabled(enable_3D_tools)
    my_window.ResampleZLineEdit.setEnabled(enable_3D_tools)
    size_infos = 'Volumes:' if enable_3D_tools else 'Areas:'
    my_window.VolumeLimitLabel.setText(size_infos)
    unity_dim_str = '3' if enable_3D_tools else '2'
    dim_str = my_window.UnityMuLabel.text()[:-2] + unity_dim_str + ')'
    my_window.UnityMuLabel.setText(dim_str)
    
    selectedImage = FileInfo.Display()
    my_window.setChannelsComboBox(FileInfo)
    my_window.setVoxelSizes( FileInfo)
    
    if dictPredicted is not None:
        if dictPredicted['file']:
            dictPredicted = None
            my_window.setMasksComboBox(dictPredicted)
            my_window.setStatisticsTableInit(dictPredicted)
            dictLayers, currentLayer, currentMask, currentDf = None, None, None, None
            setStatisticsTable()
        else:
            dictLayers = createDictLayers(dictPredicted, index_selected_file = index)
            currentLayer, currentMask = changeLayer(my_window.MaskVisualisationComboBox.currentText())
    else:
        dictPredicted = None
        my_window.setMasksComboBox(dictPredicted)
        dictLayers, currentLayer, currentMask, currentDf = None, None, None, None
        setStatisticsTable()
    my_window.setSliderVisualisation(selectedImage.shape[0] - 1)
    if my_window.changeViewCheckBox.isChecked():
        my_window.clear3DWindow() #test
        view3D(spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)
    else:
        my_window.showImage(selectedImage, layer = currentLayer)
    my_window.ExploreVolumesWindowButton.setEnabled(False)
    
    
def chooseModel():
    model_name = QFileDialog.getExistingDirectory(None, "Select A Model")
    my_window.ChangeModelTextBrowser.setText(model_name)

def changePlotFeature(columnName = None):
    if columnName is None or len(columnName)<1:
        columnName = my_window.FeaturePlotComboBox.currentText()
    typeGraph = my_window.PlotTypeComboBox.currentText()
    my_window.showPlot(currentDf, columnName, typeGraph)

def changePlotType(typeGraph = None):
    if typeGraph is None or len(typeGraph)<1:
        typeGraph = my_window.PlotTypeComboBox.currentText()
    columnName = my_window.FeaturePlotComboBox.currentText()
    my_window.showPlot(currentDf, columnName, typeGraph)

def createPlot(tab):
    if tab != 2:
        pass
    elif tab == 2:
        changePlotType()

def zViewChange(z):
    my_window.showImage(selectedImage, z = z, layer = currentLayer)
    
def channelViewChange(channel):
    if channel == '':
        return
    if not my_window.changeViewCheckBox.isChecked():
        my_window.showImage(selectedImage, channel = channel, layer = currentLayer)
    else:
        my_window.clear3DWindow() #test
        view3D(channel = channel, spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)

def createDictLayers(dict_pred, index_selected_file = None):
    if dict_pred["folder"] : 
        path_nuclei_mask = dict_pred["images_paths"]["mask_nuclei"][index_selected_file]
        cell = len(dict_pred['images_paths']["mask_cell"])>0
        path_cell_mask = dict_pred["images_paths"]["mask_cell"][index_selected_file] if cell else None
        organo = len(dict_pred["images_paths"]["mask_organo"])>0

        path_organoid_mask = dict_pred["images_paths"]["mask_organo"][index_selected_file] if organo else None
    else:
        path_nuclei_mask = dict_pred["images_paths"]["mask_nuclei"]
        cell = (dict_pred['images_paths']["mask_cell"] is not None)
        path_cell_mask = dict_pred["images_paths"]["mask_cell"] if cell else None
        organo = dict_pred["images_paths"]["mask_organo"] is not None
        path_organoid_mask = dict_pred["images_paths"]["mask_organo"] if organo else None
    mask_nuclei = imread(path_nuclei_mask)
    nucleiContourOverlay = createContourOverlay(mask_nuclei,1)    
    if cell:
        mask_cell = imread(path_cell_mask)
        cellContourOverlay = createContourOverlay(mask_cell,1, [255,255,0])
        nucleiCellContourOverlay = createContourOverlay(mask_nuclei,1,[255,0,255])
        nucleiCellContourOverlay[mask_nuclei==0] = cellContourOverlay[mask_nuclei==0]  
    if organo:
        mask_organo = imread(path_organoid_mask)
        organoidContourOverlay = createContourOverlay(mask_organo, 1)
    return {
        "nucleiContourOverlay" : nucleiContourOverlay,
        "cellContourOverlay" : cellContourOverlay if cell else None,
        "nucleiCellContourOverlay" : nucleiCellContourOverlay if cell else None,
        "organoidContourOverlay" : organoidContourOverlay if organo else None
    } 
      
def getCurrentMask(layerItem, index = None, folder_mode = False):
    currentMask = None
    if layerItem == "" or layerItem == "None":
        currentLayer = None
        currentMask = None
    elif layerItem == "Nuclei":
        currentLayer = dictLayers["nucleiContourOverlay"].copy()
        currentMask = imread(getMaskPath("mask_nuclei", index, folder_mode))
    elif layerItem == "Cells":
        currentLayer = dictLayers["cellContourOverlay"].copy()
        currentMask = imread(getMaskPath("mask_cell", index, folder_mode))
    elif layerItem == "Nuclei + Cells":
        currentLayer = dictLayers["nucleiCellContourOverlay"].copy()
        currentMask = None
    elif layerItem == "Organoid":
        currentLayer = dictLayers["organoidContourOverlay"].copy()
        currentMask = imread(getMaskPath("mask_organo", index, folder_mode))

    return currentLayer, currentMask

def getMaskPath(name, index = None, folder_mode =False):
    return dictPredicted["images_paths"][name][index] if  folder_mode  else dictPredicted["images_paths"][name]

def changeLayer(layerItem):
    global currentLayer
    global currentMask
    currentLayer, currentMask = getCurrentMask(layerItem, index = my_window.FileListWidget.currentRow(), folder_mode=dictPredicted["folder"] if dictPredicted is not None else None)
    if not my_window.changeViewCheckBox.isChecked():
        my_window.showImage(selectedImage, layer = currentLayer)
    else:
        my_window.clear3DWindow() #test
        view3D(layer = layerItem, spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)
    return currentLayer, currentMask
    
def processFile():
    global dictPredicted
    global dictLayers
    global currentDf
    # my_window.setWindowTitle(f"OrganoSegmenter (version {my_window.app_version}) (running) - Quantacell - ")
    popup = ProgressBarWindow()
    # popup.exec_()
    nucleiParameters = my_window.getNucleiParam()
    cellsParameters = my_window.getCellsParam()
    organoidParameters = my_window.getOrganoidParam()
    imageParameters = my_window.getImageParameters()
    preprocessingList = my_window.getPreprocessingList()
    dictPreprocessing = getDictPreprocFromListPreproc(preprocessingList)
    dictExport = my_window.getExportParam()
    dictParameters = createDictParam(nucleiParameters, cellsParameters, organoidParameters, dictPreprocessing, imageParameters, dictExport)
    dictPredicted = predict_file_global(**dictParameters)
    if not isinstance(dictPredicted, dict):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        if isinstance(dictPredicted, tuple):
            error_msg = 'Error: image dimensions exceed limits. '
            error_msg += f'The dimensions of the current image {dictPredicted} exceed '
            error_msg += 'the maximum allowed dimensions. Tiling processing may be necessary. '
            error_msg += 'Please contact us for more information.'
            window_title = 'OrganoSegmenter: image dimensions too large'
        elif isinstance(dictPredicted, int):
            error_msg = "Error: The model failed to load correctly. Please verify the file path and format, and ensure that all necessary dependencies are installed."
            window_title = 'Error: model loading'
        else:
            error_msg = 'Error: The loaded model has a different dimensoin than the image you are attempting to process. '
            error_msg += 'Please ensure that the model matches the input image dimensions for proper processing.'
            window_title = 'OrganoSegmenter: dimension mismatch error'
        msg.setText(error_msg)
        msg.setWindowTitle(window_title)
        msg.exec()
        dictPredicted = {"file" : True, "folder" : False,
                         "dataframes": {"dt_nuclei": None, "dt_organo": None,
                                        "dt_cell": None, "dt_cyto": None},
                         "result_folder": '',
                         "images_paths": {"montage_nuclei":[], "mask_nuclei":[],
                                          "mask_organo":[], "montage_cell":[],
                                          "mask_cell":[], "montage_cell_nuclei":[],
                                          "mask_cyto":[]}
                         }
        return dictPredicted
    popup.updateProgressBar()
    dictLayers = createDictLayers(dictPredicted)
    if dictExport["exportParameters"]:
        writeJsonParameters(nucleiParameters, cellsParameters, organoidParameters, imageParameters, preprocessingList, dictExport, dictPredicted["result_folder"])
    my_window.setStatisticsTableInit(dictPredicted)
    currentDf = dictPredicted["dataframes"]["dt_nuclei"]
    columns_to_remove = [col for col in currentDf.columns if 'name_split' in col]
    currentDf = currentDf.loc[:, ~currentDf.columns.isin(columns_to_remove)]
    setStatisticsTable()
    changePlotType()
    my_window.setMasksComboBox(dictPredicted)
    my_window.setStatisticsTableInit(dictPredicted)
    my_window.ExploreVolumesWindowButton.setEnabled(True)
    # my_window.setWindowTitle(f"OrganoSegmenter (version {my_window.app_version}) - Quantacell - ")
    return dictPredicted



def process_with_cellpose():
    """
    Handles image processing with the CellposeSAM model via the Cellpose API.
    """
    global dictPredicted

    # Get parameters from the UI
    index = my_window.FileListWidget.currentRow()
    if index < 0:
        print("No image selected.")
        return None

    image_path_str = fileInfos[index].MainPath()
    image_path = Path(image_path_str)
    params = my_window.getNucleiParam()
    imageParameters = my_window.getImageParameters()

    # Create a results directory
    result_folder = Path("results") / f"{image_path.stem}_cellpose_output"
    result_folder.mkdir(exist_ok=True, parents=True)

    # Load the image
    try:
        image_data = imread(image_path)
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

    # Initialize and run the CellposeSAM model
    print("Initializing CellposeSAM model...")
    # Note: The 'cellpose_sam' model might require a GPU.
    model = CellposeModel(model_type='cellpose_sam')

    print(f"Processing {image_path.name} with CellposeSAM...")
    # The channel axis needs to be set correctly for model.eval.
    # For grayscale 3D, channels=[0,0] is standard.
    # For 3D RGB, it might be channels=[[2,3],[1,3]] or similar depending on your data.
    # We assume grayscale here.
    masks, flows, styles, diams = model.eval(image_data,
                                             diameter=params.get('diameter'),
                                             z_axis=0,
                                             do_3D=True)

    # Save the output mask
    mask_path = result_folder / f"{image_path.stem}_mask.tif"
    imwrite(mask_path, masks)
    print(f"Saved mask to {mask_path}")

    # Create a dummy statistics file to prevent downstream errors.
    # The real feature extraction happens later in the pipeline.
    fusion_path = result_folder / "fusion-statistics.csv"
    pd.DataFrame({'label': np.unique(masks)[1:]}).to_csv(fusion_path, index=False)

    # Return the results dictionary in the expected format
    dictPredicted = {
        "result_folder": str(result_folder),
        "folder": True,
        "images_paths": {
            "mask_nuclei": str(mask_path),
            "mask_organo": None  # No organoid mask from this process
        }
    }
    return dictPredicted

def createDictParamFolder(nucleiParameters, cellsParameters, organoidParameters, dictPreprocessing, folderPath, imageParameters, dictExport):
        fnames = [info.name for info in fileInfos]
        volumeMin = int(nucleiParameters["volumeMin"]) if nucleiParameters["volumeMin"].isdigit() else None
        volumeMax = int(nucleiParameters["volumeMax"]) if nucleiParameters["volumeMax"].isdigit() else None
        if organoidParameters["volumeMinOrganoid"] is not None : 
            volumeMinOrganoid = int(organoidParameters["volumeMinOrganoid"]) if organoidParameters["volumeMinOrganoid"].isdigit() else 0
        if Path(nucleiParameters["modelPath"]).exists() and len(nucleiParameters["modelPath"])>0:
            modelName = os.path.split(nucleiParameters["modelPath"])[-1]
            modelPath = os.path.split(nucleiParameters["modelPath"])[0]
        else :
            modelName = None
            modelPath = None
        return {
        "folder_path" : folderPath, 
        "fnames" : fnames,
        "channelNuclei" : int(nucleiParameters["channelNuclei"]) - 1 if fileInfos[my_window.FileListWidget.currentRow()].channel>0 else None,  
        "channelOrganoid" : organoidParameters["channelOrganoid"] if (organoidParameters["doOrganoid"] and fileInfos[my_window.FileListWidget.currentRow()].channel>0) else None, 
        "channelCell" : (int(cellsParameters["channelCells"]) - 1) if (cellsParameters["doCells"] and fileInfos[my_window.FileListWidget.currentRow()].channel>0) else None,
        "organoMethod" : organoidParameters["methodOrganoid"] if organoidParameters["doOrganoid"] else None,
        "organoidParameter" : organoidParameters["parameterOrganoid"],
        "keepLargestOrganoid" : organoidParameters["keepLargestOrganoid"],
        "volumeMinOrganoid" : volumeMinOrganoid if not organoidParameters["keepLargestOrganoid"] else None,
        "prep" : len(dictPreprocessing)>0, 
        "dict_preproc" : dictPreprocessing, 
        "slider_nms" : nucleiParameters["NmsThreshold"], 
        "slider_prob" : nucleiParameters["ProbThreshold"],
        "resize_valueX" : float(nucleiParameters["resizeX"]), 
        "resize_valueY" : float(nucleiParameters["resizeY"]), 
        "resize_valueZ" : float(nucleiParameters["resizeZ"]), 
        "dx" : float(imageParameters["dx"]), 
        "dy" : float(imageParameters["dy"]), 
        "dz" : float(imageParameters["dz"]),
        "radius_cell" : int(cellsParameters["radius"]) if cellsParameters["radius"].isdigit() else 5,
        "dist_max" : int(cellsParameters["distMax"]) if cellsParameters["radius"].isdigit() else 14,
        "cell_seg_method" : cellsParameters["methodCells"] if cellsParameters["doCells"] else None,  
        "cellStains" : cellsParameters["cellStains"],
        "cytoStains" : cellsParameters["cytoStains"],
        "cell" : cellsParameters["doCells"], 
        "min_vol" : volumeMin, 
        "max_vol" : volumeMax, 
        "folder_model" : modelPath,
        "modelname" : modelName,
        "defaultModel" : nucleiParameters["defaultModel"],
        "exportChannels" : dictExport["exportChannels"],
        "exportOverlays" : dictExport["exportOverlays"],
        "exportParameters" : dictExport["exportParameters"],
        "exportComposite" :  dictExport["exportComposite"]  
        }
        
def writeJsonParameters(nucleiParameters, cellsParameters, organoidParameters, imageParameters, preprocessingList, dictExport, folder_path):
    complete_path = folder_path + "/parameters.json"
    data = {
        "NucleiParameters":{
            "channelNuclei" : nucleiParameters["channelNuclei"],
            "modelPath" : nucleiParameters["modelPath"],
            "defaultModel" : nucleiParameters["defaultModel"],
            "resizeX" : nucleiParameters["resizeX"],
            "resizeY" : nucleiParameters["resizeY"],
            "resizeZ" : nucleiParameters["resizeZ"],
            "NmsThreshold" : nucleiParameters["NmsThreshold"],
            "ProbThreshold" : nucleiParameters["ProbThreshold"],
            "volumeMin" : nucleiParameters["volumeMin"],
            "volumeMax" : nucleiParameters["volumeMax"]},
        "CellsParameters":{
            "doCells" : cellsParameters["doCells"],
            "channelCells" : cellsParameters["channelCells"],
            "methodCells" : cellsParameters["methodCells"],
            "cellStains" : cellsParameters["cellStains"],
            "cytoStains" : cellsParameters["cytoStains"],
            "distMax" : cellsParameters["distMax"], 
            "radius" : cellsParameters["radius"]},
        "OrganoidParameters":{    
            "doOrganoid" : organoidParameters["doOrganoid"], 
            "channelOrganoid" : organoidParameters["channelOrganoid"],
            "methodOrganoid" : organoidParameters["methodOrganoid"],
            "parameterOrganoid" : my_window.Parameter1OrganoidSlider.value(), #organoidParameters["parameterOrganoid"],
            "keepLargestOrganoid" : organoidParameters["keepLargestOrganoid"],
            "keepMultipleOrganoids" : organoidParameters["keepMultipleOrganoids"], 
            "volumeMinOrganoid" : organoidParameters["volumeMinOrganoid"]},
        "ImageParameters":{        
            "dx" : imageParameters["dx"],
            "dy" : imageParameters["dy"],
            "dz" : imageParameters["dz"]},
        "PreprocessingParameters":{
            "listPreprocessing" : preprocessingList},
        "ExportParameters" :{
            "exportChannels" : dictExport["exportChannels"],
            "exportOverlays" : dictExport["exportOverlays"],
            "exportParameters" : dictExport["exportParameters"],
            "exportComposite" : dictExport["exportComposite"]
        }
    }
    with open(complete_path, "w") as file:
        json.dump(data, file)
    file.close()
        
def createDictParam(nucleiParameters, cellsParameters, organoidParameters, dictPreprocessing, imageParameters, dictExport):
    if Path(nucleiParameters["modelPath"]).exists() and len(nucleiParameters["modelPath"])>0:
        modelName = os.path.split(nucleiParameters["modelPath"])[-1]
        modelPath = os.path.split(nucleiParameters["modelPath"])[0]
    else :
        modelName = None
        modelPath = None
    index = my_window.FileListWidget.currentRow()
    FileInfo = fileInfos[index]
    volumeMin = int(nucleiParameters["volumeMin"]) if nucleiParameters["volumeMin"].isdigit() else None
    volumeMax = int(nucleiParameters["volumeMax"]) if nucleiParameters["volumeMax"].isdigit() else None
    if organoidParameters["volumeMinOrganoid"] is not None :
        volumeMinOrganoid = int(organoidParameters["volumeMinOrganoid"]) if organoidParameters["volumeMinOrganoid"].isdigit() else 0
    return {"filePath" : FileInfo.MainPath(), 
        "channelNuclei" : int(nucleiParameters["channelNuclei"]) - 1 if FileInfo.channel>0 else None, 
        "channelCell" : (int(cellsParameters["channelCells"]) - 1) if (cellsParameters["doCells"] and FileInfo.channel>0) else None, 
        "channelOrganoid" : organoidParameters["channelOrganoid"] if (organoidParameters["doOrganoid"] and FileInfo.channel>0) else None, 
        "organoMethod" : organoidParameters["methodOrganoid"] if organoidParameters["doOrganoid"] else None,
        "organoidParameter" : organoidParameters["parameterOrganoid"],
        "keepLargestOrganoid" : organoidParameters["keepLargestOrganoid"],
        "volumeMinOrganoid" : volumeMinOrganoid if not organoidParameters["keepLargestOrganoid"] else None,
        "prep" : len(dictPreprocessing)>0, 
        "dict_preproc" : dictPreprocessing, 
        "factor_resize_Z" : float(nucleiParameters["resizeZ"]), 
        "factor_resize_Y" : float(nucleiParameters["resizeY"]), 
        "factor_resize_X" : float(nucleiParameters["resizeX"]), 
        "prob_thresh" : nucleiParameters["ProbThreshold"],
        "nms_thresh" : nucleiParameters["NmsThreshold"], 
        "volume_min" : volumeMin, 
        "volume_max" : volumeMax, 
        "modelName" : modelName,
        "modelPath" : modelPath,
        "defaultModel" : nucleiParameters["defaultModel"],
        "cell" : cellsParameters["doCells"], 
        "cell_seg_method" : cellsParameters["methodCells"] if cellsParameters["doCells"] else None, 
        "cellStains" : cellsParameters["cellStains"],
        "cytoStains" : cellsParameters["cytoStains"],
        "dx" : float(imageParameters["dx"]), 
        "dy" : float(imageParameters["dy"]), 
        "dz" : float(imageParameters["dz"]),  
        "radius_cell" : int(cellsParameters["radius"]) if cellsParameters["radius"].isdigit() else 5,
        "dist_max" : int(cellsParameters["distMax"]) if cellsParameters["radius"].isdigit() else 14, 
        "exportChannels" : dictExport["exportChannels"],
        "exportOverlays" : dictExport["exportOverlays"],
        "exportParameters" : dictExport["exportParameters"],
        "exportComposite" :  dictExport["exportComposite"]  
    }

def updateNmsLabel(value):
    my_window.NmsValueLabel.setText(str(value/10))

def addPreprocessing():
    channelPreprocessing, methodPreprocessing, param1, param2 = my_window.getPreprocessingParam()
    if channelPreprocessing is not None :
        if methodPreprocessing in ["gaussian difference", "gaussian division"]:
            item = 'C' + channelPreprocessing + ' ' + methodPreprocessing + ' sigma ' + str(param1)
        elif methodPreprocessing == "unsharp mask":
            item = 'C' + channelPreprocessing + ' ' + methodPreprocessing + ' radius ' + str(param1) + ' amount ' + str(param2)
        else :
            item = 'C' + channelPreprocessing + ' ' + methodPreprocessing 
        my_window.setPreprocessingItem(item)

def removePreprocessing():
    my_window.PreprocessingListWidget.takeItem(my_window.PreprocessingListWidget.currentRow())

def getDictPreprocFromListPreproc(preprocessingList):
    dictPreprocessing = {}
    for name in preprocessingList:
        channel, preprocessObject = objectPreprocFromName(name)
        if channel in dictPreprocessing.keys():
            dictPreprocessing[channel].append(preprocessObject)
        else:
            dictPreprocessing[channel] = [preprocessObject]
    return dictPreprocessing

def objectPreprocFromName(name):
    nameSplit = name.split()
    channel = nameSplit[0][1] if len(nameSplit[0])>1 else "1"
    method = nameSplit[2]
    if method == "difference":
        sigma = int(nameSplit[4])
        preprocessObject = gaussianDifference(sigma)
    elif method == "division":
        sigma = int(nameSplit[4])
        preprocessObject = gaussianDivision(sigma)
    elif method == "mask":
        radius = int(nameSplit[4])
        amount = float(nameSplit[6])
        preprocessObject = unsharpMask(radius, amount)
    elif method == "bleaching":
        preprocessObject = correctBleaching()
    return channel, preprocessObject  
    
def updateProbLabel(value):
    my_window.ProbValueLabel.setText(str(value/10))
    
def updateParameter1OrganoidLabel(value):
    method = my_window.MethodOrganoidComboBox.currentText()
    if method == 'Dynamic Range Threshold':
        my_window.Parameter1OrganoidValueLabel.setText(str(value/10))
    elif method == 'Otsu Threshold':
        my_window.Parameter1OrganoidValueLabel.setText(str(on_slider_value_changed(value)))

def preprocessingComboboxChange(text):  
    if text in ["gaussian difference", "gaussian division"]:
        my_window.Parameter1PreprocessingLabel.setText('Sigma')
        my_window.Parameter1PreprocessingLabel.setVisible(True)
        my_window.Parameter1PreprocessingLineEdit.setVisible(True)
        my_window.Parameter2PreprocessingLabel.setVisible(False)
        my_window.Parameter2PreprocessingLineEdit.setVisible(False)
    elif text == "unsharp mask":
        my_window.Parameter1PreprocessingLabel.setText('Radius')
        my_window.Parameter1PreprocessingLabel.setVisible(True)
        my_window.Parameter1PreprocessingLineEdit.setVisible(True)
        my_window.Parameter2PreprocessingLabel.setText('Amount')
        my_window.Parameter2PreprocessingLabel.setVisible(True)
        my_window.Parameter2PreprocessingLineEdit.setVisible(True)
    elif text == "correct bleaching":
        my_window.Parameter1PreprocessingLabel.setVisible(False)
        my_window.Parameter1PreprocessingLineEdit.setVisible(False)
        my_window.Parameter2PreprocessingLabel.setVisible(False)
        my_window.Parameter2PreprocessingLineEdit.setVisible(False)

def organoidComboboxChange(text):
    if text == "Dynamic Range Threshold":
        my_window.Parameter1OrganoidLabel.setText('Dynamic Ratio ')
        my_window.Parameter1OrganoidSlider.setMinimum(0)
        my_window.Parameter1OrganoidSlider.setMaximum(10)
        my_window.Parameter1OrganoidSlider.setValue(1)
    elif text == "Otsu Threshold":
        default_log_value = 0.8
        default_slider_value = int(50 * (1 + math.log10(default_log_value)))
        my_window.Parameter1OrganoidSlider.setMinimum(1)
        my_window.Parameter1OrganoidSlider.setMaximum(100)
        my_window.Parameter1OrganoidSlider.setSingleStep(1)
        my_window.Parameter1OrganoidSlider.setPageStep(10)
        my_window.Parameter1OrganoidSlider.setValue(default_slider_value) 
        
        my_window.Parameter1OrganoidLabel.setText('Otsu Scale ')

def on_slider_value_changed(value):
        # Convert the linear slider value to a logarithmic value
        log_value = 10 ** ((value / 50) - 1)
        return round(log_value, 1)
        
def getCurrentImageMinMax(ch = None):    
    if ch is not None and ch != '':  
        channel = int(ch) - 1
    else:
        channel = None
    index = my_window.FileListWidget.currentRow()
    FileInfo = fileInfos[index]
    img = FileInfo.LoadImage()[:,:,:,channel] if channel is not None else FileInfo.LoadImage()
    return img.min(), np.median(img), img.max()
       
def ChangeOrganoidIcon(check):
    if check == 0:
        newIcon = QIcon(u":/logos/logos/notOrganoid.png")
        my_window.SettingsToolBox.setItemIcon(2, newIcon)
        my_window.SettingsToolBox.setItemText(2, "Organoid Segmentation (no detection)")
    elif check == 2:
        newIcon = QIcon(u":/logos/logos/organoid.png")
        my_window.SettingsToolBox.setItemIcon(2, newIcon)
        my_window.SettingsToolBox.setItemText(2, "Organoid Segmentation")

def ChangeCellIcon(check):
    if check == 0:
        newIcon = QIcon(u":/logos/logos/notCells.png")
        my_window.SettingsToolBox.setItemIcon(3, newIcon)
        my_window.SettingsToolBox.setItemText(3, "Cells Segmentation (no detection)")
    elif check == 2:
        newIcon = QIcon(u":/logos/logos/cells.png")
        my_window.SettingsToolBox.setItemIcon(3, newIcon)
        my_window.SettingsToolBox.setItemText(3, "Cells Segmentation")
              
def cellsComboboxChange(text):
    if text == "Watershed distance map":
        my_window.RadiusLineEdit.setVisible(True)
        my_window.RadiusLabel.setVisible(True)
    elif text == "Watershed intensity channel":
        my_window.RadiusLineEdit.setVisible(False)
        my_window.RadiusLabel.setVisible(False)

def preprocessingVisu(check):
    global selectedImage
    index = my_window.FileListWidget.currentRow()
    FileInfo = fileInfos[index]
    if check == 0:
        selectedImage = FileInfo.Display()
    elif check == 2:
        preprocessingList = my_window.getPreprocessingList()
        dictPreprocessing = getDictPreprocFromListPreproc(preprocessingList)
        selectedImage = apply_preproc(dictPreprocessing, selectedImage, FileInfo)
    if my_window.changeViewCheckBox.isChecked():
        my_window.clear3DWindow() #test
        view3D(spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)
    else:
        my_window.showImage(selectedImage, layer = currentLayer)

def openWindowVolume():
    montageNuclei = imread(dictPredicted["images_paths"]["montage_nuclei"])
    maskNuclei = imread(dictPredicted["images_paths"]["mask_nuclei"])
    dt = dictPredicted["dataframes"]["dt_nuclei"]
    my_window.openVolumeWindow(montageNuclei, maskNuclei, dt)

def setStatisticsTable():
    if currentDf is not None:
        my_window.StatisticsTableWidget.setRowCount(currentDf.shape[0])
        my_window.StatisticsTableWidget.setColumnCount(currentDf.shape[1])
        headers = [col for col in currentDf.columns if 'name_split' not in col]
        my_window.StatisticsTableWidget.setHorizontalHeaderLabels(headers)
        for row in range(currentDf.shape[0]):
            for col in range(currentDf.shape[1]):
                cell_value = currentDf.iloc[row, col]
                table_item = QTableWidgetItem(str(cell_value))
                my_window.StatisticsTableWidget.setItem(row, col, table_item)
    else:
        my_window.StatisticsTableWidget.clear()
        
    
def changeStatsTable(text):
    global currentDf
    if text == "Nuclei":
        currentDf = dictPredicted["dataframes"]["dt_nuclei"]
    elif text == "Cells":
        currentDf = dictPredicted["dataframes"]["dt_cell"]
    elif text == "Cytoplasm":
        currentDf = dictPredicted["dataframes"]["dt_cyto"]
    elif text == "Organoid":
        currentDf = dictPredicted["dataframes"]["dt_organo"]
    columns_to_remove = [col for col in currentDf.columns if 'name_split' in col]
    currentDf = currentDf.loc[:, ~currentDf.columns.isin(columns_to_remove)]
    setStatisticsTable()

def infoButtonOpen():
    handle = webbrowser.get()
    handle.open('OS_help.pdf')

def changeView(check):
    if check == 0: #3d is removed
        my_window.ImageViewerSlider.setEnabled(True)
        my_window.clear3DWindow() #test
        my_window.clearImageFrame()
        my_window.setImageWindows()
        my_window.ChannelVisualisationComboBox.removeItem(my_window.ChannelVisualisationComboBox.count()-1)
        if my_window.MaskVisualisationComboBox.findText("Cells")>=0:
            my_window.MaskVisualisationComboBox.addItem("Nuclei + Cells")
        my_window.showImage(selectedImage, channel = my_window.ChannelVisualisationComboBox.currentText(), layer = currentLayer)
    elif check == 2: #3d is checked
        my_window.ImageViewerSlider.setEnabled(False)
        my_window.ChannelVisualisationComboBox.addItem('None')
        
        ind = my_window.MaskVisualisationComboBox.findText("Nuclei + Cells")
        if ind >=0:
            my_window.MaskVisualisationComboBox.removeItem(ind)
        
        view3D(channel = my_window.ChannelVisualisationComboBox.currentText(), 
               spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)

def view3D(channel = None, layer = None, spacingX = None, spacingY = None, spacingZ = None, opacity = 1, listParam3d = None):
    global currentMask, currentLayer
    image_data, ch, actor = None, None, None
    index = my_window.FileListWidget.currentRow()
    FileInfo = fileInfos[index]
    
    spacingX = FileInfo.resolution[2] if spacingX is None else spacingX
    spacingY = FileInfo.resolution[1] if spacingY is None else spacingY
    spacingZ = FileInfo.resolution[0] if spacingZ is None else spacingZ
    
    dictParam3d = getDict3dFromList(listParam3d, FileInfo.channel) if listParam3d is not None else getDict3dFromList([], FileInfo.channel)
    
    my_window.clearImageFrame()
    my_window.setVTKImage()
    currentLayer, currentMask = getCurrentMask(my_window.MaskVisualisationComboBox.currentText(),
                                index = index, folder_mode = dictPredicted["folder"] if dictPredicted is not None else None)
    if channel is None:
        channel = my_window.ChannelVisualisationComboBox.currentText()
    if layer != '' and currentMask is not None:
        mask_data = numpyToVTK(currentMask, spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)
        actor = getSurface(mask_data, max_value = currentMask.max(), opacity = opacity, transparency = 0.0)
    colors = {0:(255, 0, 0), 1:(0, 255, 0), 2:(0,0,255), 3:(255,215,0), 4:(199,21,133), 5:(255,140,0), 6:(0,255,255)}
    if channel == "None":
        image_data = [numpyToVTK(np.zeros((selectedImage.shape[0], selectedImage.shape[1], selectedImage.shape[2])), spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)]
    elif FileInfo.channel == 0:
        image_data = [numpyToVTK(selectedImage, spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)]
    elif channel != "all":
        ch = int(channel) - 1
        image_data = [numpyToVTK(selectedImage[:,:,:,ch], spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)] 
    elif channel == "all":
        image_data = [numpyToVTK(selectedImage[:,:,:,0], spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)]
        for c in range(1, FileInfo.channel):
           image_data.append(numpyToVTK(selectedImage[:,:,:,c], spacingX = spacingX, spacingY = spacingY, spacingZ = spacingZ)) 
    if image_data is not None:       
        for i,im in enumerate(image_data):
            min_value = dictParam3d[i][0] if ch is None else dictParam3d[ch][0]
            max_value = dictParam3d[i][1] if ch is None else dictParam3d[ch][1]
            volume = getVolumes(im, min_value = min_value, max_value = max_value, transparency = 1.0, color = colors[i]) if ch is None else \
                 getVolumes(im, min_value = min_value, max_value = max_value, transparency = 1.0, color = colors[ch])
            my_window.addVTKImage(volume = volume)    
    if actor is not None:
        my_window.addVTKImage(actor=actor)
        
    my_window.finishVisuVTK()

def getDict3dFromList(listItems, nbchannels):
    dict3dParam = {key: [50, 200] for key in range(nbchannels)} if nbchannels>0 else {0: [50, 200]}
    for i, el in enumerate(listItems):
        list_val = el.split()
        channel = 0 if len(list_val[0])==1 else int(list_val[0][1])-1
        if list_val[1] == 'min':
            dict3dParam[channel][0] = float(list_val[2])
        elif list_val[1] == 'max':
             dict3dParam[channel][1] = float(list_val[2])
    return dict3dParam
             
def ParametersWindow():
    index = my_window.FileListWidget.currentRow()
    FileInfo = fileInfos[index]
    my_window.spacingX = FileInfo.resolution[2] if my_window.spacingX is None else my_window.spacingX
    my_window.spacingY = FileInfo.resolution[1] if my_window.spacingY is None else my_window.spacingY
    my_window.spacingZ = FileInfo.resolution[0] if my_window.spacingZ is None else my_window.spacingZ
    opacityValueSlider = 10 if my_window.opacityValueSlider is None else my_window.opacityValueSlider
    my_window.open3dParametersWindow(FileInfo, my_window.spacingX, my_window.spacingY, my_window.spacingZ, opacityValueSlider, my_window.ValuesList)
    if my_window.changeViewCheckBox.isChecked():
        my_window.clear3DWindow()
        my_window.clearImageFrame()
        my_window.setVTKImage()
        view3D(channel = my_window.ChannelVisualisationComboBox.currentText(),
               spacingX = my_window.spacingX, spacingY = my_window.spacingY, spacingZ = my_window.spacingZ, 
               opacity = 1 if my_window.opacityValueSlider is None else my_window.opacityValueSlider/10, listParam3d = my_window.ValuesList)

def connections(window : OrganoSegmenterWindow):      
    window.BrowseFolderButton.clicked.connect(openFolder)
    window.BrowseParametersButton.clicked.connect(openJsonParameters)
    window.ChangeModelButton.clicked.connect(chooseModel)
    window.NmsSlider.valueChanged.connect(updateNmsLabel)
    window.ProbSlider.valueChanged.connect(updateProbLabel)
    window.Parameter1OrganoidSlider.valueChanged.connect(updateParameter1OrganoidLabel)
    window.FileListWidget.itemClicked.connect(imageSelected)
    window.ImageViewerSlider.valueChanged.connect(zViewChange)
    window.ChannelVisualisationComboBox.currentTextChanged.connect(channelViewChange)
    window.FeaturePlotComboBox.currentTextChanged.connect(changePlotFeature)
    window.PlotTypeComboBox.currentTextChanged.connect(changePlotType)
    window.RightSideTabWidget.currentChanged.connect(createPlot)
    window.DetectOrganoidCheckBox.stateChanged.connect(ChangeOrganoidIcon)
    window.DetectCellsCheckBox.stateChanged.connect(ChangeCellIcon)
    window.ProcessFileButton.clicked.connect(processFile)
    window.MaskVisualisationComboBox.currentTextChanged.connect(changeLayer)
    window.AddPreprocessingButton.clicked.connect(addPreprocessing)
    window.RemovePreprocessingButton.clicked.connect(removePreprocessing)
    window.MethodPreprocessingComboBox.currentTextChanged.connect(preprocessingComboboxChange)
    window.MethodOrganoidComboBox.currentTextChanged.connect(organoidComboboxChange)
    window.MethodCellsComboBox.currentTextChanged.connect(cellsComboboxChange)
    window.PreprocessingCheckBox.stateChanged.connect(preprocessingVisu)
    window.AutoResizeWindowButton.clicked.connect(my_window.openAutoResizeWindow)
    window.ExploreVolumesWindowButton.clicked.connect(openWindowVolume)
    window.TableComboBox.currentTextChanged.connect(changeStatsTable)
    window.InfoButton.clicked.connect(infoButtonOpen)
    window.changeViewCheckBox.stateChanged.connect(changeView)
    window.View3DPushButton.clicked.connect(ParametersWindow)
        
if __name__ == "__main__":
    
    dark_palette = create_dark_palette()
    app.setPalette(dark_palette)
    app.setStyle("Fusion")
    connections(my_window)
    my_window.show()
    app.exec()
    
