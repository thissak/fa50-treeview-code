# ui.py
from PyQt5.QtWidgets import (
    QMainWindow, QTreeWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QRadioButton, QGroupBox, QPushButton, QSpacerItem, QSizePolicy, QCheckBox,
    QLineEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics
from tree_widget import MyTreeWidget

# 클릭 가능한 QLabel
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

# UI 구성만 담당하는 클래스
class MainWindowUI:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 1600)
        
        # ─── 공통 스타일 ───────────────────────────────────────
        self.qgroupbox_style = (
            "QGroupBox { background-color: #f0f0f0; border: 1px solid gray; margin-top: 10px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; font-weight: bold; }"
        )
        self.button_style = (
            "QPushButton { background-color: lightgray; border: 2px solid gray; border-radius: 5px; padding: 8px; font-size: 20px; }"
            "QPushButton:checked, QPushButton:pressed { background-color: yellow; border: 2px solid orange; }"
        )
        
        # ─── 좌측: 트리뷰 (로그창은 제거) ──────────────────────────────
        self.tree = MyTreeWidget(self)
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["FA-50M FINAL ASSEMBLY VERSION POLAND"])
        
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.tree)
        leftWidget = QWidget()
        leftWidget.setLayout(leftLayout)
        
        # ─── 하단: 로그창 (전체 하단 가로폭 사용) ──────────────────────────────
        self.logText = QTextEdit(MainWindow)
        self.logText.setReadOnly(True)
        self.logText.setFixedHeight(300)
        
        # ─── 우측 상단: 이미지 패널 및 기타 구성요소 ──────────────────────────────
        self.imageLabel = ClickableLabel("이미지가 여기에 표시됩니다.", MainWindow)
        self.imageLabel.setAlignment(Qt.AlignHCenter | Qt.AlignCenter)
        self.imageLabel.setStyleSheet("border: 1px solid gray;")
        self.imageLabel.setFixedSize(400, 400)
        
        # 라디오 버튼 그룹
        self.radio_image = QRadioButton("Image", MainWindow)
        self.radio_3dxml = QRadioButton("3DXML", MainWindow)
        self.radio_fbx = QRadioButton("FBX", MainWindow)
        self.radio_image.setChecked(True)

        # Refresh 버튼 추가
        self.refresh_button = QPushButton("R", MainWindow)
        self.refresh_button.setMinimumSize(40, 40)
        self.refresh_button.setStyleSheet(self.button_style)

        self.filter_button = QPushButton("Filter", MainWindow)
        self.filter_button.setCheckable(True)
        self.filter_button.setMinimumSize(130, 40)
        self.filter_button.setStyleSheet(self.button_style)

        # 라디오 버튼 가로 레이아웃
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_image)
        radio_layout.addWidget(self.radio_3dxml)
        radio_layout.addWidget(self.radio_fbx)
        radio_layout.setSpacing(35)
        radio_layout.setAlignment(Qt.AlignCenter)

        # FILE 체크박스 생성
        self.checkbox_file = QCheckBox("Show in Explorer", MainWindow)
        self.checkbox_file.setChecked(False)
        font = self.checkbox_file.font()
        bold_font = QFont(font)
        bold_font.setBold(True)
        fm = QFontMetrics(bold_font)
        self.checkbox_file.setFixedWidth(fm.horizontalAdvance(self.checkbox_file.text()) + 30)
        self.checkbox_file.toggled.connect(
            lambda checked: self.checkbox_file.setStyleSheet("font-weight: bold;" if checked else "font-weight: normal;")
        )

        # Filter 버튼과 FILE 체크박스를 같은 행에 배치
        filter_layout = QHBoxLayout()
        filter_layout.addStretch()
        filter_layout.addWidget(self.refresh_button)
        filter_layout.addWidget(self.filter_button)
        filter_layout.addSpacing(10)
        filter_layout.addWidget(self.checkbox_file)
        filter_layout.addStretch()

        # 상단 라디오 버튼과 하단 Filter+FILE 레이아웃을 수직으로 배치
        radio_main_layout = QVBoxLayout()
        radio_main_layout.addLayout(radio_layout)
        radio_main_layout.addLayout(filter_layout)

        self.radio_group = QGroupBox("Select mode", MainWindow)
        self.radio_group.setStyleSheet(self.qgroupbox_style)
        self.radio_group.setFixedHeight(180)
        self.radio_group.setLayout(radio_main_layout)

        # ─── 메모 그룹 ─────────────────────────────────────────
        self.memo_group = QGroupBox("Memo", MainWindow)
        self.memo_group.setStyleSheet(self.qgroupbox_style)
        memo_layout = QVBoxLayout()
        
        self.memoOutput = QTextEdit(MainWindow)
        self.memoOutput.setReadOnly(True)
        self.memoOutput.setFixedHeight(150)
        self.memoOutput.setStyleSheet("QTextEdit { background-color: #e0e0e0; }")
        
        self.memoText = QTextEdit(MainWindow)
        self.memoText.setFixedHeight(150)
        self.memoText.setStyleSheet("QTextEdit { text-align: left; }")
        
        button_layout = QHBoxLayout()
        self.memoSaveButton = QPushButton("Save Memo", MainWindow)
        self.memoSaveButton.setStyleSheet(self.button_style)
        self.memoClearButton = QPushButton("Clear Memo", MainWindow)
        self.memoClearButton.setStyleSheet(self.button_style)
        button_layout.addWidget(self.memoSaveButton)
        button_layout.addWidget(self.memoClearButton)
        
        memo_layout.addWidget(self.memoOutput)
        memo_layout.addWidget(self.memoText)
        memo_layout.addLayout(button_layout)
        self.memo_group.setLayout(memo_layout)
        self.memo_group.setFixedHeight(480)
        
        # ─── Search 항목: 파트넘버 검색 텍스트박스 ─────────────
        self.searchLineEdit = QLineEdit(MainWindow)
        self.searchLineEdit.setPlaceholderText("Enter Part No and press Enter")
        self.searchLineEdit.setMinimumSize(130, 40)
        self.search_group = QGroupBox("Search", MainWindow)
        self.search_group.setStyleSheet(self.qgroupbox_style)
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.searchLineEdit)
        self.search_group.setLayout(search_layout)

        # 우측 전체 레이아웃 (SpacerItem 제거)
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.imageLabel)
        rightLayout.addWidget(self.radio_group)
        rightLayout.addWidget(self.memo_group)
        rightLayout.setSpacing(25)
        rightLayout.addWidget(self.search_group)
        rightWidget = QWidget()
        rightWidget.setLayout(rightLayout)
        
        # ─── 상단 영역: 좌측(트리뷰) + 우측(이미지/메모 등) ─────────────────────────────
        topLayout = QHBoxLayout()
        topLayout.addWidget(leftWidget, 4)
        topLayout.addWidget(rightWidget, 3)
        
        # ─── 메인 레이아웃: 상단 영역 + 하단 로그창 (전체 가로폭 사용) ─────────────────────────────
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.logText)
        
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        MainWindow.setCentralWidget(centralWidget)
