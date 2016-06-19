#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import time

# TODO:
# save sort state

if __name__ == "__main__" and __package__ is None:
    # https://github.com/arruda/relative_import_example
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.insert(1, parent_dir)

    mod = __import__('DawnlightSearch')
    sys.modules["DawnlightSearch"] = mod
    __package__ = 'DawnlightSearch'

from ._Global_logger import *

from .UI_delegate.listview_delegate import *
from .DB_Builder.update_db_module import Update_DB_Thread
from .QueryWorker.query_thread import DistributeQueryWorker

from .Ui_change_advanced_setting_dialog import EditSettingDialog
from .Ui_change_excluded_folder_dialog import EditFolderDialog
from .DB_Builder.sys_blk_devices import SystemDevices

from .QueryWorker.sql_formatter import format_sql_cmd
# ini db path
try:
    _tmp_settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
    _tmp_settings.setValue("History/last_run", time.time())
    del _tmp_settings
except:
    pass

MainWindow_base_class, _ = uic.loadUiType("Ui_mainwindow.ui")


# from .ui.mainwindows_base import MainWindow_base_class

class AppDawnlightSearch(QMainWindow, MainWindow_base_class):
    send_query_to_worker_SIGNAL = QtCore.pyqtSignal(list)
    update_db_SIGNAL = QtCore.pyqtSignal(list)
    save_uuid_flag_SIGNAL = QtCore.pyqtSignal(list)
    get_uuid_SIGNAL = QtCore.pyqtSignal()
    merge_db_SIGNAL = QtCore.pyqtSignal()

    def __init__(self):
        # super(MyApp, self).__init__()
        super(self.__class__, self).__init__()
        self.setupUi(self)

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        # http://stackoverflow.com/questions/8923562/getting-data-from-selected-item-in-qlistview
        # self.model = QtSql.QSqlTableModel(self)
        # self.model.setTable("tableView")
        # self.model.setEditStrategy(2)
        # self.model.select()

        # self.dockWidget_sqlcmd = QtWidgets.QDockWidget(MainWindow)
        # self.dockWidget_sqlcmd.close()
        # self.dockWidget_sqlcmd.setHidden()

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 10000)
        self.progressBar.setValue(400)

        self.statusBar.addPermanentWidget(self.progressBar)
        self.progressBar.show()
        self.progressBar.setVisible(False)

        self.pushButton.clicked.connect(self.on_push_button_clicked)
        self.pushButton_2.clicked.connect(self.refresh_table_uuid_mount_state_slot)

        # self.pushButton_updatedb.clicked.connect(self.on_push_button_updatedb_clicked)
        # self.pushButton_stopupdatedb.clicked.connect(self.on_push_button_stopupdatedb_clicked)
        self.actionUpdatedb.triggered.connect(self.on_push_button_updatedb_clicked)
        self.actionStop_Updating.triggered.connect(self.on_push_button_stopupdatedb_clicked)

        self._Former_search_text = ""

        self.lazy_query_timer = QtCore.QTimer(self)
        self.lazy_query_timer.setSingleShot(True)
        self.lazy_query_timer.timeout.connect(self.update_query_result)
        self.lazy_query_timer.setInterval(settings.value("Start_Querying_after_Typing_Finished", type=int, defaultValue=50))

        self.hide_tooltip_timer = QtCore.QTimer(self)
        self.hide_tooltip_timer.setSingleShot(True)
        self.hide_tooltip_timer.timeout.connect(self._hide_tooltip_slot)
        self.hide_tooltip_timer.setInterval(2000)

        self.restore_statusbar_timer = QtCore.QTimer(self)
        self.restore_statusbar_timer.setSingleShot(True)
        self.restore_statusbar_timer.timeout.connect(self._restore_statusbar_style)
        self.restore_statusbar_timer.setInterval(2000)

        # self.refresh_mount_state_timer = QtCore.QTimer(self)
        # self.refresh_mount_state_timer.setSingleShot(False)
        # self.refresh_mount_state_timer.timeout.connect(self.refresh_table_uuid_mount_state_slot)
        # self.mount_state_timestamp = 0

        # self.Query_Text_ID_list = [1]  # hack: make the ID accessible from other threads
        self.Query_Model_ID = 0

        self.elapsedtimer = QtCore.QElapsedTimer()

        desktop = QtWidgets.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        screen_w = screen_size.x() + screen_size.width()
        screen_h = screen_size.y() + screen_size.height()


        x = settings.value("Main_Window/x", type=int, defaultValue=screen_w / 4)
        y = settings.value("Main_Window/y", type=int, defaultValue=screen_h / 4)
        w = settings.value("Main_Window/width", type=int, defaultValue=-1)
        h = settings.value("Main_Window/height", type=int, defaultValue=-1)

        GlobalVar.MOUNT_STATE_UPDATE_INTERVAL = settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000)
        GlobalVar.ROWID_UPDATE_INTERVAL = settings.value('Rowid_Update_Interval', type=int, defaultValue=3000)
        GlobalVar.DB_UPDATE_INTERVAL = settings.value('Database_Update_Interval', type=int, defaultValue=1000)

        if w > 0:
            self.resize(w, h)
        self.move(x, y)

        self.__init_connect_menu_action()
        # MainCon.cur.execute("select (?),(?),md5(?), md5(?) ", ("Filename","Path","Filename","Path"))
        # print MainCon.cur.fetchone()

        # self.Submit.clicked.connect(self.dbinput)
        # treeview style:  https://joekuan.wordpress.com/2015/10/02/styling-qt-qtreeview-with-css/

        self.lineEdit_search = self.comboBox_search.lineEdit()
        self.comboBox_search.lineEdit().textChanged.connect(self.on_lineedit_text_changed)
        self.comboBox_search.lineEdit().setClearButtonEnabled(True)
        # self.comboBox_search.lineEdit().installEventFilter(self)
        self.query_ok_icon = QtGui.QIcon()
        self.query_error_icon = QtGui.QIcon()
        self.query_error_icon.addPixmap(QtGui.QPixmap("./ui/icon/hint.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.query_error_icon.addPixmap(QtGui.QPixmap("./ui/icon/hint.png"), QtGui.QIcon.Disabled, QtGui.QIcon.Off)

        self.comboBox_search.installEventFilter(self)
        self.comboBox_search.lineEdit().returnPressed.connect(self.on_lineedit_enter_pressed)
        # search setting
        self.actionCase_Sensitive.toggled.connect(self.on_toolbutton_casesensitive_toggled)
        self.toolButton_casesensitive.setChecked(settings.value('Search/Case_Sensitive', type=bool, defaultValue=False))
        default_rb = [self.radioButton_1, self.radioButton_2, self.radioButton_3, self.radioButton_4,
         self.radioButton_5][settings.value('Search/Match_Mode', type=int, defaultValue=1) - 1]

        self.toolButton_avd_setting.setChecked(
            settings.value("Main_Window/Show_Search_Setting_Panel", type=bool, defaultValue=False))
        self.frame_adv_setting.setVisible(
            settings.value("Main_Window/Show_Search_Setting_Panel", type=bool, defaultValue=False))

        GlobalVar.DATETIME_FORMAT = settings.value('Search/Date_Format',type=str,defaultValue="d/M/yyyy h:m:s")
        # self.radioButton_1 = QtWidgets.QRadioButton(self.groupBox_matchoption)
        # self.radioButton_1.setChecked()
        for radioButton in [self.radioButton_1, self.radioButton_2, self.radioButton_3, self.radioButton_4,
                            self.radioButton_5]:
            radioButton.toggled.connect(self.on_match_option_changed)
        default_rb.setChecked(True)

        # skip diff dev
        GlobalVar.SKIP_DIFF_DEV = settings.value('Database/Skip_Different_Device', type=bool, defaultValue=True)

        # size unit
        GlobalVar.SIZE_UNIT = settings.value('Size_Unit', type=str, defaultValue='KB')

        # instant search
        GlobalVar.INSTANT_SEARCH = settings.value('Search/Instant_Search', type=bool, defaultValue=True)

        # load excluded UUID
        try:
            GlobalVar.EXCLUDED_UUID = set(settings.value('Excluded_UUID',type=str, defaultValue=[]))
            self.actionShow_All.setChecked(settings.value('Excluded_UUID_Visible', type=bool, defaultValue=True))
        except Exception as e:
            logger.error('Fail to load excluded: '+ str(e))

    def eventFilter(self, source, event):
        # auto save search text when focus lost
        if source is self.comboBox_search.lineEdit() or \
                        source is self.comboBox_search:
            # http://doc.qt.io/qt-5/qevent.html
            if (event.type() == QtCore.QEvent.FocusOut):
                print("focus out")
                self.comboBox_search.lineEdit().returnPressed.emit()
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def __init_connect_menu_action(self):

        self.actionChange_excluded_folders.setStatusTip('Exclude folders from indexing.')
        self.actionChange_excluded_folders.setToolTip("folder1")
        self.actionChange_excluded_folders.triggered.connect(self._show_dialog_change_excluded_folders)
        self.actionChange_excluded_folders.hovered.connect(self._show_tooltips_change_excluded_folders)

        self.actionEnable_C_MFT_parser.toggled.connect(self._toggle_C_MFT_parser)
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        GlobalVar.USE_MFT_PARSER_CPP = settings.value('Use_CPP_MFT_parser', type=bool, defaultValue=True)
        self.actionEnable_C_MFT_parser.setChecked(GlobalVar.USE_MFT_PARSER_CPP)

        self.actionUse_MFT_parser.triggered.connect(self._toggle_use_MFT_parser)
        GlobalVar.USE_MFT_PARSER = settings.value('Use_MFT_parser', type=bool, defaultValue=True)
        self.actionUse_MFT_parser.setChecked(GlobalVar.USE_MFT_PARSER)
        self.actionEnable_C_MFT_parser.setEnabled(GlobalVar.USE_MFT_PARSER)

        self.actionAbout.triggered.connect(self._show_dialog_about)
        self.actionAbout_Qt.triggered.connect(self._show_dialog_about_qt)
        self.actionOpen_Project_Homepage.triggered.connect(self._about_open_homepage)
        self.actionLatest_Version.triggered.connect(self._about_open_latest_version)

        self.actionAdvanced_settings.triggered.connect(self._show_dialog_advanced_setting)

        self.actionOpen_setting_path.triggered.connect(self._open_setting_path)
        self.actionOpen_db_path.triggered.connect(self._open_db_path)
        self.actionOpen_temp_db_path.triggered.connect(self._open_temp_db_path)

    def ini_after_show(self):
        logger.info('ini table.')
        self.statusBar.showMessage("Loading...")
        self.ini_table()
        logger.info('ini subthread.')
        self.ini_subthread()
        logger.info('ini done.')

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        if (settings.value("Main_Window/DOCK_LOCATIONS")):
            try:
                self.restoreState(settings.value("Main_Window/DOCK_LOCATIONS"))
            except Exception as e:
                logger.error('Failt to restore dock states.')
        else:
            self.dockWidget_sqlcmd.close()


    def ini_subthread(self):
        # Calling heavy-work function through fun() and signal-slot, will block gui event loop.
        # Only thread.run solve.
        logger.info('ini_subthread 1')
        update_db_Thread = Update_DB_Thread(parent=self)
        logger.info('ini_subthread 2')
        self.update_db_SIGNAL.connect(update_db_Thread.update_db_slot, QtCore.Qt.QueuedConnection)
        self.save_uuid_flag_SIGNAL.connect(update_db_Thread.save_uuid_flag_slot, QtCore.Qt.QueuedConnection)
        self.get_uuid_SIGNAL.connect(update_db_Thread.get_table_uuid_slot, QtCore.Qt.QueuedConnection)
        self.merge_db_SIGNAL.connect(update_db_Thread.merge_db_slot, QtCore.Qt.QueuedConnection)

        update_db_Thread.start()
        self.update_db_Thread = update_db_Thread

        self.distribute_query_thread = DistributeQueryWorker(self,
                                       target_slot=self.on_model_receive_new_row,
                                       progress_slot=self.on_update_progress_bar)
        self.send_query_to_worker_SIGNAL.connect(self.distribute_query_thread.distribute_new_query)

        self.distribute_query_thread.start()


    def ini_table(self):
        self.build_table_model()
        # self.build_table_model_uuid()

        # self.build_table_widget_uuid()
        self.header_list_uuid = UUID_HEADER_LIST
        self.header_name_uuid = UUID_HEADER_LABEL
        self.tableWidget_uuid.setColumnCount(len(UUID_HEADER_LABEL))
        self.tableWidget_uuid.setHorizontalHeaderLabels(UUID_HEADER_LABEL)

        # self.tableView.setModel(self.model)

        HTMLDelegate = HTMLDelegate_VC_HL
        self.tableView.setItemDelegate( HTMLDelegate())
        # self.tableView.setItemDelegateForColumn(0, HTMLDelegate_VC_HL_display_only()) # crash when using multi delegates.

        # self.tableView.setModel(self.proxy)
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setSectionsMovable(True)
        self.tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.on_tableview_context_menu_requested)
        self.tableView.doubleClicked.connect(self.on_tableview_double_clicked)
        self.tableView.verticalHeader().hide()

        # self.tableview_menu = QtWidgets.QMenu(self)
        # self.tableView.horizontalHeader().restoreGeometry()
        self.tableView.setSortingEnabled(1)

        # self.tableView_uuid.setModel(self.model_uuid)
        # self.tableView_uuid.horizontalHeader().setSectionsMovable(True)
        # self.tableView_uuid.resizeColumnsToContents()
        self.tableWidget_uuid.horizontalHeader().setSectionsMovable(True)
        # self.tableWidget_uuid.resizeColumnsToContents()

        self.tableWidget_uuid.horizontalHeader().setSectionsMovable(True)

        # Build tablewidget uuid menu
        self.tableWidget_uuid.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tableWidget_uuid.customContextMenuRequested.connect(self.on_tableWidget_uuid_context_menu_requested)
        self.tableWidget_uuid_menu = QtWidgets.QMenu(self)
        self.tableWidget_uuid_menu.addAction(self.actionShow_All)
        self.tableWidget_uuid_menu.addSeparator()
        self.tableWidget_uuid_menu.addAction(self.actionShow_UUID)
        self.tableWidget_uuid_menu.addAction(self.actionHide_UUID)
        self.tableWidget_uuid_menu.addSeparator()
        self.tableWidget_uuid_menu.addAction(self.actionUpdatedb_onlyselected)
        self.tableWidget_uuid_menu.addSeparator()
        self.tableWidget_uuid_menu.addAction(self.actionUpdatedb)
        self.tableWidget_uuid_menu.addAction(self.actionStop_Updating)

        self.tableWidget_uuid_menu.addSeparator()
        self.tableWidget_uuid_menu.addAction(self.actionCheck_Included)
        self.tableWidget_uuid_menu.addAction(self.actionUncheck_Included)
        self.tableWidget_uuid_menu.addSeparator()
        self.tableWidget_uuid_menu.addAction(self.actionCheck_Updatable)
        self.tableWidget_uuid_menu.addAction(self.actionUncheck_Updatable)

        self.actionShow_All.triggered.connect(self.action_uuid_show_all)
        self.actionShow_UUID.triggered.connect(self.action_uuid_show_uuid)
        self.actionHide_UUID.triggered.connect(self.action_uuid_hide_uuid)

        self.actionCheck_Included.triggered.connect(self.action_uuid_check_included)
        self.actionUncheck_Included.triggered.connect(self.action_uuid_uncheck_included)
        self.actionCheck_Updatable.triggered.connect(self.action_uuid_check_updatable)
        self.actionUncheck_Updatable.triggered.connect(self.action_uuid_uncheck_updatable)


        self.actionUpdatedb_onlyselected.triggered.connect(self.on_push_button_updatedb_only_selected_clicked)
        # Recovery column width
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        width_list_result = settings.value("Column_width_of_reslut_list", type=int, defaultValue=[])
        width_list_uuid = settings.value("Column_width_of_uuid_list", type=int, defaultValue=[])
        try:
            for i, width in enumerate(width_list_result):
                self.tableView.setColumnWidth(i, width)
            for i, width in enumerate(width_list_uuid):
                self.tableWidget_uuid.setColumnWidth(i, width)
        except Exception as e:
            logger.error(str(e))

    def on_tableWidget_uuid_context_menu_requested(self):
        point = QtGui.QCursor.pos()
        self.tableWidget_uuid_menu.exec_(point)


    @pyqtSlot(bool)
    def action_uuid_show_all(self,checked):
        for row in range(self.tableWidget_uuid.rowCount()):
            if checked:
                self.tableWidget_uuid.setRowHidden(row, False)
            else:
                uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).text()
                if uuid in GlobalVar.EXCLUDED_UUID:
                    self.tableWidget_uuid.setRowHidden(row, True)

    @pyqtSlot()
    def action_uuid_show_uuid(self):

        for item in self.tableWidget_uuid.selectedItems():
            item.setForeground(QtCore.Qt.black)
            temp_font = item.font()
            temp_font.setItalic(False)
            item.setFont(temp_font)
            if item.column() == 3:
                uuid = item.text()
                if uuid in GlobalVar.EXCLUDED_UUID:
                    GlobalVar.EXCLUDED_UUID.remove(uuid)

        # for i in self.tableWidget_uuid.selectedRanges():
        #     row = i.topRow()

    @pyqtSlot()
    def action_uuid_hide_uuid(self):
        for item in self.tableWidget_uuid.selectedItems():
            item.setForeground(QtCore.Qt.gray)
            temp_font = item.font()
            temp_font.setItalic(True)
            item.setFont(temp_font)

            if item.column() == 3:
                uuid = item.text()
                GlobalVar.EXCLUDED_UUID.add(uuid)
                if not (self.actionShow_All.isChecked()):
                    self.tableWidget_uuid.setRowHidden(item.row(), True)

    @pyqtSlot()
    def action_uuid_check_included(self):
        for i in self.tableWidget_uuid.selectedRanges():
            for row in range(i.topRow(), i.bottomRow() + 1):
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setCheckState(QtCore.Qt.Checked)

    @pyqtSlot()
    def action_uuid_uncheck_included(self):
        for i in self.tableWidget_uuid.selectedRanges():
            for row in range(i.topRow(), i.bottomRow() + 1):
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setCheckState(QtCore.Qt.Unchecked)

    @pyqtSlot()
    def action_uuid_check_updatable(self):
        for i in self.tableWidget_uuid.selectedRanges():
            for row in range(i.topRow(), i.bottomRow() + 1):
                self.tableWidget_uuid.item(row, UUID_HEADER.updatable).setCheckState(QtCore.Qt.Checked)

    @pyqtSlot()
    def action_uuid_uncheck_updatable(self):
        for i in self.tableWidget_uuid.selectedRanges():
            for row in range(i.topRow(), i.bottomRow() + 1):
                self.tableWidget_uuid.item(row, UUID_HEADER.updatable).setCheckState(QtCore.Qt.Unchecked)


    def _show_dialog_about(self):
        print("About dialog...")
        msg = QtWidgets.QMessageBox()
        # msg.setIcon()
        msg.about(self, "About Dawnlight Search", COPYRIGHT)

    def _open_setting_path(self):
        self._open_file_or_folder(os.path.dirname(
            QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME).fileName()
        ))

    def _open_db_path(self):
        self._open_file_or_folder(os.path.dirname(DATABASE_FILE_NAME))

    def _open_temp_db_path(self):
        self._open_file_or_folder(os.path.dirname(TEMP_DB_NAME))

    def _show_dialog_about_qt(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.aboutQt(self, 'cccc')

    def _about_open_homepage(self):
        QDesktopServices.openUrl(QUrl("https://github.com/chg-hou/DawnlightSearch"))

    def _about_open_latest_version(self):
        QDesktopServices.openUrl(QUrl("https://github.com/chg-hou/DawnlightSearch/wiki/Latest-Version"))


    @pyqtSlot()
    def _hide_tooltip_slot(self):
        QtWidgets.QToolTip.hideText()

    def _show_tooltips_change_excluded_folders(self, *avg):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str)

        # str1 = str(time.time())
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "\n".join(excluded_folders))
        # self.hide_tooltip_timer.setInterval(2000)
        self.hide_tooltip_timer.start()
        # print avg

    def _show_dialog_change_excluded_folders(self):

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        excluded_folders = settings.value('Excluded_folders', type=str)

        folder_list, ok = EditFolderDialog.getFolders(excluded_folders, parent=self)

        logger.info("Excluded folders updated.")
        logger.info("{}  {}".format(folder_list, ok))
        if ok:
            folder_list = list(set(folder_list))
            folder_list.sort()
            logger.info("Setting file path:" + settings.fileName())
            settings.setValue('Excluded_folders', folder_list)
            settings.sync()

    def _show_dialog_advanced_setting(self):

        new_settings, ok = EditSettingDialog.getSetting(ORGANIZATION_NAME, ALLICATION_NAME,
                                                        DATABASE_FILE_NAME, TEMP_DB_NAME, GlobalVar.DATETIME_FORMAT,
                                                        parent=self)
        if ok:
            settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
            GlobalVar.QUERY_CHUNK_SIZE = settings.value('Query_Chunk_Size', type=int, defaultValue=10000)
            GlobalVar.MODEL_MAX_ITEMS = settings.value('Max_Items_in_List', type=int, defaultValue=3000)
            GlobalVar.QUERY_LIMIT = settings.value('Query_limit', type=int, defaultValue=100)
            # self.refresh_mount_state_timer.setInterval(
            #     settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000))

            self.lazy_query_timer.setInterval(
                settings.value("Start_Querying_after_Typing_Finished", type=int, defaultValue=50))

            GlobalVar.DATETIME_FORMAT = settings.value('Search/Date_Format', type=str, defaultValue="d/M/yyyy h:m:s")
            GlobalVar.SKIP_DIFF_DEV = settings.value('Database/Skip_Different_Device', type=bool, defaultValue=True)
            GlobalVar.SIZE_UNIT = settings.value('Size_Unit', type=str, defaultValue='KB')
            GlobalVar.INSTANT_SEARCH = settings.value('Search/Instant_Search', type=bool, defaultValue=True)

            GlobalVar.MOUNT_STATE_UPDATE_INTERVAL = settings.value('Mount_State_Update_Interval', type=int, defaultValue=3000)
            GlobalVar.ROWID_UPDATE_INTERVAL = settings.value('Rowid_Update_Interval', type=int, defaultValue=3000)
            GlobalVar.DB_UPDATE_INTERVAL = settings.value('Database_Update_Interval', type=int, defaultValue=1000)

            logger.info(
                "Advanced Setting updated. " + str(GlobalVar.QUERY_CHUNK_SIZE) + " " + str(GlobalVar.MODEL_MAX_ITEMS))
            logger.info("{}  {}".format(new_settings, ok))

    def _toggle_use_MFT_parser(self, enable_MFT_parser):
        logger.info("toggle_use_MFT_parser: " + str(enable_MFT_parser))
        GlobalVar.USE_MFT_PARSER = enable_MFT_parser
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_MFT_parser', enable_MFT_parser)
        self.actionEnable_C_MFT_parser.setEnabled(enable_MFT_parser)
        settings.sync()

    def _toggle_C_MFT_parser(self, enable_C_MFT_parser):
        logger.info("toggle_C_MFT_parser: " + str(enable_C_MFT_parser))
        GlobalVar.USE_MFT_PARSER_CPP = enable_C_MFT_parser
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue('Use_CPP_MFT_parser', enable_C_MFT_parser)
        settings.sync()

    def print_clipboard(self):
        print('\n\nclipboard:\n\n')
        cb = QtWidgets.QApplication.clipboard()
        print(cb.text(mode=cb.Clipboard))
        md = cb.mimeData(mode=cb.Clipboard)
        print(cb.mimeData(mode=cb.Clipboard))
        print(md.text())
        print(md.html())
        print(md.urls())
        print(md.imageData())
        print(md.colorData())

        if md.urls():
            a = md.urls()[0]
            fun_names = "adjusted authority errorString fileName fragment host password path query resolved scheme toDisplayString toLocalFile url 	userInfo"
            for i in fun_names.split(" "):
                try:
                    print(i, ":\t\t", getattr(a, i)())
                except:
                    pass

    @pyqtSlot()
    def on_push_button_clicked(self):

        logger.info('on_push_button_clicked')
        # a = self.saveGeometry()
        self.statusBar.setStyleSheet(
            "QStatusBar{color:red;font-weight:bold;}")

        self.statusBar.showMessage("fgsfdgaf", 3000)
        self.restore_statusbar_timer.setInterval(4000)
        self.restore_statusbar_timer.start()
        for row in range(self.tableWidget_uuid.rowCount()):
            progressbar = self.tableWidget_uuid.cellWidget(row, UUID_HEADER.processbar)
            if not progressbar:
                print("empty progress bar")
            else:
                progressbar.hide()
        str1 = str(time.time())
        QtGui.QCursor.pos()

        QtWidgets.QToolTip.showText(QtCore.QPoint(100, 200), str1)

    # @pyqtSlot()
    # def on_push_button_clicked_old(self):
    #     # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
    #     #                'major_dnum', 'minor_dnum', 'rows', 'updatable']
    #     # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
    #     #          '', '', 'rows', 'updatable', 'progress']
    #     self.aa = QtWidgets.QProgressBar()
    #     # self.itemc = QtGui.QStandardItem(self.aa)
    #     self.model_uuid.setItem(0, 9, QtWidgets.QProgressBar())
    #
    #     pass
    #     return
    #     row = []
    #     for idx, col in enumerate(['NAME', 2, 3, 4, 5, 6, 7]):
    #         newitem = QtGui.QStandardItem()
    #         if idx in [0]:
    #             newitem.setData(QtCore.QVariant("aaaa"), QtCore.Qt.DisplayRole)
    #             newitem.setData(QtCore.QVariant("dddd"), HACKED_QT_EDITROLE)
    #
    #         if idx in [2]:
    #             newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
    #         if idx in [4, 5, 6]:
    #             newitem.setData(QtCore.QVariant(col), HACKED_QT_EDITROLE)
    #         row.append(newitem)
    #     self.model.appendRow(row)
    #
    #     return
    #     self.print_clipboard()
    #
    #     cb = QtWidgets.QApplication.clipboard()
    #
    #     qurl = QtCore.QUrl().fromLocalFile("/home/cc/Desktop/TeamViewer.desktop")
    #
    #     md = QtCore.QMimeData()
    #     md.setUrls([qurl])
    #     md.setText("/home/cc/Desktop/TeamViewer.desktop")
    #     cb.setMimeData(md, mode=cb.Clipboard)
    #
    #     self.print_clipboard()
    #     # print self.get_search_included_uuid()
    #
    #
    #     # self.qsql_model = QtSql.QSqlQueryModel()
    #     # header_list = self.header_list
    #     # self.qsql_model.setQuery(
    #     #     "select  " + ",".join(header_list) + ' from `c08e276b-45d6-4669-bef3-77260a891c31` WHERE Filename LIKE "%zip"  ')
    #     # self.tableView.setModel(self.qsql_model)
    #     # self.proxy.setSourceModel(self.qsql_model)
    #
    #     # self.model_uuid.clear()
    #     # print self.table_header.sortIndicatorSection()
    #     # print self.table_header.sortIndicatorOrder()
    #     # self.tableView.setSortingEnabled(1)

    @pyqtSlot()
    def on_push_button_updatedb_clicked(self):
        update_path_list = []
        for row in range(self.tableWidget_uuid.rowCount()):
            uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).data(QtCore.Qt.DisplayRole)
            path = self.tableWidget_uuid.item(row, UUID_HEADER.path).data(QtCore.Qt.DisplayRole)
            included = self.tableWidget_uuid.item(row, UUID_HEADER.included).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            updatable = self.tableWidget_uuid.item(row, UUID_HEADER.updatable).data(QtCore.Qt.CheckStateRole) \
                        == QtCore.Qt.Checked
            if not updatable:
                continue
            update_path_list.append({'path': path, 'uuid': uuid})

        # for row in range(self.model_uuid.rowCount()):
        #     uuid = self.model_uuid.index(row, 3).data()
        #     path = self.model_uuid.index(row, 1).data()
        #     included = self.model_uuid.index(row, 0).data(QtCore.Qt.CheckStateRole) \
        #                == QtCore.Qt.Checked
        #     updatable = self.model_uuid.index(row, 9).data(QtCore.Qt.CheckStateRole) \
        #                 == QtCore.Qt.Checked
        #     if not updatable:
        #         continue
        #     update_path_list.append({'path': path, 'uuid': uuid})
        print("Updatedb clicked.", update_path_list)
        print("main Thread:", int(QtCore.QThread.currentThreadId()))
        self.update_db_SIGNAL.emit(update_path_list)

    @pyqtSlot()
    def on_push_button_updatedb_only_selected_clicked(self):
        update_path_list = []
        for i in self.tableWidget_uuid.selectedRanges():
            for row in range(i.topRow(), i.bottomRow() + 1):
                uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).data(QtCore.Qt.DisplayRole)
                path = self.tableWidget_uuid.item(row, UUID_HEADER.path).data(QtCore.Qt.DisplayRole)
                update_path_list.append({'path': path, 'uuid': uuid})
        print("Updatedb clicked.", update_path_list)
        print("main Thread:", int(QtCore.QThread.currentThreadId()))
        self.update_db_SIGNAL.emit(update_path_list)

    @pyqtSlot()
    def on_push_button_stopupdatedb_clicked(self):
        update_path_list = []
        print("Stop Updatedb clicked.", update_path_list)
        print("main Thread:", int(QtCore.QThread.currentThreadId()))
        self.update_db_SIGNAL.emit(update_path_list)

    @pyqtSlot(int)
    def on_table_header_clicked(self, logicalIndex):
        print('Header clicked: ', logicalIndex)

        # sortIndicatorOrder()
        # sortIndicatorSection()   logical index of the section that has a sort indicator

        # setSortIndicator(int  logicalIndex, Qt::SortOrder order)
        # isSortIndicatorShown(),  setSortIndicatorShown(bool  show)
        # showSection(int logicalIndex)
        # hideSection(int logicalIndex)

        # print self.table_header.sortIndicatorSection()
        # print self.table_header.sortIndicatorOrder()

    @pyqtSlot(QtGui.QStandardItem)
    def on_table_uuid_itemChanged(self, item):
        pass
        # idx = self.model_uuid.indexFromItem(item)
        # if idx.column() == 0:
        #     row = idx.row()
        #     uuid = self.model_uuid.index(row, 3).data()
        #     print "UUID item changed: ", idx.column(), idx.row(), item.checkState(), uuid
        #     MainCon.cur.execute(''' UPDATE  UUID SET included=?
        #             WHERE uuid=? ''',
        #                 (item.checkState()==QtCore.Qt.Checked,uuid))
        #     MainCon.con.commit()

    @pyqtSlot()
    def on_lineedit_enter_pressed(self):
        self._query_text_changed()

    @pyqtSlot(str)
    def on_lineedit_text_changed(self, text):
        print('Text changerd.')
        if GlobalVar.INSTANT_SEARCH:
            self._query_text_changed()

    def _query_text_changed(self):
        text = self.lineEdit_search.text().strip()
        if self._Former_search_text == text:  # or (not text)
            return
        GlobalVar.Query_Text_ID += 1

        self._Former_search_text = text

        # ============================
        OK_flag, _, sql_where , _, _, highlight_words = format_sql_cmd(
            {
                'path': 'pathname',
                'uuid': 'uuid',
                'sql_text': text,
                'rowid_low': 0,
                'rowid_high': 0,
            }
        )
        GlobalVar.HIGHLIGHT_WORDS = highlight_words
        # print sql_where
        # self.plainTextEdit_sql_where = QtWidgets.QPlainTextEdit(self.centralWidget)
        self.plainTextEdit_sql_where.setPlainText(sql_where)
        if OK_flag:
            self.toolButton_query_ok.setIcon(self.query_ok_icon)
        else:
            self.toolButton_query_ok.setIcon(self.query_error_icon)
        # return
        # ============================

        # Bug with directly calling update_query_result, if typing too fast
        # if self.lazy_query_timer.interval()>0:
        #     self.lazy_query_timer.start()
        # else:
        #     self.update_query_result()
        self.lazy_query_timer.start()

    @pyqtSlot(int, int)
    def on_update_progress_bar(self, remained, total):
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(total - remained)
        if remained == 0:
            self.progressBar.setVisible(False)

    def test_action_slot(self, x):
        print(x)

    @pyqtSlot(QtCore.QPoint)
    def on_tableview_context_menu_requested(self, point):
        menu = QtWidgets.QMenu(self)
        file_type = self._get_filetype_of_selected()
        filename_list = [x[2] for x in self.get_tableview_selected()]
        icon_filename, app_name, app_tooltip, app_launch_fun, app_launcher = get_default_app(file_type)
        if (not file_type) or (file_type == "folder") or (not app_name):
            menu.addAction("Open", self.on_tableview_context_menu_open)
        else:
            tmp = menu.addAction('''Open with "%s"''' % app_name, partial(app_launch_fun, app_launcher, filename_list))
            tmp.setIcon(get_QIcon_object(icon_filename))
            tmp.setToolTip(app_tooltip)

            open_with_menu = menu.addMenu("Open with")
            for icon_filename, app_name, app_tooltip, app_launch_fun, app_launcher in get_open_with_app(file_type):
                tmp = open_with_menu.addAction('''Open with "%s"''' % app_name,
                                               partial(app_launch_fun, app_launcher, filename_list))
                tmp.setIcon(get_QIcon_object(icon_filename))
                tmp.setToolTip(app_tooltip)
            open_with_menu.addAction('''Open With Other Application...''' ,
                                         partial(pop_select_app_dialog_and_open, file_type, filename_list))

        menu.addAction("Open path", self.on_tableview_context_menu_open_path)
        copy_menu = menu.addMenu("Copy ...")
        copy_menu.addAction("Copy fullpath", self.on_tableview_context_menu_copy_fullpath)
        copy_menu.addAction("Copy filename", self.on_tableview_context_menu_copy_filename)
        copy_menu.addAction("Copy path", self.on_tableview_context_menu_copy_path)
        menu.addSeparator()
        move_to_menu = menu.addMenu("Move to ...")
        move_to_menu.addAction("Browser ...", self.on_tableview_context_menu_move_to)
        # TODO: history
        move_to_menu.addSeparator()
        copy_to_menu = menu.addMenu("Copy to ...")
        copy_to_menu.addAction("Browser ...", self.on_tableview_context_menu_copy_to)
        copy_to_menu.addSeparator()

        # https://github.com/hsoft/send2trash
        # tmp = menu.addAction("Move to trash", self.on_tableview_context_menu_move_to_trash)
        # tmp.setIcon(get_QIcon_object('./ui/icon/user-trash.png'))
        tmp = menu.addAction("Delete", self.on_tableview_context_menu_delete)
        tmp.setIcon(get_QIcon_object('./ui/icon/trash-empty.png'))

        # Need GTk3 to use Gtk.AppChooserDialog.new_for_content_type
        # menu.addAction("Open with Other Application...",lambda  *args: pop_select_app_dialog())
        point = QtGui.QCursor.pos()
        menu.exec_(point)

    @pyqtSlot(QtCore.QModelIndex)
    # a = QtCore.QModelIndex()
    def on_tableview_double_clicked(self, index):
        logger.info("Item double clicked: " + str(index))
        row = index.row()
        if index.column() == 0:
            Filename = self.model.data(self.model.index(row, 0), HACKED_QT_EDITROLE)
            Path = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)
            import os
            fullpath = os.path.join(Path, Filename)  # TODO: convert in Windows
        elif index.column() == 1:
            fullpath = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)
        self._open_file_or_folder(fullpath)

    def _get_filetype_of_selected(self):
        file_type_set = set()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            if IsFolder:
                return "folder"
            file_type_set.add(get_file_type(Filename, IsFolder))
            if len(file_type_set) != 1:
                return "folder"
        if len(file_type_set)>0:
            return file_type_set.pop()
        else:
            return ''

    def get_tableview_selected(self):
        import os
        print(self.tableView.SelectRows)
        row_set = set()
        # TODO: get row
        # for i in self.tableWidget_uuid.selectedRanges():
        #     row = i.topRow()
        for i in self.tableView.selectedIndexes():
            row_set.add(i.row())
        for row in row_set:
            IsFolder = self.model.data(self.model.index(row, 3), HACKED_QT_EDITROLE)
            Filename = self.model.data(self.model.index(row, 0), HACKED_QT_EDITROLE)
            Path = self.model.data(self.model.index(row, 1), HACKED_QT_EDITROLE)

            fullpath = os.path.join(Path, Filename)  # TODO: convert in Windows
            logger.debug('==== Selected : ' + str([Filename, Path, fullpath, int(IsFolder) > 0]))
            yield Filename, Path, fullpath, int(IsFolder) > 0

    @pyqtSlot()
    def on_tableview_context_menu_open(self):
        # print "Open."

        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            logger.debug('Open: ' + fullpath)
            self._open_file_or_folder(fullpath)

    def _open_file_or_folder(self, path):
        import os, subprocess
        if not os.path.exists(path):
            logger.warning("File/path does not exist: " + path)
            msg = "File/path does not exist: " + path
            QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), msg)
            self.statusBar.setStyleSheet(
                "QStatusBar{color:red;font-weight:bold;}")

            self.statusBar.showMessage(msg, 3000)
            self.restore_statusbar_timer.setInterval(3000)
            self.restore_statusbar_timer.start()
            return
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            # if sys.platform.startswith('darwin'):
            #     subprocess.call(('open', path))
            # elif os.name == 'nt':
            #     os.startfile(path)
            # elif os.name == 'posix':
            #     subprocess.call(('xdg-open', path))
        except:
            logger.warning("Cannot open file: %s" % path)

    def _restore_statusbar_style(self):
        self.statusBar.setStyleSheet("QStatusBar{}")

    @pyqtSlot()
    def on_tableview_context_menu_open_path(self):
        print("Open path.")
        import os, subprocess
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            print(Path)
            if not os.path.exists(Path):    continue
            try:
                if sys.platform.startswith('darwin'):
                    subprocess.call(('open', Path))
                elif os.name == 'nt':
                    os.startfile(Path)
                elif os.name == 'posix':
                    subprocess.call(('xdg-open', Path))
            except:
                print("Cannot open path: %s" % Path)

    @pyqtSlot()
    def on_tableview_context_menu_copy_fullpath(self):
        print("copy fullpath")
        cb = QtWidgets.QApplication.clipboard()
        qurls = []
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            qurls.append(QtCore.QUrl().fromLocalFile(fullpath))
            paths.append(fullpath)
        md.setUrls(qurls)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_copy_filename(self):
        print("copy filename")
        cb = QtWidgets.QApplication.clipboard()
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            paths.append(Filename)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_copy_path(self):
        print("copy path")
        cb = QtWidgets.QApplication.clipboard()
        paths = []
        md = QtCore.QMimeData()
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            paths.append(Path)
        md.setText("\n".join(paths))
        cb.setMimeData(md, mode=cb.Clipboard)

    @pyqtSlot()
    def on_tableview_context_menu_move_to(self):
        # TODO: show process?
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (move to)"))
        print("move to", des_path)
        if not os.path.exists(des_path):    return
        self.statusBar.showMessage("Moving...")
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                shutil.move(fullpath, des_path)
            except:
                print("Fail to move file: %s" % fullpath)
        self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot()
    def on_tableview_context_menu_copy_to(self):
        import os, shutil
        des_path = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory (copy to)"))
        # print "copy to", des_path
        if not os.path.exists(des_path):    return
        self.statusBar.showMessage("Coping...")
        for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
            # if not os.path.exists(Path):    continue
            try:
                if False and IsFolder:
                    shutil.copy2(fullpath, des_path)
                    # shutil.copytree(fullpath, des_path) # TODO: test this
                else:
                    shutil.copy2(fullpath, des_path)
            except:
                logger.error("Fail to copy file: %s" % fullpath)
        self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot()
    def on_tableview_context_menu_move_to_trash(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
                                           "Are you sure to move file(s) to trash?", QtGui.QMessageBox.Yes |
                                           QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        # TODO : ?Gio.File.trash  https://developer.gnome.org/gio/stable/GFile.html#g-file-new-for-path
        if reply == QMessageBox.Yes:
            pass

    @pyqtSlot()
    def on_tableview_context_menu_delete(self):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to DELETE?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.statusBar.showMessage("Deleting...")

            import shutil
            for Filename, Path, fullpath, IsFolder in self.get_tableview_selected():
                logger.info("Delete: " + fullpath)
                # if not os.path.exists(Path):    continue
                try:
                    if IsFolder:
                        os.removedirs(fullpath)
                    else:
                        os.remove(fullpath)
                except:
                    logger.error("Fail to delete file: %s" % fullpath)
            self.statusBar.showMessage("Done.", 3000)

    @pyqtSlot(bool)
    def on_toolbutton_casesensitive_toggled(self, checked):
        logger.info('Case Sensitive toggled:' + str(checked))
        self._Former_search_text = ''
        GlobalVar.CASE_SENSTITIVE = checked
        self.on_lineedit_text_changed(self.lineEdit_search.text())

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue("Search/Case_Sensitive", GlobalVar.CASE_SENSTITIVE)

    @pyqtSlot(bool)
    def on_match_option_changed(self, checked):
        if self.radioButton_1.isChecked():
            GlobalVar.MATCH_OPTION = 1
        elif self.radioButton_2.isChecked():
            GlobalVar.MATCH_OPTION = 2
        elif self.radioButton_3.isChecked():
            GlobalVar.MATCH_OPTION = 3
        elif self.radioButton_4.isChecked():
            GlobalVar.MATCH_OPTION = 4
        elif self.radioButton_5.isChecked():
            GlobalVar.MATCH_OPTION = 5
        logger.debug('on_match_option_changed:' + str(GlobalVar.MATCH_OPTION))

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)
        settings.setValue("Search/Match_Mode", GlobalVar.MATCH_OPTION)


    @pyqtSlot(int, list)
    def on_model_receive_new_row(self, query_id, insert_row):
        # QApplication.processEvents()
        # self.parent_application.processEvents()
        if query_id < GlobalVar.Query_Text_ID:
            # old query, ignore
            return

        # self.parent_application.processEvents()
        # if self.Query_Model_ID < query_id:
        #     self.Query_Model_ID = query_id
        #     self._clear_model()
        #     # TODO: highlight former selected rows
        row = self.model.rowCount()
        GlobalVar.CURRENT_MODEL_ITEMS = row
        if row < GlobalVar.MODEL_MAX_ITEMS:
            #  method 2
            for col, item in enumerate(insert_row):
                if col > 0:
                    # Safe, even sorting is enabled.
                    row = insert_row[0].row()
                self.model.setItem(row, col, item)
            #  method 1, XXX, memory leak!
            # self.model.appendRow(insert_row)

    @pyqtSlot(int, int, str)
    def on_db_progress_update(self, num_records, mftsize, uuid_updating):
        # self.update_progress_SIGNAL.emit

        # header_list = ['included', 'path', 'label', 'uuid', 'fstype', 'name',
        #                'major_dnum', 'minor_dnum', 'rows', 'updatable']
        # h_header = ['', 'Path', 'Label', 'UUID', 'FS type', 'Dev name',
        #             '', '', 'rows', 'updatable', 'progress']
        # self.tableWidget_uuid = QtWidgets.QTableWidget()

        logger.debug("DB progress update: " + str([num_records, mftsize, uuid_updating]))
        # self.parent_application.processEvents()

        for row in range(self.tableWidget_uuid.rowCount()):
            uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).data(QtCore.Qt.DisplayRole)
            if uuid == uuid_updating:
                progressbar = self.tableWidget_uuid.cellWidget(row, UUID_HEADER.processbar)
                if not progressbar:
                    progressbar = QtWidgets.QProgressBar()
                    progressbar.setMaximum(100)
                    self.tableWidget_uuid.setCellWidget(row, UUID_HEADER.processbar, progressbar)
                    progressbar.hide()
                # progressbar = QtWidgets.QProgressBar()
                if num_records == -1:
                    progressbar.show()
                    progressbar.setVisible(True)
                    progressbar.setTextVisible(True)
                    progressbar.setMaximum(100)
                    progressbar.setMinimum(0)
                    progressbar.setValue(0)
                    progressbar.setFormat("%p%")
                elif num_records == -2:
                    # Qt bug? even show when resized.
                    # progressbar.setHidden(True)
                    # progressbar.hide()
                    # progressbar.setVisible(False)
                    progressbar.setMaximum(100)
                    progressbar.setMinimum(0)
                    progressbar.setValue(100)
                    progressbar.setFormat("Merging...")
                    QApplication.processEvents()    #
                else:
                    if mftsize < 0:
                        progressbar.setMinimum(0)
                        progressbar.setMaximum(0)
                        progressbar.setFormat(str(num_records))
                    else:
                        progressbar.setFormat("%d/%d  " % (num_records, mftsize) + "%p%")
                        progressbar.setValue(num_records * 100 / mftsize)
                break

        if num_records == -2:
            logger.debug("DB progress update: " + "merge temp db.")
            self.merge_db_SIGNAL.emit()
            progressbar.setFormat("Done")

    def _clear_model(self):
        self.model.setRowCount(0)
        GlobalVar.CURRENT_MODEL_ITEMS = 0
        # self.model.clear()    # will clear header too.

    @pyqtSlot()
    def update_query_result(self):
        sql_text = self.lineEdit_search.text().strip()

        query_id = GlobalVar.Query_Text_ID

        uuid_path_list = self.get_search_included_uuid()

        if (len(uuid_path_list) == 0) or (not sql_text):
            self.progressBar.setVisible(False)
            self._clear_model()
            return
        # debug sql formatter


        self._clear_model()
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.send_query_to_worker_SIGNAL.emit([query_id, uuid_path_list, sql_text])


    def build_table_model(self):
        self.model = QtGui.QStandardItemModel(self.tableView)
        self.model.setSortRole(HACKED_QT_EDITROLE)
        header_list = DB_HEADER_LIST
        self.header_list = header_list
        print(len(header_list))
        self.model.setColumnCount(len(header_list))
        self.model.setHorizontalHeaderLabels(DB_HEADER_LABEL)

        # self.proxy = QtCore.QSortFilterProxyModel(self)
        # self.proxy.setSourceModel(self.model)
        # self.proxy.setFilterKeyColumn(
        #     0)  # The default value is 0. If the value is -1, the keys will be read from all columns.
        # # self.proxy.setFilterWildcard("*.zip*")
        # # https://deptinfo-ensip.univ-poitiers.fr/ENS/pyside-docs/PySide/QtGui/QSortFilterProxyModel.html
        # self.proxy.setDynamicSortFilter(
        #     True)  # This property holds whether the proxy model is dynamically sorted and filtered whenever the contents of the source model change.
        # self.proxy.setFilterRole(HACKED_QT_EDITROLE)

    @pyqtSlot(str)
    def show_statusbar_warning_msg_slot(self, msg):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), msg)
        self.statusBar.setStyleSheet(
            "QStatusBar{color:red;font-weight:bold;}")

        self.statusBar.showMessage(msg, 3000)
        self.restore_statusbar_timer.setInterval(3000)
        self.restore_statusbar_timer.start()
        QApplication.processEvents()

    @pyqtSlot(list)
    def get_table_widget_uuid_back_slot(self, cur_result_list):
        self.tableWidget_uuid.setSortingEnabled(False)
        for query_row in cur_result_list:
            self.tableWidget_uuid.insertRow(self.tableWidget_uuid.rowCount())
            row = self.tableWidget_uuid.rowCount() - 1
            logger.info(str(query_row))

            uuid_excluded_flag = query_row[UUID_HEADER.uuid] in GlobalVar.EXCLUDED_UUID

            for idx, col in enumerate(query_row):
                # print col
                if col is None:
                    col = ''
                newitem = QtWidgets.QTableWidgetItem(str(col))
                if idx in [UUID_HEADER.major_dnum, UUID_HEADER.minor_dnum, UUID_HEADER.rows]:
                    if not (col == ''):
                        newitem = QtWidgets.QTableWidgetItem(col)
                        newitem.setData(QtCore.Qt.DisplayRole, int(col))

                elif idx in [UUID_HEADER.included]:
                    # newitem.setData(HACKED_QT_EDITROLE, '')
                    newitem.setData(QtCore.Qt.DisplayRole, '')
                    if int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)
                    newitem.setIcon(get_QIcon_object('./ui/icon/tab-close-other.png'))
                    newitem.setData(QtCore.Qt.DisplayRole, 0)
                    # Hack: hide text
                    temp_font = newitem.font()
                    temp_font.setPointSizeF(0.1)
                    newitem.setFont(temp_font)
                elif idx in [UUID_HEADER.updatable]:
                    # newitem.setData(HACKED_QT_EDITROLE, '')
                    newitem.setData(QtCore.Qt.DisplayRole, '')
                    if col and int(col) > 0:
                        newitem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newitem.setCheckState(QtCore.Qt.Unchecked)

                if idx > UUID_HEADER.fstype:
                    newitem.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

                # Excluded
                if uuid_excluded_flag:
                    newitem.setForeground(QtCore.Qt.gray)
                    temp_font = newitem.font()
                    temp_font.setItalic(True)
                    newitem.setFont(temp_font)
                if not idx in[UUID_HEADER.alias]:
                    newitem.setFlags(newitem.flags() ^ QtCore.Qt.ItemIsEditable)
                # row.append(newitem)
                self.tableWidget_uuid.setItem(row, idx, newitem)

                # newitem = QtWidgets.QProgressBar()
                # newitem.setMaximum(100)
                # newitem.setValue(40)
                # self.tableWidget_uuid.setCellWidget(row, 10, newitem)
                # progressbar = self.tableWidget_uuid.cellWidget(row, 10)
                # progressbar.hide()
            if uuid_excluded_flag and not(self.actionShow_All.isChecked()):
                self.tableWidget_uuid.setRowHidden(row, True)

                # self.model_uuid.appendRow(row)
        # self.refresh_table_uuid_mount_state_slot()
        # self.refresh_mount_state_timer.start()
        self.tableWidget_uuid.setSortingEnabled(True)
        self.statusBar.showMessage("Almost done.",1000)


    def _find_row_of_uuid(self, uuid):
        if self.tableWidget_uuid.rowCount() == 0:
            return -1
        for row in range(self.tableWidget_uuid.rowCount()):
            if self.tableWidget_uuid.item(row, UUID_HEADER.uuid) and uuid == self.tableWidget_uuid.item(row, 3).data(QtCore.Qt.DisplayRole):
                return row
        return -1

    @pyqtSlot()
    def refresh_table_uuid_mount_state_slot(self):
        # if (not SystemDevices.refresh_state()) and \
        #         (SystemDevices.timestamp == self.mount_state_timestamp):
        #     logger.debug('Same, will not refresh.')
        #     return
        self.tableWidget_uuid.setSortingEnabled(False)
        # Note that if sorting is enabled (see sortingEnabled) and column is the current sort column, the row
        # will be moved to the sorted position determined by item.
        # So we disable sorting first and recovery it later.
        deviceDict = SystemDevices.deviceDict
        self.mount_state_timestamp = SystemDevices.timestamp
        for id, device in deviceDict.items():
            uuid = device['uuid']
            row = self._find_row_of_uuid(uuid)
            uuid_excluded_flag = uuid in GlobalVar.EXCLUDED_UUID

            if row < 0:  # uuid does not exist, insert now row
                self.tableWidget_uuid.insertRow(self.tableWidget_uuid.rowCount())
                row = self.tableWidget_uuid.rowCount() - 1

                newitem = QtWidgets.QTableWidgetItem('')
                newitem.setCheckState(QtCore.Qt.Unchecked)
                newitem.setData(QtCore.Qt.DisplayRole, UUID_HEADER.included)
                # Hack: hide text
                temp_font = newitem.font()
                temp_font.setPointSizeF(0.1)
                newitem.setFont(temp_font)
                self.tableWidget_uuid.setItem(row, UUID_HEADER.included, newitem)

                newitem = QtWidgets.QTableWidgetItem('')
                newitem.setCheckState(QtCore.Qt.Unchecked)
                self.tableWidget_uuid.setItem(row, UUID_HEADER.updatable, newitem)

                newitem = QtWidgets.QTableWidgetItem(device['uuid'])
                self.tableWidget_uuid.setItem(row, UUID_HEADER.uuid, newitem)

                for col in [UUID_HEADER.path, UUID_HEADER.alias, UUID_HEADER.name, UUID_HEADER.label, UUID_HEADER.fstype,
                     UUID_HEADER.major_dnum, UUID_HEADER.minor_dnum, UUID_HEADER.rows]:
                    newitem = QtWidgets.QTableWidgetItem()
                    self.tableWidget_uuid.setItem(row, col, newitem)

                if uuid_excluded_flag:
                    for col in range(len(UUID_HEADER_LIST)):
                        newitem = self.tableWidget_uuid.item(row, col)
                        newitem.setForeground(QtCore.Qt.gray)
                        temp_font = newitem.font()
                        temp_font.setItalic(True)
                        newitem.setFont(temp_font)
                    if not (self.actionShow_All.isChecked()):
                        self.tableWidget_uuid.setRowHidden(row, True)

            if device['mountpoint']:
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setIcon(get_QIcon_object('./ui/icon/dev-harddisk.png'))
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setData(QtCore.Qt.DisplayRole, 1)
            else:
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setIcon(get_QIcon_object('./ui/icon/tab-close-other.png'))
                self.tableWidget_uuid.item(row, UUID_HEADER.included).setData(QtCore.Qt.DisplayRole, 0)

            self.tableWidget_uuid.item(row, UUID_HEADER.path).setData(QtCore.Qt.DisplayRole, device['mountpoint'])
            self.tableWidget_uuid.item(row, UUID_HEADER.label).setData(QtCore.Qt.DisplayRole, device['label'])
            self.tableWidget_uuid.item(row, UUID_HEADER.fstype).setData(QtCore.Qt.DisplayRole, device['fstype'])
            self.tableWidget_uuid.item(row, UUID_HEADER.name).setData(QtCore.Qt.DisplayRole, device['name'])

            self.tableWidget_uuid.item(row, UUID_HEADER.major_dnum).setData(QtCore.Qt.DisplayRole, int(id[0]))
            self.tableWidget_uuid.item(row, UUID_HEADER.minor_dnum).setData(QtCore.Qt.DisplayRole, int(id[1]))
        self.tableWidget_uuid.setSortingEnabled(True)

    @pyqtSlot(list)
    def refresh_table_uuid_row_id_slot(self,resulit_list):
        self.tableWidget_uuid.setSortingEnabled(False)
        for uuid, rowid in resulit_list:
            row = self._find_row_of_uuid(uuid)
            if row < 0:  # uuid does not exist, continue
               continue
            self.tableWidget_uuid.item(row, UUID_HEADER.rows).setData(QtCore.Qt.DisplayRole, int(rowid))
        self.tableWidget_uuid.setSortingEnabled(True)

    def get_search_included_uuid(self):
        r = []
        for row in range(self.tableWidget_uuid.rowCount()):
            included = self.tableWidget_uuid.item(row, UUID_HEADER.included).data(QtCore.Qt.CheckStateRole) \
                       == QtCore.Qt.Checked
            if not included:
                continue
            uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).data(QtCore.Qt.DisplayRole)
            path = self.tableWidget_uuid.item(row, UUID_HEADER.path).data(QtCore.Qt.DisplayRole)
            # MainCon.cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid))
            # rows = MainCon.cur.fetchall()[0][0]  # max(rowid)
            rows = int(self.tableWidget_uuid.item(row, UUID_HEADER.rows).data(QtCore.Qt.DisplayRole))
            # TODO: move rows into query thread
            r.append({'uuid': uuid, 'path': path, 'rows': rows})
        return r

        # MainCon.cur.execute('''SELECT `uuid`,`path` FROM UUID WHERE (included=1) ''')
        # r = []
        # for c in MainCon.cur.fetchall():
        #     uuid = c[0]
        #     path = c[1]
        #     MainCon.cur.execute('''SELECT COALESCE(MAX(rowid),0) FROM `%s` ''' % (uuid) )
        #     rows = MainCon.cur.fetchall()[0][0]     # max(rowid)
        #     r.append({'uuid':uuid,
        #               'path':path,
        #               'rows':rows})
        # return r

    def closeEvent(self, event):
        print('close')
        self.distribute_query_thread.quit()
        self.update_db_Thread.quit()
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, ALLICATION_NAME)

        # save uuid state
        uuid_list = []
        for row in range(self.tableWidget_uuid.rowCount()):
            try:
                uuid = self.tableWidget_uuid.item(row, UUID_HEADER.uuid).data(QtCore.Qt.DisplayRole)
                included = self.tableWidget_uuid.item(row, UUID_HEADER.included).data(QtCore.Qt.CheckStateRole) \
                           == QtCore.Qt.Checked
                updatable = self.tableWidget_uuid.item(row, UUID_HEADER.updatable).data(QtCore.Qt.CheckStateRole) \
                            == QtCore.Qt.Checked
                alias = self.tableWidget_uuid.item(row, UUID_HEADER.alias).data(QtCore.Qt.DisplayRole)
                logger.info("uuid: %s, included: %s, alias: %s" % (uuid, included, alias))
                # MainCon.cur.execute(''' UPDATE  UUID SET included=?, updatable=?
                #             WHERE uuid=? ''',
                #             (included, updatable, uuid))
                uuid_list.append([uuid, included, updatable, alias])
            except Exception as e:
                logger.error(str(e))
        self.save_uuid_flag_SIGNAL.emit(uuid_list)

        # save excluded UUID
        settings.setValue('Excluded_UUID', list(GlobalVar.EXCLUDED_UUID))
        settings.setValue('Excluded_UUID_Visible', self.actionShow_All.isChecked())

        # save column width
        width_list_result = []
        width_list_uuid = []
        for i in range(self.model.columnCount()):
            width_list_result.append(self.tableView.columnWidth(i))
        for i in range(self.tableWidget_uuid.columnCount()):
            width_list_uuid.append(self.tableWidget_uuid.columnWidth(i))

        settings.setValue("Column_width_of_reslut_list", width_list_result)
        settings.setValue("Column_width_of_uuid_list", width_list_uuid)

        # save adv frame isVisible
        settings.setValue("Main_Window/Show_Search_Setting_Panel", self.frame_adv_setting.isVisible())

        # save windows position
        settings.setValue("Main_Window/x", self.x())
        settings.setValue("Main_Window/y", self.y())
        settings.setValue("Main_Window/width", self.width())
        settings.setValue("Main_Window/height", self.height())
        desktop = QtWidgets.QDesktopWidget()
        screen_size = QtCore.QRectF(desktop.screenGeometry(desktop.primaryScreen()))
        x = screen_size.x() + screen_size.width()
        y = screen_size.y() + screen_size.height()

        # event.accept()
        super(self.__class__, self).closeEvent(event)

        settings.setValue("Main_Window/DOCK_LOCATIONS", self.saveState())

if __name__ == '__main__':
    app = QApplication(sys.argv)

    while 1:
        # https://docs.python.org/2/library/sqlite3.html
        try:
            MainCon.con = sqlite3.connect(DATABASE_FILE_NAME, check_same_thread=False, timeout=10)
            MainCon.cur = MainCon.con.cursor()
            break
            # MainCon.con.create_function("md5", 1, md5sum)
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText("Fail to connect to databse:\n%s\n\nError message:\n%s" % (DATABASE_FILE_NAME, str(e)))
            msgBox.setInformativeText("Do you want to retry?")
            msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Retry)
            ret = msgBox.exec_()
            if (ret != msgBox.Retry):
                sys.exit(0)

    # from .DB_Builder.update_db_module import Update_DB_Thread

    # if not createDBConnection():
    #     sys.exit(1)
    try:
        window = AppDawnlightSearch()
        window.show()
        window.ini_after_show()

        exit_code = app.exec_()
    except Exception as e:
        logger.error(str(e))
        print(str(e))
    finally:

        logger.info("Close db.")
        logger.info("Vacuum db.")
        try:
            MainCon.cur.execute("VACUUM;")
        except Exception as e:
            logger.error('Fail to vacuum db.')
            logger.error(str(e))

        while 1:
            try:
                MainCon.con.commit()
                MainCon.con.close()
                sys.exit(exit_code)
            except Exception as e:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText("Fail to close databse:\n%s\n\nError message:\n%s" % (DATABASE_FILE_NAME, str(e)))
                msgBox.setInformativeText("Do you want to retry?")
                msgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Retry)
                ret = msgBox.exec_()
                if (ret != msgBox.Retry):
                    sys.exit(exit_code)
        logger.error('Exit...')