import os
import sys
from PyQt5.QtWidgets import QTreeWidget, QMessageBox
from PyQt5.QtCore import Qt, QUrl, QMimeData  # QMimeData를 여기서 가져옵니다.
from PyQt5.QtGui import QDrag

# files_dict 등 필요한 항목을 tree_manager에서 import
from tree_manager import files_dict

class MyTreeWidget(QTreeWidget):
    """
    드래그 앤 드롭, 더블 클릭, 노드 검색 기능을 포함한 QTreeWidget 하위 클래스
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def mouseDoubleClickEvent(self, event):
        """더블 클릭 시 기본 노드 확장/축소 기능을 막고 사용자 정의 이벤트만 실행"""
        item = self.itemAt(event.pos())
        if item:
            main_window = self.window()
            if hasattr(main_window, "on_tree_item_double_clicked"):
                main_window.on_tree_item_double_clicked(item, 0)
        event.ignore()  # 기본 동작(노드 확장/축소) 방지

    def keyPressEvent(self, event):
        """엔터 키를 누르면 현재 선택된 노드에 대해 더블 클릭 이벤트 실행"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.currentItem()
            if item:
                main_window = self.window()
                if hasattr(main_window, "on_tree_item_double_clicked"):
                    main_window.on_tree_item_double_clicked(item, 0)
            event.accept()
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            main_window = self.window()
            not_found_files = []  # 찾지 못한 파일 리스트

            for url in event.mimeData().urls():
                file_name_no_ext = os.path.splitext(
                    os.path.basename(url.toLocalFile())
                )[0]
                parts = file_name_no_ext.split("_")
                part_number = parts[3] if len(parts) >= 4 else file_name_no_ext
                item = self.find_item(part_number)

                if item:
                    self.setCurrentItem(item)
                    item.setExpanded(True)
                    if hasattr(main_window, "on_tree_item_clicked"):
                        main_window.on_tree_item_clicked(item, 0)
                else:
                    not_found_files.append(file_name_no_ext)  # 찾지 못한 파일 저장

            # 찾지 못한 파일이 있을 경우 경고 메시지 표시
            if not_found_files:
                QMessageBox.warning(
                    self, "파일 노드 없음",
                    "다음 파일과 일치하는 노드를 찾을 수 없습니다:\n\n" + "\n".join(not_found_files),
                    QMessageBox.Ok
                )

            event.acceptProposedAction()
        else:
            event.ignore()

    def find_item(self, text):
        """
        재귀적으로 트리 내에서 주어진 텍스트와 일치하는 노드를 검색
        """
        def recursive_search(item):
            if item.text(0) == text:
                return item
            for i in range(item.childCount()):
                found = recursive_search(item.child(i))
                if found:
                    return found
            return None

        for i in range(self.topLevelItemCount()):
            found = recursive_search(self.topLevelItem(i))
            if found:
                return found
        return None

    def startDrag(self, supportedActions):
        """
        노드를 드래그할 때, 노드 텍스트(파트넘버)를 기반으로 현재 모드에 맞는 파일 경로를 files_dict에서 찾아
        외부(예: Windows Explorer)로 파일처럼 드래그 앤 드롭할 수 있도록 MIME 데이터를 생성합니다.
        """
        item = self.currentItem()
        if not item:
            return

        part_no = item.text(0).strip().upper()
        main_window = self.window()

        file_path = None
        # MainWindow의 라디오 버튼 상태에 따라 파일 경로를 선택 (ui_functionality.py의 on_tree_item_double_clicked 참고)
        if hasattr(main_window, "radio_image") and main_window.radio_image.isChecked():
            if part_no in files_dict.get("image", {}):
                file_path = files_dict["image"][part_no]
        elif hasattr(main_window, "radio_3dxml") and main_window.radio_3dxml.isChecked():
            if part_no in files_dict.get("xml3d", {}):
                file_path = files_dict["xml3d"][part_no]
        elif hasattr(main_window, "radio_fbx") and main_window.radio_fbx.isChecked():
            if part_no in files_dict.get("fbx", {}):
                file_path = files_dict["fbx"][part_no]

        if not file_path or not os.path.exists(file_path):
            # 파일 경로가 없거나 유효하지 않으면 드래그 동작 중단
            return

        mimeData = QMimeData()
        url = QUrl.fromLocalFile(file_path)
        mimeData.setUrls([url])

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        # 필요에 따라 drag.setPixmap() 등으로 시각적 효과를 추가할 수 있습니다.
        drag.exec_(supportedActions)
