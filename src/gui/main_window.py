# -*- coding: utf-8 -*-
"""主窗口模块"""

import os
import json
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QProgressBar, QGroupBox,
    QFormLayout, QTextEdit, QSplitter, QCheckBox, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon

from src.pdf_processor import PDFReader, PDFWriter
from src.llm import TocExtractor
from src.utils.logger import logger
from src.utils.language_manager import language_manager

class WorkerThread(QThread):
    """工作线程，用于后台处理PDF文件"""
    progress_updated = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    finished = pyqtSignal(bool, str, str)
    toc_extracted = pyqtSignal(list)
    
    def __init__(self, task_type: str, **kwargs):
        """
        初始化工作线程
        
        Args:
            task_type: 任务类型 ('extract_toc' 或 'process_pdf')
            kwargs: 任务参数
        """
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        """运行任务"""
        try:
            if self.task_type == 'extract_toc':
                self._extract_toc()
            elif self.task_type == 'process_pdf':
                self._process_pdf()
        except Exception as e:
            self.finished.emit(False, f"处理过程中发生错误: {str(e)}", "")
    
    def _extract_toc(self):
        """提取目录任务（结合图片辅助）"""
        file_path = self.kwargs.get('file_path')
        api_key = self.kwargs.get('api_key')
        start_page = self.kwargs.get('start_page')  # 注意这里保持原始页码，不做减1处理
        end_page = self.kwargs.get('end_page')
        
        self.status_changed.emit("正在加载PDF文件...")
        self.progress_updated.emit(10)
        
        # 读取PDF
        reader = PDFReader(file_path)
        if not reader.load_pdf():
            self.finished.emit(False, "PDF文件加载失败", "")
            return
        
        self.status_changed.emit("正在提取目录文本...")
        self.progress_updated.emit(30)
        
        # 提取目录文本
        toc_text = reader.extract_table_of_contents(start_page - 1, end_page - 1)  # 这里转换为0基索引
        if not toc_text:
            self.finished.emit(False, "无法提取目录文本", "")
            return
        
        self.status_changed.emit("正在处理PDF页面并转换为图片...")
        self.progress_updated.emit(40)
        
        self.status_changed.emit("正在使用LLM分析目录（结合图片辅助）...")
        self.progress_updated.emit(60)
        
        model_name = self.kwargs.get('model_name', 'gpt-4-vision-preview')
        base_url = self.kwargs.get('base_url')
        
        # 使用LLM和图片辅助提取目录
        toc_extractor = TocExtractor(api_key, model_name=model_name, base_url=base_url)
        if not toc_extractor.initialize():
            # 如果初始化失败，尝试降级到普通模型，但仍然使用用户指定的模型名称
            toc_extractor = TocExtractor(api_key, model_name=model_name, base_url=base_url)
            if not toc_extractor.initialize():
                self.finished.emit(False, "LLM初始化失败，请检查API密钥", "")
                return
            # 使用纯文本方式
            toc_data = toc_extractor.extract_toc_from_text(toc_text)
        else:
            # 尝试使用图片辅助方式提取目录
            toc_data = toc_extractor.extract_toc_from_text_with_images(
                toc_text, file_path, start_page, end_page
            )
            
            if not toc_data:
                # 如果图片辅助失败，降级使用纯文本方式，但仍然使用用户指定的模型名称
                self.status_changed.emit("图片辅助失败，尝试纯文本提取...")
                toc_extractor = TocExtractor(api_key, model_name=model_name, base_url=base_url)
                if not toc_extractor.initialize():
                    self.finished.emit(False, "LLM初始化失败，请检查API密钥", "")
                    return
                toc_data = toc_extractor.extract_toc_from_text(toc_text)
        
        if not toc_data:
            self.finished.emit(False, "未能识别有效目录", "")
            return
        
        # 验证目录数据
        toc_data = toc_extractor.validate_toc_data(toc_data, reader.get_num_pages())
        
        self.status_changed.emit("目录提取完成")
        self.progress_updated.emit(100)
        
        # 发送提取的目录数据
        self.toc_extracted.emit(toc_data)
        self.finished.emit(True, "目录提取成功", "")
    
    def _process_pdf(self):
        """处理PDF任务"""
        input_file = self.kwargs.get('input_file')
        output_file = self.kwargs.get('output_file')
        toc_data = self.kwargs.get('toc_data')
        page_offset = self.kwargs.get('page_offset')
        
        self.status_changed.emit("正在加载PDF文件...")
        self.progress_updated.emit(20)
        
        # 应用页码偏移
        adjusted_toc = []
        for item in toc_data:
            adjusted_item = item.copy()
            if adjusted_item['page'] != -1:
                adjusted_item['page'] += page_offset - 1  # 转换为0基索引
            adjusted_toc.append(adjusted_item)
        
        self.status_changed.emit("正在创建PDF写入器...")
        self.progress_updated.emit(40)
        
        # 创建PDF写入器
        writer = PDFWriter(input_file)
        if not writer.load():
            self.finished.emit(False, "PDF文件加载失败", "")
            return
        
        self.status_changed.emit("正在创建书签...")
        self.progress_updated.emit(60)
        
        # 创建书签
        if not writer.create_bookmarks_from_toc(adjusted_toc):
            self.finished.emit(False, "创建书签失败", "")
            return
        
        self.status_changed.emit("正在保存文件...")
        self.progress_updated.emit(80)
        
        # 保存文件
        if not writer.save(output_file):
            self.finished.emit(False, "保存文件失败", "")
            return
        
        self.status_changed.emit("处理完成")
        self.progress_updated.emit(100)
        
        self.finished.emit(True, "PDF处理成功", output_file)

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        self.pdf_file_path = None
        self.toc_data = None
        self.worker_thread = None
        self.settings = QSettings("EasyBookmark", "EasyBookmark")
        
        # 窗口图标将在main.py中设置，避免重复设置
        
        # 为方便使用，定义翻译方法的别名
        self._ = language_manager._
        
        logger.info(self._("status_idle"))
        self.init_ui()
        self.load_settings()
        
        # 添加语言选择器（临时实现，后续可以集成到UI中）
        self.setup_language_selection()
    
    def setup_language_selection(self):
        """设置语言选择功能"""
        # 这里可以添加UI控件来选择语言
        # 目前仅提供方法接口，方便后续扩展
        pass
    
    def change_language(self, language_code: str):
        """
        更改应用程序语言
        
        Args:
            language_code: 语言代码，如 'zh', 'en' 等
        """
        if language_manager.load_language(language_code):
            # 更新翻译方法的别名
            self._ = language_manager._
            # 更新窗口标题和UI文本
            self.setWindowTitle(self._("window_title"))
            # 刷新UI
            self.refresh_ui_texts()
            # 保存设置
            self.save_settings()
            logger.info(f"语言已更改为: {language_code}")
            return True
        return False
    
    def refresh_ui_texts(self):
        """刷新UI文本，应用新的语言设置"""
        # 这里需要根据实际UI实现更新所有文本控件
        # 暂时只更新窗口标题，后续需要完善所有UI元素的文本更新
        pass
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle(self._("window_title"))
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        
        # ========== 文件上传区域 ==========
        file_group = QGroupBox(self._("file_upload_section"))
        file_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit, 1)
        
        browse_btn = QPushButton(self._("browse_button"))
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # ========== 参数设置区域 ==========
        param_group = QGroupBox(self._("parameter_settings"))
        param_layout = QFormLayout()
        
        # API Key输入
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        param_layout.addRow(QLabel(self._("api_key_label")), self.api_key_edit)
        
        # 模型名称输入 - 使用placeholder作为灰色提示文字
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText(self._("model_name_placeholder"))
        param_layout.addRow(QLabel(self._("model_name_label")), self.model_name_edit)
        
        # API基础URL输入 - 使用placeholder作为灰色提示文字
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText(self._("base_url_placeholder"))
        param_layout.addRow(QLabel(self._("base_url_label")), self.base_url_edit)
        
        # 显示API Key复选框
        show_key_check = QCheckBox(self._("show_api_key_checkbox"))
        show_key_check.toggled.connect(self.toggle_api_key_visibility)
        param_layout.addWidget(show_key_check)
        
        # 目录页码范围
        page_range_layout = QHBoxLayout()
        self.start_page_spin = QSpinBox()
        self.start_page_spin.setMinimum(1)
        self.start_page_spin.setMaximum(9999)
        self.start_page_spin.setValue(1)
        page_range_layout.addWidget(self.start_page_spin)
        page_range_layout.addWidget(QLabel(self._("to")))
        self.end_page_spin = QSpinBox()
        self.end_page_spin.setMinimum(1)
        self.end_page_spin.setMaximum(9999)
        self.end_page_spin.setValue(5)
        page_range_layout.addWidget(self.end_page_spin)
        
        param_layout.addRow(QLabel(self._("toc_page_range_label")), page_range_layout)
        
        # 页码偏置
        self.offset_spin = QSpinBox()
        self.offset_spin.setMinimum(-999)
        self.offset_spin.setMaximum(9999)
        self.offset_spin.setValue(0)
        param_layout.addRow(QLabel(self._("page_offset_label")), self.offset_spin)
        
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)
        
        # ========== 按钮区域 ==========
        btn_layout = QHBoxLayout()
        
        self.extract_btn = QPushButton(self._("extract_toc_button"))
        self.extract_btn.clicked.connect(self.start_extract_toc)
        btn_layout.addWidget(self.extract_btn)
        
        self.import_json_btn = QPushButton(self._("import_json_toc_button"))
        self.import_json_btn.clicked.connect(self.import_json_toc)
        btn_layout.addWidget(self.import_json_btn)
        
        self.process_btn = QPushButton(self._("process_pdf_button"))
        self.process_btn.clicked.connect(self.start_process_pdf)
        self.process_btn.setEnabled(False)
        btn_layout.addWidget(self.process_btn)
        
        self.reset_btn = QPushButton(self._("reset_button"))
        self.reset_btn.clicked.connect(self.reset_all)
        btn_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(btn_layout)
        
        # ========== 进度区域 ==========
        self.status_label = QLabel(self._("status_idle"))
        main_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # ========== 结果显示区域 ==========
        result_group = QGroupBox(self._("toc_preview_section"))
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group, 1)
        
    def load_settings(self):
        """加载保存的设置"""
        api_key = self.settings.value("api_key", "")
        self.api_key_edit.setText(api_key)
        
        # 只在有保存值时设置，否则保持placeholder显示
        model_name = self.settings.value("model_name", "")
        if model_name:
            self.model_name_edit.setText(model_name)
        
        # 只在有保存值时设置，否则保持placeholder显示
        base_url = self.settings.value("base_url", "")
        if base_url:
            self.base_url_edit.setText(base_url)
        
        start_page = self.settings.value("start_page", 1, type=int)
        self.start_page_spin.setValue(start_page)
        
        end_page = self.settings.value("end_page", 5, type=int)
        self.end_page_spin.setValue(end_page)
        
        offset = self.settings.value("offset", 0, type=int)
        self.offset_spin.setValue(offset)
        
        # 加载语言设置
        language = self.settings.value("language", "")
        if language:
            language_manager.load_language(language)
        
        logger.info("已加载应用程序设置")
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("api_key", self.api_key_edit.text())
        self.settings.setValue("model_name", self.model_name_edit.text())
        self.settings.setValue("base_url", self.base_url_edit.text())
        self.settings.setValue("start_page", self.start_page_spin.value())
        self.settings.setValue("end_page", self.end_page_spin.value())
        self.settings.setValue("offset", self.offset_spin.value())
        
        # 保存当前语言设置到QSettings
        self.settings.setValue("language", language_manager.current_language)
        
        # 同时保存语言设置到config.json文件
        language_manager.save_to_config_file(language_manager.current_language)
        
        logger.info("已保存应用程序设置")
    
    def browse_file(self):
        """浏览并选择PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self._("select_pdf_file"), "", self._("pdf_files_filter")
        )
        if file_path:
            self.pdf_file_path = file_path
            self.file_path_edit.setText(file_path)
            logger.info(f"选择PDF文件: {file_path}")
            # 尝试获取PDF页数并更新页码范围
            reader = PDFReader(self.pdf_file_path)
            if reader.load_pdf():
                num_pages = reader.get_num_pages()
                self.start_page_spin.setMaximum(num_pages)
                self.end_page_spin.setMaximum(num_pages)
                self.end_page_spin.setValue(min(5, num_pages))
    
    def _update_page_range(self):
        """更新页码范围"""
        if self.pdf_file_path:
            reader = PDFReader(self.pdf_file_path)
            if reader.load_pdf():
                num_pages = reader.get_num_pages()
                self.start_page_spin.setMaximum(num_pages)
                self.end_page_spin.setMaximum(num_pages)
                self.end_page_spin.setValue(min(5, num_pages))
    
    def toggle_api_key_visibility(self, checked):
        """切换API Key可见性"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def start_extract_toc(self):
        """开始提取目录"""
        # 验证输入
        if not self._validate_extract_input():
            return
        
        # 保存设置
        self.save_settings()
        
        # 禁用按钮
        self._disable_controls(True)
        
        logger.info(f"开始提取目录: 文件={self.pdf_file_path}, 页码范围={self.start_page_spin.value()}-{self.end_page_spin.value()}")
        
        # 创建工作线程
        self.worker_thread = WorkerThread(
            'extract_toc',
            file_path=self.pdf_file_path,
            api_key=self.api_key_edit.text(),
            model_name=self.model_name_edit.text() or "gpt-4-vision-preview",
            base_url=self.base_url_edit.text() if self.base_url_edit.text() else None,
            start_page=self.start_page_spin.value(),
            end_page=self.end_page_spin.value()
        )
        
        # 连接信号
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.status_changed.connect(self.update_status)
        self.worker_thread.toc_extracted.connect(self.on_toc_extracted)
        self.worker_thread.finished.connect(self.on_task_finished)
        
        # 启动线程
        self.worker_thread.start()
    
    def start_process_pdf(self):
        """开始处理PDF"""
        # 获取输出文件路径
        output_file, _ = QFileDialog.getSaveFileName(
            self, self._("save_processed_pdf"), "", self._("pdf_files_filter")
        )
        if not output_file:
            return
        
        # 禁用按钮
        self._disable_controls(True)
        
        logger.info(f"开始处理PDF: 输入={self.pdf_file_path}, 输出={output_file}, 页码偏置={self.offset_spin.value()}")
        
        # 创建工作线程
        self.worker_thread = WorkerThread(
            'process_pdf',
            input_file=self.pdf_file_path,
            output_file=output_file,
            toc_data=self.toc_data,
            page_offset=self.offset_spin.value()
        )
        
        # 连接信号
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.status_changed.connect(self.update_status)
        self.worker_thread.finished.connect(self.on_task_finished)
        
        # 启动线程
        self.worker_thread.start()
    
    def _validate_extract_input(self):
        """验证提取目录的输入"""
        if not self.pdf_file_path:
            QMessageBox.warning(self, self._("warning"), self._("please_select_pdf_file"))
            return False
        
        if not os.path.exists(self.pdf_file_path):
            QMessageBox.warning(self, self._("warning"), self._("pdf_file_not_exist"))
            return False
        
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, self._("warning"), self._("please_input_api_key"))
            return False
        
        start_page = self.start_page_spin.value()
        end_page = self.end_page_spin.value()
        if start_page > end_page:
            QMessageBox.warning(self, self._("warning"), self._("start_page_greater_than_end"))
            return False
        
        return True
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """更新状态文本"""
        self.status_label.setText(status)
    
    def on_toc_extracted(self, toc_data):
        """处理提取的目录数据"""
        self.toc_data = toc_data
        logger.info(f"成功提取到 {len(toc_data)} 个目录项")
        
        # 显示目录预览
        preview_text = ""
        for item in toc_data:
            indent = "  " * (item['level'] - 1)
            preview_text += f"{indent}[{item['page']}] {item['title']}\n"
        
        self.result_text.setText(preview_text)
        self.process_btn.setEnabled(True)
    
    def on_task_finished(self, success, message, output_file):
        """任务完成处理"""
        # 启用控件
        self._disable_controls(False)
        
        # 显示消息
        if success:
            QMessageBox.information(self, self._("success"), message)
            # 如果是处理PDF任务，打开输出文件目录
            if output_file and os.path.exists(output_file):
                if QMessageBox.question(self, self._("completed"), self._("open_output_folder"), 
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    os.startfile(os.path.dirname(output_file))
        else:
            QMessageBox.critical(self, self._("error"), message)
    
    def _disable_controls(self, disable):
        """禁用/启用控件"""
        self.extract_btn.setEnabled(not disable)
        self.import_json_btn.setEnabled(not disable)
        self.process_btn.setEnabled(not disable and self.toc_data is not None)
        self.reset_btn.setEnabled(not disable)
        
    def reset_all(self):
        """重置所有设置"""
        self.pdf_file_path = None
        self.toc_data = None
        self.file_path_edit.setText("")
        self.result_text.setText("")
        self.progress_bar.setValue(0)
        self.status_label.setText(self._("status_idle"))
        self.process_btn.setEnabled(False)
        
        # 重置页码范围
        self.start_page_spin.setValue(1)
        self.end_page_spin.setValue(5)
        self.offset_spin.setValue(0)
        
        logger.info("已重置所有设置")
    
    def import_json_toc(self):
        """导入JSON格式的目录数据"""
        if not self.pdf_file_path:
            QMessageBox.warning(self, self._("warning"), self._("please_select_pdf_file"))
            return
        
        # 创建一个输入对话框
        input_dialog = QMessageBox()
        input_dialog.setWindowTitle(self._("input_json_toc"))
        input_dialog.setText(self._("please_paste_json_toc"))
        
        # 创建多行文本编辑框
        text_edit = QTextEdit()
        # 设置更完整的JSON示例
        complete_example = '''[
  {
    "title": "第一章 引言",
    "page": 1,
    "level": 1
  },
  {
    "title": "1.1 研究背景",
    "page": 2,
    "level": 2
  },
  {
    "title": "1.2 研究目的",
    "page": 5,
    "level": 2
  },
  {
    "title": "第二章 文献综述",
    "page": 8,
    "level": 1
  },
  {
    "title": "2.1 国内研究现状",
    "page": 9,
    "level": 2
  },
  {
    "title": "2.1.1 主要成果",
    "page": 10,
    "level": 3
  },
  {
    "title": "第三章 研究方法",
    "page": 15,
    "level": 1
  }
]'''
        text_edit.setText(complete_example)  # 直接设置为文本内容，而不是占位符
        # 增大输入框尺寸
        text_edit.setMinimumHeight(300)
        text_edit.setMinimumWidth(500)
        
        # 添加到对话框
        input_dialog.layout().addWidget(text_edit, 1, 0, 1, input_dialog.layout().columnCount())
        
        # 设置按钮
        input_dialog.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        # 显示对话框
        if input_dialog.exec() != QMessageBox.StandardButton.Ok:
            return
        
        toc_json = text_edit.toPlainText()
        
        if not toc_json:
            return
        
        try:
            
            # 使用PDFReader设置用户目录数据
            reader = PDFReader()
            toc_data = reader.set_user_toc_data(toc_json)
            
            if toc_data:
                # 验证目录页码是否在PDF范围内
                reader_with_pdf = PDFReader(self.pdf_file_path)
                if reader_with_pdf.load_pdf():
                    max_pages = reader_with_pdf.get_num_pages()
                    # 过滤掉页码超出范围的项
                    valid_toc_data = []
                    for item in toc_data:
                        if item['page'] == -1 or (item['page'] >= 1 and item['page'] <= max_pages):
                            valid_toc_data.append(item)
                        else:
                            logger.warning(f"跳过无效页码的目录项: {item['title']} (页码: {item['page']})")
                    
                    self.toc_data = valid_toc_data
                    logger.info(f"成功导入 {len(valid_toc_data)} 个有效目录项")
                    
                    # 显示目录预览
                    preview_text = ""
                    for item in valid_toc_data:
                        indent = "  " * (item['level'] - 1)
                        preview_text += f"{indent}[{item['page']}] {item['title']}\n"
                    
                    self.result_text.setText(preview_text)
                    self.process_btn.setEnabled(True)
                    self.status_label.setText(f"已导入 {len(valid_toc_data)} 个目录项")
                    
                    QMessageBox.information(self, "成功", f"成功导入 {len(valid_toc_data)} 个目录项")
                else:
                    QMessageBox.critical(self, "错误", "PDF文件加载失败")
            else:
                QMessageBox.critical(self, "错误", "无法解析JSON格式的目录数据")
        
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "JSON格式无效，请检查文件内容")
        except Exception as e:
            logger.error(f"导入JSON目录失败: {e}")
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 保存设置
        self.save_settings()
        
        # 检查工作线程
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
            logger.info("已终止工作线程")
        
        logger.info("应用程序关闭")
        event.accept()