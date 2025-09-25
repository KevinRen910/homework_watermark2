import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem, QSlider, 
    QTabWidget, QLineEdit, QComboBox, QCheckBox, QGroupBox, QGridLayout,
    QMessageBox, QSplitter, QFrame, QAction, QMenu, QMenuBar, QToolBar,
    QInputDialog
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon, QImage
from PyQt5.QtCore import Qt, QPoint, QSize
from PIL import Image, ImageDraw, ImageFont, ImageQt

class WatermarkApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("水印文件本地应用")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化数据
        self.image_paths = []
        self.current_index = -1
        self.watermark_text = "水印"
        self.text_opacity = 50  # 默认50%透明度
        self.watermark_position = QPoint(0, 0)
        self.output_format = "PNG"
        self.output_folder = os.path.join(os.getcwd(), "output")
        self.file_naming_rule = "original"  # original, prefix, suffix
        self.custom_prefix = "wm_"
        self.custom_suffix = "_watermarked"
        self.templates = {}
        self.template_folder = os.path.join(os.getcwd(), "templates")
        
        # 确保必要的文件夹存在
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.template_folder, exist_ok=True)
        
        # 加载上次保存的设置
        self.load_settings()
        
        # 创建界面
        self.init_ui()
        
        # 创建菜单和工具栏
        self.create_menus_toolbars()
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def init_ui(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 顶部状态栏
        self.status_bar = QLabel("就绪")
        main_layout.addWidget(self.status_bar)
        
        # 创建分割器
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 左侧图片列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 图片列表标题和按钮
        list_header_layout = QHBoxLayout()
        list_header_layout.addWidget(QLabel("图片列表"))
        add_button = QPushButton("添加图片")
        add_button.clicked.connect(self.add_images)
        list_header_layout.addWidget(add_button)
        add_folder_button = QPushButton("添加文件夹")
        add_folder_button.clicked.connect(self.add_folder)
        list_header_layout.addWidget(add_folder_button)
        left_layout.addLayout(list_header_layout)
        
        # 图片列表控件
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(120, 120))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setSpacing(10)
        self.image_list.itemClicked.connect(self.on_image_selected)
        left_layout.addWidget(self.image_list)
        
        # 导出按钮
        export_button = QPushButton("导出所有图片")
        export_button.clicked.connect(self.export_all_images)
        left_layout.addWidget(export_button)
        
        # 将左侧部件添加到分割器
        main_splitter.addWidget(left_widget)
        
        # 中央预览区域
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # 预览标签
        self.preview_label = QLabel("拖放图片到此处预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.preview_label.setAcceptDrops(True)
        self.preview_label.mousePressEvent = self.on_preview_click
        self.preview_label.mouseMoveEvent = self.on_preview_drag
        self.preview_label.mouseReleaseEvent = self.on_preview_release
        self.dragging = False
        
        center_layout.addWidget(self.preview_label)
        
        # 预设位置按钮
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("预设位置："))
        positions = ["左上", "右上", "左下", "右下", "中心"]
        for pos in positions:
            btn = QPushButton(pos)
            btn.clicked.connect(lambda checked, p=pos: self.set_preset_position(p))
            position_layout.addWidget(btn)
        center_layout.addLayout(position_layout)
        
        # 将中央部件添加到分割器
        main_splitter.addWidget(center_widget)
        
        # 右侧设置面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 创建设置标签页
        tab_widget = QTabWidget()
        
        # 文本水印设置
        text_watermark_tab = QWidget()
        text_layout = QVBoxLayout(text_watermark_tab)
        
        # 文本内容
        text_group = QGroupBox("文本水印")
        text_group_layout = QVBoxLayout()
        
        text_input_layout = QHBoxLayout()
        text_input_layout.addWidget(QLabel("水印文本："))
        self.text_input = QLineEdit(self.watermark_text)
        self.text_input.textChanged.connect(self.on_text_changed)
        text_input_layout.addWidget(self.text_input)
        text_group_layout.addLayout(text_input_layout)
        
        # 透明度设置
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度："))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(self.text_opacity)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel(f"{self.text_opacity}%")
        opacity_layout.addWidget(self.opacity_label)
        text_group_layout.addLayout(opacity_layout)
        
        text_group.setLayout(text_group_layout)
        text_layout.addWidget(text_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        # 输出格式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式："))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        self.format_combo.setCurrentText(self.output_format)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_layout.addWidget(self.format_combo)
        output_layout.addLayout(format_layout)
        
        # 输出文件夹
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("输出文件夹："))
        self.folder_path = QLineEdit(self.output_folder)
        folder_layout.addWidget(self.folder_path)
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_output_folder)
        folder_layout.addWidget(browse_button)
        output_layout.addLayout(folder_layout)
        
        # 文件命名规则
        naming_layout = QHBoxLayout()
        naming_layout.addWidget(QLabel("命名规则："))
        self.naming_combo = QComboBox()
        self.naming_combo.addItems(["保留原文件名", "添加前缀", "添加后缀"])
        self.naming_combo.setCurrentIndex({
            "original": 0, "prefix": 1, "suffix": 2
        }.get(self.file_naming_rule, 0))
        self.naming_combo.currentIndexChanged.connect(self.on_naming_changed)
        naming_layout.addWidget(self.naming_combo)
        output_layout.addLayout(naming_layout)
        
        # 前缀输入
        self.prefix_layout = QHBoxLayout()
        self.prefix_layout.addWidget(QLabel("前缀："))
        self.prefix_input = QLineEdit(self.custom_prefix)
        self.prefix_input.textChanged.connect(self.on_prefix_changed)
        self.prefix_layout.addWidget(self.prefix_input)
        output_layout.addLayout(self.prefix_layout)
        
        # 后缀输入
        self.suffix_layout = QHBoxLayout()
        self.suffix_layout.addWidget(QLabel("后缀："))
        self.suffix_input = QLineEdit(self.custom_suffix)
        self.suffix_input.textChanged.connect(self.on_suffix_changed)
        self.suffix_layout.addWidget(self.suffix_input)
        output_layout.addLayout(self.suffix_layout)
        
        output_group.setLayout(output_layout)
        text_layout.addWidget(output_group)
        
        text_layout.addStretch()
        tab_widget.addTab(text_watermark_tab, "水印设置")
        
        # 模板设置
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        
        template_group = QGroupBox("水印模板")
        template_group_layout = QVBoxLayout()
        
        # 模板列表
        self.template_list = QListWidget()
        template_group_layout.addWidget(QLabel("已保存模板："))
        template_group_layout.addWidget(self.template_list)
        
        # 模板按钮布局
        template_buttons_layout = QHBoxLayout()
        save_template_btn = QPushButton("保存当前设置为模板")
        save_template_btn.clicked.connect(self.save_template)
        template_buttons_layout.addWidget(save_template_btn)
        
        load_template_btn = QPushButton("加载选中模板")
        load_template_btn.clicked.connect(self.load_template)
        template_buttons_layout.addWidget(load_template_btn)
        
        delete_template_btn = QPushButton("删除选中模板")
        delete_template_btn.clicked.connect(self.delete_template)
        template_buttons_layout.addWidget(delete_template_btn)
        
        template_group_layout.addLayout(template_buttons_layout)
        
        template_group.setLayout(template_group_layout)
        template_layout.addWidget(template_group)
        
        template_layout.addStretch()
        tab_widget.addTab(template_tab, "模板管理")
        
        # 添加标签页到右侧布局
        right_layout.addWidget(tab_widget)
        
        # 将右侧部件添加到分割器
        main_splitter.addWidget(right_widget)
        
        # 设置分割器的初始大小
        main_splitter.setSizes([300, 600, 300])
        
        # 加载已保存的模板
        self.load_templates()
        
    def create_menus_toolbars(self):
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_image_action = QAction("添加图片", self)
        add_image_action.triggered.connect(self.add_images)
        file_menu.addAction(add_image_action)
        
        add_folder_action = QAction("添加文件夹", self)
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出所有图片", self)
        export_action.triggered.connect(self.export_all_images)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑")
        
        save_settings_action = QAction("保存设置", self)
        save_settings_action.triggered.connect(self.save_settings)
        edit_menu.addAction(save_settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 创建工具栏
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        toolbar.addAction(add_image_action)
        toolbar.addAction(add_folder_action)
        toolbar.addAction(export_action)
    
    def add_images(self):
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择图片", "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*)", 
            options=options
        )
        
        if file_paths:
            self.add_files_to_list(file_paths)
    
    def add_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "", options=options
        )
        
        if folder:
            # 获取文件夹中的所有图片文件
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            file_paths = []
            
            for root, _, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in image_extensions):
                        file_paths.append(os.path.join(root, file))
            
            if file_paths:
                self.add_files_to_list(file_paths)
    
    def add_files_to_list(self, file_paths):
        for file_path in file_paths:
            if file_path not in self.image_paths:
                self.image_paths.append(file_path)
                
                # 创建列表项
                item = QListWidgetItem()
                
                # 创建缩略图
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(scaled_pixmap))
                
                # 设置文件名
                file_name = os.path.basename(file_path)
                item.setText(file_name)
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                
                # 将项添加到列表
                self.image_list.addItem(item)
        
        # 如果是第一次添加图片，自动选择第一张
        if len(self.image_paths) > 0 and self.current_index == -1:
            self.image_list.setCurrentRow(0)
            self.on_image_selected(self.image_list.item(0))
    
    def on_image_selected(self, item):
        if item:
            index = self.image_list.row(item)
            if 0 <= index < len(self.image_paths):
                self.current_index = index
                self.update_preview()
    
    def update_preview(self):
        if 0 <= self.current_index < len(self.image_paths):
            file_path = self.image_paths[self.current_index]
            
            try:
                # 打开图片并添加水印进行预览
                image = Image.open(file_path)
                preview_image = self.add_watermark_to_image(image, preview=True)
                
                # 转换为QPixmap显示
                q_image = self.pil_to_qimage(preview_image)
                pixmap = QPixmap.fromImage(q_image)
                
                # 调整大小以适应预览窗口
                max_size = self.preview_label.size()
                scaled_pixmap = pixmap.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 更新状态栏
                self.status_bar.setText(f"预览: {os.path.basename(file_path)}")
                
            except Exception as e:
                self.status_bar.setText(f"错误: 无法预览图片 - {str(e)}")
    
    def add_watermark_to_image(self, image, preview=False):
        # 创建图片副本
        watermarked_image = image.copy()
        
        # 如果是RGBA模式，转换为RGB模式（除非是PNG格式输出）
        if watermarked_image.mode == 'RGBA' and (self.output_format == 'JPEG' or (preview and self.output_format == 'JPEG')):
            background = Image.new('RGB', watermarked_image.size, (255, 255, 255))
            background.paste(watermarked_image, mask=watermarked_image.split()[3])
            watermarked_image = background
        
        # 创建绘图对象
        draw = ImageDraw.Draw(watermarked_image, 'RGBA')
        
        # 计算水印位置
        if self.watermark_position.isNull() or (self.watermark_position.x() == 0 and self.watermark_position.y() == 0):
            # 默认位置：右下角
            position = (watermarked_image.width - 150, watermarked_image.height - 50)
        else:
            position = (self.watermark_position.x(), self.watermark_position.y())
        
        # 计算字体大小
        font_size = max(12, min(watermarked_image.width, watermarked_image.height) // 20)
        
        try:
            # 尝试加载系统字体
            font = ImageFont.truetype("simhei.ttf", font_size)
        except:
            # 如果加载失败，使用默认字体
            font = ImageFont.load_default()
        
        # 绘制文本水印
        opacity = int(255 * (1 - self.text_opacity / 100))
        draw.text(position, self.watermark_text, font=font, fill=(255, 0, 0, opacity))
        
        return watermarked_image
    
    def pil_to_qimage(self, pil_image):
        # 将PIL图像转换为QImage
        if pil_image.mode == 'RGB':
            # 对于RGB模式，我们需要将数据转换为RGBA格式
            # 创建一个临时图像
            temp_image = Image.new('RGBA', pil_image.size, (255, 255, 255, 255))
            temp_image.paste(pil_image, mask=None)
            # 将图像数据转换为字节
            data = temp_image.tobytes('raw', 'RGBA')
            # 创建QImage
            q_image = QImage(data, temp_image.size[0], temp_image.size[1], QImage.Format_RGBA8888)
        elif pil_image.mode == 'RGBA':
            # 对于RGBA模式，直接使用RGBA8888格式
            data = pil_image.tobytes('raw', 'RGBA')
            q_image = QImage(data, pil_image.size[0], pil_image.size[1], QImage.Format_RGBA8888)
        else:
            # 对于其他模式，转换为RGB模式
            rgb_image = pil_image.convert('RGB')
            data = rgb_image.tobytes('raw', 'RGB')
            q_image = QImage(data, rgb_image.size[0], rgb_image.size[1], QImage.Format_RGB888)
            q_image = q_image.rgbSwapped()  # Qt的RGB顺序与PIL不同
        
        return q_image
    
    def on_text_changed(self, text):
        self.watermark_text = text
        self.update_preview()
    
    def on_opacity_changed(self, value):
        self.text_opacity = value
        self.opacity_label.setText(f"{value}%")
        self.update_preview()
    
    def on_format_changed(self, text):
        self.output_format = text
    
    def browse_output_folder(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", self.output_folder, options=options
        )
        
        if folder:
            self.output_folder = folder
            self.folder_path.setText(folder)
    
    def on_naming_changed(self, index):
        if index == 0:
            self.file_naming_rule = "original"
            self.prefix_layout.setEnabled(False)
            self.suffix_layout.setEnabled(False)
        elif index == 1:
            self.file_naming_rule = "prefix"
            self.prefix_layout.setEnabled(True)
            self.suffix_layout.setEnabled(False)
        elif index == 2:
            self.file_naming_rule = "suffix"
            self.prefix_layout.setEnabled(False)
            self.suffix_layout.setEnabled(True)
    
    def on_prefix_changed(self, text):
        self.custom_prefix = text
    
    def on_suffix_changed(self, text):
        self.custom_suffix = text
    
    def on_preview_click(self, event):
        if self.current_index != -1 and event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.pos()
            self.watermark_position = event.pos()
            self.update_preview()
    
    def on_preview_drag(self, event):
        if self.dragging and self.current_index != -1:
            self.watermark_position = event.pos()
            self.update_preview()
    
    def on_preview_release(self, event):
        if self.dragging and self.current_index != -1:
            self.dragging = False
            self.watermark_position = event.pos()
            self.update_preview()
    
    def set_preset_position(self, position):
        if self.current_index != -1:
            file_path = self.image_paths[self.current_index]
            image = Image.open(file_path)
            
            # 获取预览标签的缩放因子
            if self.preview_label.pixmap():
                pixmap = self.preview_label.pixmap()
                scale_x = image.width / pixmap.width()
                scale_y = image.height / pixmap.height()
                
                # 根据预设位置计算水印位置
                if position == "左上":
                    pos = QPoint(int(20 * scale_x), int(20 * scale_y))
                elif position == "右上":
                    pos = QPoint(int((pixmap.width() - 150) * scale_x), int(20 * scale_y))
                elif position == "左下":
                    pos = QPoint(int(20 * scale_x), int((pixmap.height() - 50) * scale_y))
                elif position == "右下":
                    pos = QPoint(int((pixmap.width() - 150) * scale_x), int((pixmap.height() - 50) * scale_y))
                elif position == "中心":
                    pos = QPoint(int((pixmap.width() - 75) * scale_x), int((pixmap.height() - 25) * scale_y))
                    
                self.watermark_position = pos
                self.update_preview()
    
    def export_all_images(self):
        if not self.image_paths:
            QMessageBox.warning(self, "警告", "没有图片可导出")
            return
        
        # 确保输出文件夹存在
        os.makedirs(self.output_folder, exist_ok=True)
        
        # 导出所有图片
        for i, file_path in enumerate(self.image_paths):
            try:
                # 更新状态栏
                self.status_bar.setText(f"正在导出图片 {i+1}/{len(self.image_paths)}: {os.path.basename(file_path)}")
                QApplication.processEvents()  # 刷新界面
                
                # 打开图片
                image = Image.open(file_path)
                
                # 添加水印
                watermarked_image = self.add_watermark_to_image(image)
                
                # 确定输出文件名
                file_name = os.path.basename(file_path)
                base_name, ext = os.path.splitext(file_name)
                
                if self.file_naming_rule == "original":
                    output_name = f"{base_name}.{self.output_format.lower()}"
                elif self.file_naming_rule == "prefix":
                    output_name = f"{self.custom_prefix}{base_name}.{self.output_format.lower()}"
                elif self.file_naming_rule == "suffix":
                    output_name = f"{base_name}{self.custom_suffix}.{self.output_format.lower()}"
                
                # 保存图片
                output_path = os.path.join(self.output_folder, output_name)
                
                # 根据格式设置保存参数
                if self.output_format == "PNG":
                    watermarked_image.save(output_path, format="PNG")
                else:
                    # 对于JPEG，确保图片是RGB模式
                    if watermarked_image.mode != "RGB":
                        watermarked_image = watermarked_image.convert("RGB")
                    watermarked_image.save(output_path, format="JPEG", quality=95)
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法导出图片 {os.path.basename(file_path)}: {str(e)}")
        
        # 导出完成
        self.status_bar.setText(f"导出完成！共 {len(self.image_paths)} 张图片，保存至: {self.output_folder}")
        QMessageBox.information(self, "完成", f"成功导出 {len(self.image_paths)} 张图片")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        
        # 处理拖放的文件和文件夹
        file_paths = []
        for file in files:
            if os.path.isdir(file):
                # 处理文件夹
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
                for root, _, files_in_dir in os.walk(file):
                    for file_in_dir in files_in_dir:
                        if any(file_in_dir.lower().endswith(ext) for ext in image_extensions):
                            file_paths.append(os.path.join(root, file_in_dir))
            elif os.path.isfile(file):
                # 处理文件
                file_paths.append(file)
        
        if file_paths:
            self.add_files_to_list(file_paths)
    
    def save_template(self):
        template_name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称：")
        if ok and template_name:
            # 保存当前设置为模板
            template = {
                "watermark_text": self.watermark_text,
                "text_opacity": self.text_opacity,
                "output_format": self.output_format,
                "file_naming_rule": self.file_naming_rule,
                "custom_prefix": self.custom_prefix,
                "custom_suffix": self.custom_suffix
            }
            
            # 保存到模板字典
            self.templates[template_name] = template
            
            # 保存到文件
            template_file = os.path.join(self.template_folder, f"{template_name}.json")
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=4)
            
            # 更新模板列表
            self.load_templates()
            
            QMessageBox.information(self, "成功", f"模板 '{template_name}' 已保存")
    
    def load_template(self):
        current_item = self.template_list.currentItem()
        if current_item:
            template_name = current_item.text()
            
            # 从文件加载模板
            template_file = os.path.join(self.template_folder, f"{template_name}.json")
            if os.path.exists(template_file):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    
                    # 应用模板设置
                    if "watermark_text" in template:
                        self.watermark_text = template["watermark_text"]
                        self.text_input.setText(self.watermark_text)
                    
                    if "text_opacity" in template:
                        self.text_opacity = template["text_opacity"]
                        self.opacity_slider.setValue(self.text_opacity)
                        self.opacity_label.setText(f"{self.text_opacity}%")
                    
                    if "output_format" in template:
                        self.output_format = template["output_format"]
                        self.format_combo.setCurrentText(self.output_format)
                    
                    if "file_naming_rule" in template:
                        self.file_naming_rule = template["file_naming_rule"]
                        self.naming_combo.setCurrentIndex({
                            "original": 0, "prefix": 1, "suffix": 2
                        }.get(self.file_naming_rule, 0))
                    
                    if "custom_prefix" in template:
                        self.custom_prefix = template["custom_prefix"]
                        self.prefix_input.setText(self.custom_prefix)
                    
                    if "custom_suffix" in template:
                        self.custom_suffix = template["custom_suffix"]
                        self.suffix_input.setText(self.custom_suffix)
                    
                    # 更新预览
                    self.update_preview()
                    
                    QMessageBox.information(self, "成功", f"已加载模板 '{template_name}'")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"无法加载模板 '{template_name}': {str(e)}")
    
    def delete_template(self):
        current_item = self.template_list.currentItem()
        if current_item:
            template_name = current_item.text()
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除模板 '{template_name}' 吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除文件
                template_file = os.path.join(self.template_folder, f"{template_name}.json")
                if os.path.exists(template_file):
                    try:
                        os.remove(template_file)
                        # 从字典中删除
                        if template_name in self.templates:
                            del self.templates[template_name]
                        # 更新列表
                        self.load_templates()
                        QMessageBox.information(self, "成功", f"模板 '{template_name}' 已删除")
                    except Exception as e:
                        QMessageBox.warning(self, "错误", f"无法删除模板 '{template_name}': {str(e)}")
    
    def load_templates(self):
        # 清空列表
        self.template_list.clear()
        
        # 重新加载模板
        self.templates = {}
        if os.path.exists(self.template_folder):
            for file in os.listdir(self.template_folder):
                if file.endswith(".json"):
                    template_name = os.path.splitext(file)[0]
                    self.template_list.addItem(template_name)
                    
                    # 加载模板内容
                    try:
                        with open(os.path.join(self.template_folder, file), 'r', encoding='utf-8') as f:
                            self.templates[template_name] = json.load(f)
                    except:
                        pass  # 忽略无法加载的模板
    
    def save_settings(self):
        try:
            # 保存当前设置
            settings = {
                "watermark_text": self.watermark_text,
                "text_opacity": self.text_opacity,
                "watermark_position": {
                    "x": self.watermark_position.x(),
                    "y": self.watermark_position.y()
                },
                "output_format": self.output_format,
                "output_folder": self.output_folder,
                "file_naming_rule": self.file_naming_rule,
                "custom_prefix": self.custom_prefix,
                "custom_suffix": self.custom_suffix
            }
            
            settings_file = os.path.join(os.getcwd(), "watermark_settings.json")
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            QMessageBox.information(self, "成功", "设置已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法保存设置: {str(e)}")
    
    def load_settings(self):
        try:
            settings_file = os.path.join(os.getcwd(), "watermark_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 加载设置
                if "watermark_text" in settings:
                    self.watermark_text = settings["watermark_text"]
                
                if "text_opacity" in settings:
                    self.text_opacity = settings["text_opacity"]
                
                if "watermark_position" in settings:
                    pos = settings["watermark_position"]
                    self.watermark_position = QPoint(pos["x"], pos["y"])
                
                if "output_format" in settings:
                    self.output_format = settings["output_format"]
                
                if "output_folder" in settings:
                    self.output_folder = settings["output_folder"]
                
                if "file_naming_rule" in settings:
                    self.file_naming_rule = settings["file_naming_rule"]
                
                if "custom_prefix" in settings:
                    self.custom_prefix = settings["custom_prefix"]
                
                if "custom_suffix" in settings:
                    self.custom_suffix = settings["custom_suffix"]
        except:
            pass  # 忽略无法加载的设置
    
    def show_about(self):
        QMessageBox.about(
            self, "关于水印应用",
            "水印文件本地应用 Windows 版\n\n" +
            "版本: 1.0.0\n" +
            "一个功能完善、用户体验更好的本地图片水印处理应用。\n\n" +
            "支持批量图片处理，实现文本和图片水印的灵活配置与实时预览，\n" +
            "提升用户的水印处理效率和体验。"
        )
    
    def closeEvent(self, event):
        # 在关闭前保存设置
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WatermarkApp()
    window.show()
    sys.exit(app.exec_())