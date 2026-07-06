import ctypes
import os
import sys


def hide_console():
    if sys.platform == "win32":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        os.system("echo off")

hide_console()
import OS_Manager
from PySide6.QtTest import QTest
import src.features_global as glob
import OS_Pannel_Window as OPW
from unittest.mock import MagicMock, patch
from pathlib import Path
import numpy as np
import pandas as pd
from PySide6 import QtCore
from PySide6.QtCore import  Qt, QSize, QRect
from PySide6.QtGui import ( QCursor, QKeySequence, QStandardItemModel, QStandardItem,QDoubleValidator)
from PySide6.QtWidgets import ( QLabel,QTableView, QHeaderView, QComboBox,QPushButton, QCheckBox, QFileDialog, QMessageBox, QVBoxLayout,QHBoxLayout,QLineEdit,QDialog,QDialogButtonBox,QStyle)
import shutil
import inspect
import json
from tifffile import imread
from OS_Density import comput_density_stats
demo_im_fold = Path("images")
info_dict = {"models": {}}

if Path(r"models\models_info.json").exists():
    with open(r"models\models_info.json", 'r') as json_file:
        info_dict = json.load(json_file)


def update_OS_UI():
    OS_Manager.my_window.setWindowTitle('3DCellScope')
    OS_Manager.app.setPalette(OS_Manager.create_dark_palette())
    OS_Manager.app.setStyle("Fusion")
    OS_Manager.my_window.ImageFolder.setVisible(False)
    OS_Manager.my_window.ExploreVolumesWindowButton.setVisible(False)
    OS_Manager.my_window.RightSideTabWidget.removeTab(2)
    OS_Manager.my_window.RightSideTabWidget.removeTab(1)
    OS_Manager.my_window.VolumeMinLineEdit.setText("300")
    OS_Manager.my_window.VolumeMaxLineEdit.setText("3000")
    OS_Manager.my_window.ChangeModelButton.setVisible(True)
    OS_Manager.my_window.ChangeModelTextBrowser.setVisible(False)
    OS_Manager.my_window.DefaultModelComboBox.clear()
    [OS_Manager.my_window.DefaultModelComboBox.addItem(el,userData=Path("models")/el) for el in info_dict["models"].keys() if (Path("models")/el).is_dir()]
    OS_Manager.my_window.DefaultModelComboBox.addItem("CellposeSAM", userData="CellposeSAM")
    OS_Manager.my_window.DefaultModelComboBox.setCurrentIndex(OS_Manager.my_window.DefaultModelComboBox.findText("DeepStar3D"))
    OS_Manager.my_window.removeCurentModelButton = QPushButton(OS_Manager.my_window.style().standardIcon(QStyle.SP_LineEditClearButton),"",OS_Manager.my_window.ChangeModelTextBrowser.parent())
    OS_Manager.my_window.removeCurentModelButton.setGeometry(OS_Manager.my_window.DefaultModelComboBox.x()+OS_Manager.my_window.DefaultModelComboBox.width(), OS_Manager.my_window.DefaultModelComboBox.y(),25,25)
    OS_Manager.my_window.removeCurentModelButton.setStyleSheet("background-color: transparent;border: none;")
    [OS_Manager.my_window.MethodPreprocessingComboBox.removeItem(3-i) for i in range(3)]
    OS_Manager.my_window.ProbSlider.setValue(5)
    OS_Manager.my_window.ProbValueLabel.setText("0.5")
    OS_Manager.my_window.SettingsToolBox.setCurrentIndex(1)
    OS_Manager.my_window.ProcessFileButton.setText("Process Image")
    OS_Manager.my_window.ExportOverlaysCheckBox.setChecked(False)
    OS_Manager.my_window.ExportCompositeCheckBox.setChecked(False)
    OS_Manager.my_window.ExportParametersCheckBox.setChecked(True)
    OS_Manager.my_window.ExportToolBox.setVisible(True)
    OS_Manager.my_window.autoResizeButton = QCheckBox("Fit Model Resolution",OS_Manager.my_window.ResampleByGroupBox)
    OS_Manager.my_window.autoResizeButton.setGeometry(QRect(10, 50, 161, 24))
    OS_Manager.my_window.autoResizeButton.clicked.connect(adjustSize2ModelAuto)
    OS_Manager.my_window.DefaultModelComboBox.currentIndexChanged.connect(lambda X:adjustSize2ModelAuto() )
    for el in [OS_Manager.my_window.DeltaXLineEdit,OS_Manager.my_window.DeltaYLineEdit,OS_Manager.my_window.DeltaZLineEdit]:
        el.textChanged.connect(adjustSize2ModelAuto)


    OS_Manager.my_window.AutoResizeWindowButton.setVisible(False)

    OS_Manager.ProgressBarWindow = getFakeProgressbar()

def update_NX_UI():
    glob.initialyse_context()
    glob.CONTEXT.main_windows.menubar.setVisible(False)
    glob.CONTEXT.main_windows.toolBox.removeItem(0)
    glob.CONTEXT.main_windows.page_2.setVisible(False)
    glob.CONTEXT.main_windows.pcaModeComboBox.setCurrentIndex(1)
    def hide_layout_content(layout):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setVisible(False)
    hide_layout_content(glob.CONTEXT.main_windows.horizontalLayout_4)
    hide_layout_content(glob.CONTEXT.main_windows.horizontalLayout_5)
    hide_layout_content(glob.CONTEXT.main_windows.horizontalLayout_7)
    hide_layout_content(glob.CONTEXT.main_windows.horizontalLayout_10)
    hide_layout_content(glob.CONTEXT.main_windows.horizontalLayout_11)
    glob.CONTEXT.main_windows.summaryPlottButton.setText("Testing")
    glob.CONTEXT.main_windows.toolBox_3.setCurrentIndex(0)
    glob.CONTEXT.main_windows.page_5.setVisible(False)
    glob.CONTEXT.main_windows.toolBox_3.removeItem(1)
    glob.CONTEXT.main_windows.toolBox_2.setItemText(0,"Data Selection")
    glob.CONTEXT.main_windows.toolBox.setItemText(0,"Feature Selection")
    glob.CONTEXT.main_windows.toolBox_3.setItemText(0,"Data Analysis")
    glob.CONTEXT.main_windows.verticalLayout.insertWidget(0,glob.CONTEXT.main_windows.toolBox_2)
    glob.CONTEXT.main_windows.toolBox_2.setMinimumSize(QSize(0, 200))
    glob.CONTEXT.main_windows.toolBox.setMinimumSize(QSize(0, 280))
    glob.CONTEXT.main_windows.excludeSelectedDescriptorButton.setText("Remove Selected")
    glob.CONTEXT.main_windows.resetDescriptorFilterButton.setText("Restore Excluded Features")
    glob.CONTEXT.main_windows.aggregateDataButton.setVisible(False)
    glob.CONTEXT.main_windows.featureGateButton2 = QPushButton("Feature Gate")
    glob.CONTEXT.main_windows.horizontalLayout_3.insertWidget(3, glob.CONTEXT.main_windows.featureGateButton2)
def update_OPW_UI():
    OPW.window = OPW.PannelWindow()
    OS_Manager.my_window.RightSideTabWidget.addTab(OPW.window,"Data Exploration")
    OPW.get_dataframe = lambda : glob.CONTEXT.data_manager.data.reset_index()
    OPW.save_fusion_dataframe_with_pca = save_fusion_dataframe
    OPW.show_on_image = OPW.pnw.Button(name="Show Selection", description="Highlight the selected nuclei on the active image.", disabled = True)
    OPW.hv_layout[4].insert(1,OPW.show_on_image)
    OPW.window.plot_widget.load("http://localhost:5006%s"%next(iter(OPW.pannels)))


def toggle_model_load_button():
    is_stardist = OS_Manager.my_window.DefaultModelComboBox.currentData() != "CellposeSAM"
    OS_Manager.my_window.ChangeModelButton.setText("Load Stardist Model" if is_stardist else "CellposeSAM (built-in)")
    OS_Manager.my_window.ChangeModelButton.setEnabled(is_stardist)

def connect_apps():
    OS_Manager.labelSelection = set()
    OS_Manager.hooverLab = HooverLab()
    OS_Manager.maskNameToDt = {'Nuclei':'nuclei', 'Cells':'cell', 'Nuclei + Cell':'cell', 'Organoid':'organo', "None":"None", '':"None",}
    OS_Manager.currentImageDf = None
    OS_Manager.interactiveLayer = None
    OS_Manager.getCurrentMask = add_interactive_layer_to_get_current_mask_decorator(OS_Manager.getCurrentMask)
    OS_Manager.imageSelected = image_clicked_decorator(OS_Manager.imageSelected)
    OS_Manager.connections(OS_Manager.my_window)
    OS_Manager.my_window.ProcessFileButton.clicked.disconnect()
    OS_Manager.my_window.ChangeModelButton.clicked.disconnect()
    OS_Manager.my_window.ChangeModelButton.clicked.connect(loadModel)
    OS_Manager.my_window.DefaultModelComboBox.currentIndexChanged.connect(toggle_model_load_button)
    toggle_model_load_button()
    OS_Manager.my_window.ProcessFileButton.clicked.connect(process_decorator(process_file_and_density ))
    OS_Manager.my_window.showImage = add_selection_layer_decorator_to_image_display(OS_Manager.my_window.showImage)
    OS_Manager.my_window.removeCurentModelButton.clicked.connect(lambda:OS_Manager.my_window.DefaultModelComboBox.removeItem(OS_Manager.my_window.DefaultModelComboBox.currentIndex()))
    glob.CONTEXT.app_manager.add_feature_gate=filter_event_link_to_image_decorator(glob.CONTEXT.app_manager.add_feature_gate)
    glob.CONTEXT.app_manager.remove_selected_groupe=filter_event_link_to_image_decorator(glob.CONTEXT.app_manager.remove_selected_groupe)
    glob.CONTEXT.app_manager.keep_only_selected_groupe=filter_event_link_to_image_decorator(glob.CONTEXT.app_manager.keep_only_selected_groupe)
    glob.CONTEXT.app_manager.undo_last_groupe_filter=filter_event_link_to_image_decorator(glob.CONTEXT.app_manager.undo_last_groupe_filter)
    glob.CONTEXT.app_manager.reset_group_filter=filter_event_link_to_image_decorator(glob.CONTEXT.app_manager.reset_group_filter)
    glob.CONTEXT.app_manager.density_plot = data_analysis_decorator(glob.CONTEXT.app_manager.density_plot,{'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :1})
    glob.CONTEXT.app_manager.bar_plot = data_analysis_decorator(glob.CONTEXT.app_manager.bar_plot,{'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :1})
    glob.CONTEXT.app_manager.box_plot = data_analysis_decorator(glob.CONTEXT.app_manager.box_plot,{'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :1})
    glob.CONTEXT.app_manager.scatter_plot = data_analysis_decorator(glob.CONTEXT.app_manager.scatter_plot,{'all_features' : 2,'feature_selected' : 2,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :1})
    glob.CONTEXT.app_manager.componnent_analysis_plot = data_analysis_decorator(glob.CONTEXT.app_manager.componnent_analysis_plot,{'all_features' : 3,'feature_selected' : 0,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :1})
    glob.CONTEXT.app_manager.summary_plot = data_analysis_decorator(glob.CONTEXT.app_manager.summary_plot,{'all_features' : 1,'feature_selected' : 0,'data_group_selected' : 1,'data_group_control' : 1,'all_data_groups' :2})
    glob.CONTEXT.app_manager.cross_test_plot = data_analysis_decorator(glob.CONTEXT.app_manager.cross_test_plot,{'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 1,'data_group_control' : 0,'all_data_groups' :2})

    glob.CONTEXT.main_windows.connect_components()
    glob.CONTEXT.main_windows.featureGateButton2.clicked.connect(filter_event_link_to_image_decorator(data_analysis_decorator(add_feature_gate_from_selection,{'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 0,'data_group_control' : 0,'all_data_groups' :1})))

    # OS_Manager.my_window.RightSideTabWidget.currentChanged.connect(OPW.window.plot_widget.reload)
    OS_Manager.my_window.image_fig.canvas.mpl_connect('button_press_event', imageClicked)
    OS_Manager.my_window.image_fig.canvas.mpl_connect('motion_notify_event', imageHoovered)
    OS_Manager.my_window.setImageWindows = set_image_window_decorator(OS_Manager.my_window.setImageWindows)

    OPW.show_on_image.on_click(show_pannel_selection)
    OPW.filter_in_selection.param.unwatch(OPW.filter_in_selection.param.watchers["value"]["value"][1])
    OPW.filter_out_selection.param.unwatch(OPW.filter_out_selection.param.watchers["value"]["value"][1])
    OPW.filter_in_selection.param.watch(filterOPWSelection,"value")
    OPW.filter_out_selection.param.watch(filterOPWSelection,"value")
    OPW.update_source_dataframe = updateFusionDf
    OPW.save_fusion_dataframe_with_pca = save_fusion_dataframe


def start():
    OS_Manager.splash.close()
    OS_Manager.my_window.show()
    with patch('OS_Manager.QFileDialog.getExistingDirectory', return_value="images"):
        OS_Manager.openFolder()

    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle("Warning: Reduced Software Version")
    msg_box.setText("Dear user,\n\n"
                    "You are currently using a version of the software with limited functionality compared "
                    "to the full version. If you require access to additional "
                    "features or wish to discuss your specific needs, please "
                    "don't hesitate to contact us directly at our email addresses: \n"
                    "mbianne@nus.edu.sg or victor.racine@quantacell.com\n\n"
                    "Thank you for using our software.")
    msg_box.setInformativeText("This version is intended for demonstration and evaluation purposes only.")
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.setDefaultButton(QMessageBox.Ok)
    # msg_box.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowSystemMenuHint)
    # msg_box.setWindowFlags(msg_box.windowFlags() & ~Qt.WindowCloseButtonHint)
    msg_box.exec()


    OS_Manager.app.exec()
#region Demo functionnality
class DataFramePopup(QTableView):
    def __init__(self, dataframe, parent=None):
        super(DataFramePopup, self).__init__(parent)
        self.init_ui(dataframe)

    def init_ui(self, dataframe):
        table_model = self.get_table_model(dataframe)
        self.setModel(table_model)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        size_hint = self.viewportSizeHint()
        cursor_pos = QCursor.pos()
        self.setGeometry(cursor_pos.x()-5, cursor_pos.y()-5,min(size_hint.width()+10,1000),min(size_hint.height()+10,800))


    def get_table_model(self, dataframe):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(dataframe.columns)
        model.setVerticalHeaderLabels(dataframe.index)
        for row in range(dataframe.shape[0]):
            for col in range(dataframe.shape[1]):
                item = QStandardItem(str(dataframe.iloc[row, col]))
                model.setItem(row, col, item)
        return model
    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copySelection()
        else:
            super(DataFramePopup, self).keyPressEvent(event)

    def copySelection(self):
        copied = ''
        select = self.selectionModel()
        if not select.hasSelection(): return
        df = pd.pivot(pd.DataFrame([[el.row(), el.column(),el.data()] for el in select.selectedIndexes()],columns = ["row","col","val"]),index = "row", columns = "col", values = "val")
        # df.columns = [self.horizontalHeader().model().headerData(el,Qt.Horizontal) for el in df.columns]
        # df.index = [self.verticalHeader().model().headerData(el,Qt.Vertical) for el in df.index]
        df.to_clipboard(sep='\t', line_terminator='\n')
class HooverLab(QLabel ):
    def __init__(self,*args,**kwargs):
        super(HooverLab, self).__init__(*args,**kwargs)
        self.setWindowFlags(Qt.FramelessWindowHint| Qt.Tool | Qt.SplashScreen   | Qt.WindowStaysOnTopHint )#
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.NoFocus)
    def update(self,lab=None, **kwargs):
        if lab is None:
            self.setText("")
        else:
            self.setText(str(lab))
            self.adjustSize()
            self.move(QCursor.pos())
            self.show()
class HoveringListWidget(QComboBox):
    def __init__(self, list_el = ["titi","toto"], parent = None):
        super(HoveringListWidget, self).__init__(parent)
        cursor_pos = QCursor.pos()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.addItems(list_el)
        self.setGeometry(cursor_pos.x()-5, cursor_pos.y()-5, 100, 20)
        self.setContentsMargins(0, 0, 0, 0)
        self.showPopup()
    def mouseMoveEvent(self, event):
        if not self.view().rect().contains(event.pos()):
            self.close()

class LoadModelInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Model Informations")

        layout1 = QVBoxLayout()
        layout2 = QHBoxLayout()

        self.model_name_edit = QLineEdit()
        layout1.addWidget(QLabel("Model Name:"))
        layout1.addWidget(self.model_name_edit)
        layout1.addWidget(QLabel("Training model voxel resolution in micron (dx,dy,dz):"))

        self.d_spins = {}
        for el in ['dx','dy','dz']:
            spin = QLineEdit("1.0")
            spin.setValidator(QDoubleValidator())
            layout2.addWidget(QLabel(el))
            layout2.addWidget(spin)
            self.d_spins[el] = spin

        layout1.addLayout(layout2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout1.addWidget(button_box)

        self.setLayout(layout1)

    @staticmethod
    def get_inputs():
        dialog = LoadModelInputDialog()
        result = dialog.exec()
        model_name = dialog.model_name_edit.text()

        model_resolution = {k:float(v.text()) for k,v in dialog.d_spins.items()}

        return model_name, model_resolution, result == QDialog.Accepted

def getFakeProgressbar():
    class fake_popup(object):
        def updateProgressBar(self,*args,**kwargs):
            pass
    return fake_popup

def getImageDataframe(object_name, file_name):
    if glob.CONTEXT.data_manager.data is None or glob.CONTEXT.data_manager.data.empty or file_name not in glob.CONTEXT.data_manager.data.index:
        empty_index = pd.MultiIndex.from_arrays([[], []], names=['file', 'corresponding_organoid'])
        return pd.DataFrame([],index = empty_index)
    element_indexer = "cell_Id" if object_name != 'organo' else "corresponding_organoid"
    d = glob.CONTEXT.data_manager.data.set_index(element_indexer,append=True)
    cols = [col for col in glob.CONTEXT.data_manager.descriptors.keys() if "%s_"%object_name in col and col != "cell_Id"]
    d=d.loc[file_name,cols].dropna(axis='columns')
    if object_name == 'organo': d = d.groupby(level=0).apply(lambda X:X.iloc[0,:])
    return d.rename(columns = lambda x:("foo"+x).replace("foo%s_"%object_name,""))

def process_decorator(f):
    """send fusion df data to the statistical analysis tool after a processing funciton
    Args:
        f (method): processing funciton
    """
    def wrapper(*args,**kwargs):
        glob.CONTEXT.data_manager.set_data(pd.DataFrame())
        OS_Manager.interactiveLayer = None
        adjustSize2ModelAuto()
        result = f(*args, **kwargs)
        if OS_Manager.dictPredicted["folder"]:
            fusion_path = next(Path(OS_Manager.dictPredicted["result_folder"]).glob("fusion-statistics.csv"))
        else:
            fusion_path = next(Path(OS_Manager.dictPredicted["result_folder"]).glob("*fusion-statistics.csv"))
        OPW.fusion_path = str(fusion_path)
        glob.CONTEXT.app_manager.fusion_path = str(fusion_path)
        glob.CONTEXT.app_manager.load_csv(fusion_path)
        features = glob.CONTEXT.data_manager.features
        glob.CONTEXT.app_manager.chose_meta_data([f for f in features if "file" in f])
        glob.CONTEXT.data_manager.descriptors["cell_Id"].ignore = True
        glob.CONTEXT.app_manager.update_descriptor_list()
        glob.CONTEXT.app_manager.data_group_item_clicked(0,0)
        OS_Manager.interactiveLayer = np.zeros_like(OS_Manager.currentLayer)
        OPW.window.plot_widget.reload()
        return result
    return wrapper


def process_file_and_density():
    OS_Manager.my_window.ChangeModelTextBrowser.setText(str(OS_Manager.my_window.DefaultModelComboBox.currentData()))

    model_name = OS_Manager.my_window.getNucleiParam()["defaultModel"]

    if model_name == "CellposeSAM":
        dictPredicted = OS_Manager.process_with_cellpose()
    else:
        dictPredicted = OS_Manager.processFile()

    if not dictPredicted or not dictPredicted.get("result_folder"):
        print("Processing failed or was cancelled.")
        return

    fusion_path = next(Path(dictPredicted["result_folder"]).glob(
        "fusion-statistics.csv" if OS_Manager.dictPredicted["folder"] else "*fusion-statistics.csv"))
    fusiondf = pd.read_csv(fusion_path)
    if dictPredicted["images_paths"].get("mask_organo") is not None:
        mask = imread(dictPredicted["images_paths"]["mask_organo"])
    elif dictPredicted["images_paths"].get("mask_nuclei") is not None:
        mask = np.ones(imread(dictPredicted["images_paths"]["mask_nuclei"]).shape)
    else:
        # Handle case where no mask is available
        print("Warning: No mask found for density analysis.")
        return dictPredicted

    try:
        new_fusion_df = comput_density_stats(fusiondf, mask)
        new_fusion_df.to_csv(fusion_path)
    except Exception as e:
        print(f"Could not process density analysis: {e}")
    return dictPredicted


def add_selection_layer_decorator_to_image_display(f):
    argspec = inspect.getfullargspec(f)
    argnames = argspec.args[1:]

    def wrapper(*args, **kwargs):
        args = list(args)
        # Map positional arguments to keyword arguments
        for i, arg_name in enumerate(argnames):
            if i < len(args):
                if arg_name not in kwargs:
                    kwargs[arg_name] = args[i]

        if kwargs.get("selectedImage") is None:
            # If selectedImage is still None, we cannot proceed.
            # This might happen if the function is called without an image.
            # We can pass the call to the original function to handle it.
            return f(*args, **kwargs)

        z = min(OS_Manager.my_window.ImageViewerSlider.value(), len(kwargs["selectedImage"]) - 1)

        layer = kwargs.get("layer")

        if layer is not None and OS_Manager.interactiveLayer is not None and not np.all(
                OS_Manager.interactiveLayer[z] == 0):
            layer = OS_Manager.interactiveLayer[z].copy()
            layer[..., :3] = np.clip(layer[..., :3] + kwargs["layer"][z, ..., :3], 0, 255)

        elif layer is not None:
            layer = layer[z]

        kwargs["layer"] = layer
        kwargs["z"] = 0
        kwargs["selectedImage"] = kwargs["selectedImage"][z, None]
        return f(**kwargs)

    return wrapper

def add_interactive_layer_to_get_current_mask_decorator(f):
    def wrapper(*args,**kwargs):
        ret = f(*args,**kwargs)
        if ret[1] is not None and not glob.CONTEXT.data_manager.data.empty:
            OS_Manager.interactiveLayer = np.zeros(ret[1].shape+(4,),dtype=np.int16)
        return ret

    return wrapper
def filter_event_link_to_image_decorator(f):
    def wrapper(*args,**kwargs):
        mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
        im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
        old_df = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
        ret = f(*args, **kwargs)
        if OS_Manager.currentMask is None: return ret

        new_df = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
        OS_Manager.currentImageDf = old_df
        for lab in old_df.index:
            if lab not in new_df.index:
                hideLabel(lab)
        OS_Manager.currentImageDf = new_df
        for lab in new_df.index:
            if lab not in old_df.index:
                unhideLabel(lab)
        OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)
        OPW.window.plot_widget.reload()
        return ret

    return wrapper

def set_image_window_decorator(f):
    def wrapper(*args,**kwargs):
        ret = f(*args,**kwargs)
        OS_Manager.my_window.image_fig.canvas.mpl_connect('button_press_event', imageClicked)
        OS_Manager.my_window.image_fig.canvas.mpl_connect('motion_notify_event', imageHoovered)
        OS_Manager.currentLayer,OS_Manager.currentMask = OS_Manager.getCurrentMask(OS_Manager.my_window.MaskVisualisationComboBox.currentText(),
                                OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name)
        return ret
    return wrapper

default_descriptors = ['nuclei_volume_um3','nuclei_elongation','nuclei_roundness']

def data_analysis_decorator(f, requirement={'all_features' : 1,'feature_selected' : 1,'data_group_selected' : 1,'data_group_control' : 1,'all_data_groups' :1}):
    def wrapper(*args,**kwargs):
        vals = data_analysis_requirement_checker()
        for k in requirement.keys():
            if len(vals[k]) < requirement[k]:
                QMessageBox.critical(None,"Invalid parameters", "missing parameters for data analysis: %s"%k)
                return

        return f(*args,**kwargs)
    return wrapper

def data_analysis_requirement_checker():
    return{
    'all_features' : set(glob.CONTEXT.data_manager.get_valid_descriptor_names()),
    'feature_selected' : set(glob.CONTEXT.main_windows.get_selected_descriptors()),
    'data_group_selected' : set(glob.CONTEXT.main_windows.get_selected_group()),
    'data_group_control' : set(glob.CONTEXT.data_manager.get_control_index()),
    'all_data_groups' : set(glob.CONTEXT.data_manager.get_unique_index()),
    }

def image_clicked_decorator(f):
    def wrapper(*args,**kwargs):
        OS_Manager.interactiveLayer = None
        return f(*args,**kwargs)
    return wrapper

def imageHoovered(event):
    z,x,y = OS_Manager.my_window.getImageClickEventPosition(event)
    if x<0 or y<0 or OS_Manager.currentMask is None or OS_Manager.currentMask[z,y,x]==0:
        OS_Manager.hooverLab.update(None)
        return
    else:
        lab = OS_Manager.currentMask[z,y,x]
        mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
        im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
        d = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
        if lab not in d.index:
            OS_Manager.hooverLab.update(None)
        else:
            OS_Manager.hooverLab.update(lab)

def imageClicked(event):
    if event.button == 1:
        selectLabelClick(event)
    elif event.button == 3:
        showObjectMenue()
    OS_Manager.hooverLab.update(None)

def showObjectMenue():
    if OS_Manager.currentMask is None: return
    OS_Manager.my_window.temp_menu = HoveringListWidget(["close", "select all"]+(["unselect all", "info selected", "remove selected"] if len(OS_Manager.labelSelection)>0 else []) + ["feature gate", "restore", "restore all"])
    OS_Manager.my_window.temp_menu.activated.connect(ObjectMenue)

def ObjectMenue(index:int):
    mode = len(OS_Manager.labelSelection)>0
    if index == 1: selectAllLabel()
    elif index == 2+3*mode: glob.CONTEXT.main_windows.featureGateButton2.click()
    elif index == 3+3*mode: glob.CONTEXT.main_windows.filterGroupButtonBack.click()
    elif index == 4+3*mode: glob.CONTEXT.main_windows.filterGroupButtonReset.click()
    elif index == 2: unSelectAllLabel()
    elif index == 3: get_info()
    elif index == 4: filterSelected()

def isLabFiltered(lab):
    return lab not in OS_Manager.currentImageDf.index

def selectLabelClick(event):
    z,x,y = OS_Manager.my_window.getImageClickEventPosition(event)
    if x<0 or y<0: return
    print(z,x,y)
    if OS_Manager.currentMask is None: return
    lab = OS_Manager.currentMask[z,y,x]
    mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
    im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
    OS_Manager.currentImageDf = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
    if lab == 0 or isLabFiltered(lab):return
    if lab in OS_Manager.labelSelection: unSelectLabel(lab)
    else : addLabelToSelection(lab)
    print("labels = ", OS_Manager.labelSelection)
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, z = z, layer = OS_Manager.currentLayer)



def getlabMask(lab):
    if lab in OS_Manager.currentImageDf.index:
        bb_x,bb_y,bb_z,bb_w,bb_h,bb_wz = OS_Manager.currentImageDf.loc[lab,["bb_X","bb_Y","bb_Z","bb_W","bb_H","bb_WZ"]].values.astype(int)
        bbox = (slice(bb_z,bb_z+bb_wz),slice(bb_y,bb_y+bb_h),slice(bb_x,bb_x+bb_w))
    else:
        bbox = (slice(None,None),slice(None,None),slice(None,None))
    mask = OS_Manager.currentMask[bbox]==lab
    return mask, bbox

def addLabelToSelection(lab):
        mask, bbox = getlabMask(lab)
        # OS_Manager.currentLayer[bbox][mask,3]= np.clip(OS_Manager.currentLayer[bbox][mask,3],150,255)
        OS_Manager.interactiveLayer[bbox][mask,3]= np.clip(OS_Manager.currentLayer[bbox][mask,3],150,255)
        OS_Manager.labelSelection.add(lab)

def unSelectLabel(lab):
        mask, bbox = getlabMask(lab)
        OS_Manager.interactiveLayer[bbox][mask,3]=0
        OS_Manager.labelSelection.remove(lab)

def get_info():
    mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
    im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
    d = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
    s = list(d.columns).index("volume")+1
    df = d.iloc[:,s:].loc[list(OS_Manager.labelSelection)]
    df.columns = [el.replace("_"," ") for el in df.columns]
    col = [el.replace("_"," ") for el in df.columns if 'bb ' not in el and 'centroid' not in el and ((el+" um") not in df.columns)]
    df:pd.DataFrame = df[col]
    df.index = df.index.astype(int).astype(str)
    OS_Manager.my_window.dataframe_popup =  DataFramePopup(df.T)
    OS_Manager.my_window.dataframe_popup.setWindowTitle("Features")
    OS_Manager.my_window.dataframe_popup.show()

def filterSelected():
    mask_name = OS_Manager.maskNameToDt[OS_Manager.my_window.MaskVisualisationComboBox.currentText()]
    querry = """`file` != "%s" | `%s` not in [%s]"""%(OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name , "cell_Id" if mask_name !="organo" else "corresponding_organoid",  ', '.join(map(str, OS_Manager.labelSelection)))
    glob.CONTEXT.data_manager.drop_data_with_querry(querry)
    for lab in OS_Manager.labelSelection:
        hideLabel(lab)
    OS_Manager.labelSelection = set()

    OPW.window.plot_widget.reload()
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)

def hideLabel(lab):
    mask, bbox = getlabMask(lab)
    OS_Manager.interactiveLayer[bbox][mask,3] = -1

def unhideLabel(lab):
    mask, bbox = getlabMask(lab)
    OS_Manager.interactiveLayer[bbox][mask,3] = 0

def selectAllLabel():
    if OS_Manager.currentMask is None : return
    mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
    im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
    OS_Manager.currentImageDf = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
    for lab in OS_Manager.currentImageDf.index:
        if lab==0 or lab in OS_Manager.labelSelection :continue
        addLabelToSelection(lab)
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)

def getFileParams():
    nucleiParameters = OS_Manager.my_window.getNucleiParam()
    cellsParameters = OS_Manager.my_window.getCellsParam()
    organoidParameters = OS_Manager.my_window.getOrganoidParam()
    imageParameters = OS_Manager.my_window.getImageParameters()
    preprocessingList = OS_Manager.my_window.getPreprocessingList()
    dictPreprocessing = OS_Manager.getDictPreprocFromListPreproc(preprocessingList)
    dictExport = OS_Manager.my_window.getExportParam()
    return  (nucleiParameters, cellsParameters, organoidParameters, imageParameters,dictPreprocessing, dictExport)

def add_feature_gate_from_selection():
    popup = glob.features_app.AddFilterOptions(glob.CONTEXT.data_manager.descriptors)
    popup.setWindowTitle("Feature Gate")
    for el in glob.CONTEXT.main_windows.get_selected_descriptors():
        popup.addFilter()
        item = popup.filter_widgets[-1]
        childeren = item.children()
        childeren[1].setCurrentIndex(childeren[1].findText(el))
        childeren[2].setCurrentIndex(childeren[2].findText("!="))
        childeren[3].setText("0")
    popup.setModal(True)
    if not popup.exec():
        return
    filter_querry = popup.results()
    if len(filter_querry)< 1:
        return
    glob.CONTEXT.data_manager.drop_data_with_querry(" & ".join(filter_querry))
    glob.CONTEXT.app_manager.update_group_list()

def unSelectAllLabel():
    if OS_Manager.currentMask is None : return
    for lab in list(OS_Manager.labelSelection):
        unSelectLabel(lab)
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)

def isValidStardisModel(model_path):
    if str(model_path) == "CellposeSAM":
        return True
    return  Path(model_path).exists() and  \
         (Path(model_path)/"config.json").exists() and \
         ( (Path(model_path)/"weights_best.h5").exists() or (Path(model_path)/"weights_last.h5").exists() )

def loadModel(*args,model_path = None, model_name = None, model_resolution = None):
    if model_path is None:
        model_path = QFileDialog.getExistingDirectory(None, "Select Stardist Model Folder")
    if not isValidStardisModel(model_path):
        QMessageBox.critical(None,"Invalid Stardist Folder", "Stardist folder must contain 'config.json' and 'weights_(best/last).h5' files")
        return

    if model_name or model_resolution is None:
        model_name, model_resolution, accepted = LoadModelInputDialog.get_inputs()
        if not accepted or model_name == "": return

    i=2
    existing_names = [OS_Manager.my_window.DefaultModelComboBox.itemText(i) for i in range(OS_Manager.my_window.DefaultModelComboBox.count())]
    while model_name in existing_names:
        model_name = model_name+"_2" if i==2 else model_name.replace("_%d"%(i-1),"_%d"%(i))
        i+=1
    info_dict["models"][model_name] = model_resolution

    OS_Manager.my_window.DefaultModelComboBox.addItem(model_name, userData=model_path)
    OS_Manager.my_window.DefaultModelComboBox.setCurrentIndex(OS_Manager.my_window.DefaultModelComboBox.count()-1)

def adjustSize2ModelAuto():
    OS_Manager.my_window.ResampleXLineEdit.setEnabled(True)
    OS_Manager.my_window.ResampleYLineEdit.setEnabled(True)
    OS_Manager.my_window.ResampleZLineEdit.setEnabled(True)
    if not OS_Manager.my_window.autoResizeButton.isChecked():return
    im_rez = OS_Manager.my_window.getImageParameters()
    for el in im_rez.values():
        if el  == "": return

    model_name = OS_Manager.my_window.getNucleiParam()["defaultModel"]
    if model_name == "CellposeSAM":
        OS_Manager.my_window.ResampleZLineEdit.setText("1.0000")
        OS_Manager.my_window.ResampleYLineEdit.setText("1.0000")
        OS_Manager.my_window.ResampleXLineEdit.setText("1.0000")
        OS_Manager.my_window.ResampleXLineEdit.setEnabled(False)
        OS_Manager.my_window.ResampleYLineEdit.setEnabled(False)
        OS_Manager.my_window.ResampleZLineEdit.setEnabled(False)
        return

    model_rez = info_dict["models"][model_name] if model_name in info_dict["models"] else {"dz":1.0,"dy":1.0,"dx":1.0}
    rz,ry,rx = (float(im_rez["dz"])/model_rez["dz"], float(im_rez["dy"])/model_rez["dy"], float(im_rez["dx"])/model_rez["dx"])
    OS_Manager.my_window.ResampleZLineEdit.setText("%.4f"%rz)
    OS_Manager.my_window.ResampleYLineEdit.setText("%.4f"%ry)
    OS_Manager.my_window.ResampleXLineEdit.setText("%.4f"%rx)
    OS_Manager.my_window.ResampleXLineEdit.setEnabled(False)
    OS_Manager.my_window.ResampleYLineEdit.setEnabled(False)
    OS_Manager.my_window.ResampleZLineEdit.setEnabled(False)


def show_pannel_selection(*args):
    im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name

    object_name = OS_Manager.maskNameToDt[ OS_Manager.my_window.MaskVisualisationComboBox.currentText()]
    OS_Manager.currentImageDf = getImageDataframe(object_name, im_name)
    if OS_Manager.currentImageDf.empty:return
    ag = [el.value for el in [OPW.group_select,OPW.aggregate_select] if el.value !="None"] if OPW.aggregate_select.value !="None" else []
    selected_indices = OPW.index_from_selection(inside=False,ag=ag)
    element_indexer = "cell_Id" if object_name != 'organo' else "corresponding_organoid"
    selected = OPW.dataset.data.loc[selected_indices,["file",element_indexer]].set_index("file")
    if im_name not in selected.index:return


    selected = np.unique(selected.loc[im_name,element_indexer].values.astype(float).astype(int))
    selected = OS_Manager.currentImageDf.index.intersection(selected)
    if len(selected)==0:return
    for lab in list(OS_Manager.labelSelection):
        unSelectLabel(lab)
    for lab in selected:
        if lab==0 or lab in OS_Manager.labelSelection :continue
        addLabelToSelection(lab)
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)
    return True

def filterOPWSelection(event):
    mask_name = OS_Manager.my_window.MaskVisualisationComboBox.currentText()
    im_name = OS_Manager.fileInfos[OS_Manager.my_window.FileListWidget.currentRow()].name
    old_df = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)


    selected_indices = OPW.filter_selection(event)
    if len(selected_indices)==0:return
    object_name = OS_Manager.maskNameToDt[ OS_Manager.my_window.MaskVisualisationComboBox.currentText()]
    element_indexer = "cell_Id" if object_name != 'organo' else "corresponding_organoid"
    selected = OPW.dataset.data.loc[selected_indices,["file",element_indexer]].set_index("file")
    for file in selected.index.unique():
        indexers = selected.loc[file,:].values.flatten().astype(float).astype(int)
        querry = """`file` != "%s" | `%s` in [%s]"""%(file , element_indexer,  ', '.join(map(str, indexers)))
        glob.CONTEXT.data_manager.drop_data_with_querry(querry)

    if OS_Manager.currentMask is None: return

    new_df = getImageDataframe(OS_Manager.maskNameToDt[mask_name],im_name)
    OS_Manager.currentImageDf = old_df
    for lab in old_df.index:
        if lab not in new_df.index:
            hideLabel(lab)
    OS_Manager.currentImageDf = new_df
    for lab in new_df.index:
        if lab not in old_df.index:
            unhideLabel(lab)
    OS_Manager.my_window.showImage(OS_Manager.selectedImage, layer = OS_Manager.currentLayer)

def updateFusionDf(df):
    old_df = glob.CONTEXT.data_manager.data.reset_index()
    to_add = [el for el in df.columns if el not in old_df.columns]
    for el in to_add:
        glob.CONTEXT.data_manager.add_column(df[el])

def save_fusion_dataframe(*args, **kwargs):
    if OS_Manager.dictPredicted["folder"]:
        fusion_path = next(Path(OS_Manager.dictPredicted["result_folder"]).glob("fusion-statistics.csv"))
    else:
        fusion_path = next(Path(OS_Manager.dictPredicted["result_folder"]).glob("*fusion-statistics.csv"))
    glob.CONTEXT.data_manager.data.to_csv(str(fusion_path), index=False)


#endregion


# if __name__ == "__main__":
update_OS_UI()
update_NX_UI()
update_OPW_UI()
connect_apps()
start()
OPW.window.server_thread.stop()