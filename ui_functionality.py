# ui_functionality.py
import os
import sys
import json
import datetime
import subprocess
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QPixmap, QIcon
from ui import MainWindowUI  # UI 구성부
# tree_widget 모듈에서 MyTreeWidget를 import
from tree_widget import MyTreeWidget
from tree_manager import files_dict, display_part_info, apply_tree_view_styles,build_image_dict,build_xml3d_dict,build_fbx_dict

class MainWindow(QMainWindow, MainWindowUI):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # UI 구성부 설정

        # 최초 자동 선택 무시를 위한 플래그 추가
        self.firstDisplay = True

        # 기능 구현부 초기화
        self.current_part_no = None           # 현재 선택된 파트넘버
        self.memo_data = {}                   # { 파트번호: [ { "memo": 내용, "timestamp": 시간 }, ... ] }
        self.json_file_path = None            # JSON 파일 경로 (예: 01_excel/memo.json)
        self.df = None                        # Excel 데이터 (나중에 build_tree_view에서 설정)
        
        # 시그널과 슬롯 연결 (이벤트 핸들러 연결)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.imageLabel.clicked.connect(self.load_image_for_current_part)
        self.radio_image.toggled.connect(self.on_radio_image_clicked)
        self.radio_3dxml.toggled.connect(self.on_radio_3dxml_clicked)
        self.radio_fbx.toggled.connect(self.on_radio_fbx_clicked)
        self.filter_button.toggled.connect(self.on_filter_button_toggled)
        self.memoSaveButton.clicked.connect(self.on_save_memo)
        self.memoClearButton.clicked.connect(self.on_clear_memo)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        self.searchLineEdit.returnPressed.connect(self.searchTree)
        self.tree.currentItemChanged.connect(self.on_current_item_changed)
    
    def on_refresh_clicked(self):
        """
        리프레쉬 버튼 클릭 시 3개의 파일 딕셔너리(이미지, 3DXML, FBX)를 다시 읽어
        현재 선택된 모드에 맞게 트리뷰 스타일을 업데이트하고,
        완료 메시지를 로그창에 출력합니다.
        """
        # 파일 딕셔너리 갱신
        build_image_dict(self)
        build_xml3d_dict(self)
        build_fbx_dict(self)
        
        # 현재 선택된 모드에 따른 스타일 결정
        if self.radio_image.isChecked():
            mode = "image"
        elif self.radio_3dxml.isChecked():
            mode = "3dxml"
        elif self.radio_fbx.isChecked():
            mode = "fbx"
        else:
            mode = "image"
        
        # 트리뷰의 스타일 재적용
        apply_tree_view_styles(self.tree, mode)
        
        # 로그창에 완료 메시지 출력
        self.appendLog("파일 딕셔너리 업데이트 및 스타일 재적용이 완료되었습니다.")

    # ─── 이벤트 핸들러 구현 ─────────────────────────────

    def on_tree_item_clicked(self, item, column):
        part_no = item.text(column).strip().upper()
        self.current_part_no = part_no
        display_part_info(part_no, self)
        self.load_image_for_current_part()
        
        # 출력 박스에 저장된 메모(여러 메모이면 개행 한 번으로 구분) 출력
        if part_no in self.memo_data:
            memo_entries = self.memo_data[part_no]
            if isinstance(memo_entries, list):
                display_text = "\n".join(
                    f"[{entry.get('timestamp','').strip()}] {entry.get('memo','').strip()}"
                    for entry in memo_entries
                )
            elif isinstance(memo_entries, dict):
                display_text = f"[{memo_entries.get('timestamp','').strip()}] {memo_entries.get('memo','').strip()}"
            else:
                display_text = str(memo_entries)
            self.memoOutput.setPlainText(display_text)
        else:
            self.memoOutput.clear()
        
        # 메모 입력창은 입력 전용으로 항상 클리어
        self.memoText.clear()
    
    def on_tree_item_double_clicked(self, item, column):
        part_no = item.text(column).strip().upper()
        # 각 모드에 따른 파일 경로 선택
        if self.radio_image.isChecked():
            if part_no in files_dict["image"]:
                file_path = files_dict["image"][part_no]
            else:
                QMessageBox.warning(self, "죄송합니다.", "해당 파트넘버에 해당하는 이미지가 없습니다.")
                return
        elif self.radio_3dxml.isChecked():
            if part_no in files_dict["xml3d"]:
                file_path = files_dict["xml3d"][part_no]
            else:
                QMessageBox.warning(self, "죄송합니다.", "해당 파트넘버에 해당하는 3DXML 파일이 없습니다.")
                return
        elif self.radio_fbx.isChecked():
            if part_no in files_dict["fbx"]:
                file_path = files_dict["fbx"][part_no]
            else:
                QMessageBox.warning(self, "죄송합니다.", "해당 파트넘버에 해당하는 FBX 파일이 없습니다.")
                return
        else:
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "죄송합니다.", "파일이 존재하지 않습니다.")
            return

        # FILE 체크박스가 체크되어 있으면 파일을 실행하지 않고 탐색기에서 파일 위치를 보여줌.
        if self.checkbox_file.isChecked():
            try:
                # explorer /select, "파일경로" 명령으로 파일이 선택된 상태의 폴더 열기
                cmd = f'explorer /select,"{file_path}"'
                subprocess.run(cmd, shell=True)
            except Exception as e:
                QMessageBox.warning(self, "에러", f"파일 위치 열기 오류: {str(e)}")
        else:
            # 체크박스 미체크 시 기존 동작 (파일 실행)
            if self.radio_image.isChecked():
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                try:
                    cmd = f'cmd /c start "" "{file_path}"'
                    subprocess.run(cmd, shell=True, check=True)
                except Exception as e:
                    QMessageBox.warning(self, "에러", f"파일 실행 오류: {str(e)}")

    
    def load_image_for_current_part(self):
        part_no = self.current_part_no
        if part_no in files_dict["image"]:
            image_path = files_dict["image"][part_no]
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        self.imageLabel.width(),
                        self.imageLabel.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.imageLabel.setPixmap(scaled)
                else:
                    self.imageLabel.clear()
                    self.imageLabel.setText("이미지 로드 실패.")
            else:
                self.imageLabel.clear()
                self.imageLabel.setText("이미지가 없습니다.")
        else:
            self.imageLabel.clear()
            self.imageLabel.setText("이미지가 없습니다.")
    
    def on_filter_button_toggled(self, checked):
        if checked:
            if self.radio_image.isChecked():
                mode = "image"
            elif self.radio_3dxml.isChecked():
                mode = "xml3d"
            elif self.radio_fbx.isChecked():
                mode = "fbx"
            else:
                mode = "image"
            self.filter_tree_items(self.tree, mode)
            
            # 필터 적용 후 보이는 노드의 개수를 계산
            def count_visible_nodes(item):
                count = 0
                if not item.isHidden():
                    count += 1
                for i in range(item.childCount()):
                    count += count_visible_nodes(item.child(i))
                return count

            visible_total = 0
            for i in range(self.tree.topLevelItemCount()):
                visible_total += count_visible_nodes(self.tree.topLevelItem(i))
            self.appendLog(f"{mode} 필터 적용 노드의 갯수: {visible_total}")
        else:
            self.clear_tree_filter(self.tree)

    def filter_tree_items(self, tree_widget, mode):
        for i in range(tree_widget.topLevelItemCount()):
            self._apply_filter(tree_widget.topLevelItem(i))

    def _apply_filter(self, item):
        # 캐싱된 활성 여부를 사용하여 필터 적용
        visible = item.data(0, Qt.UserRole)
        debug_message = f"Filtering Node: {item.text(0).upper()} | cached visible: {visible}"
        item.setHidden(not visible)
        for i in range(item.childCount()):
            self._apply_filter(item.child(i))
    
    def clear_tree_filter(self, tree_widget):
        def clear_item(item):
            item.setHidden(False)
            for i in range(item.childCount()):
                clear_item(item.child(i))
        for i in range(tree_widget.topLevelItemCount()):
            clear_item(tree_widget.topLevelItem(i))
    
    def on_radio_image_clicked(self, checked):
        if checked:
            apply_tree_view_styles(self.tree, "image")
            if self.filter_button.isChecked():
                self.reset_filter_button()
    
    def on_radio_3dxml_clicked(self, checked):
        if checked:
            apply_tree_view_styles(self.tree, "3dxml")
            if self.filter_button.isChecked():
                self.reset_filter_button()
    
    def on_radio_fbx_clicked(self, checked):
        if checked:
            apply_tree_view_styles(self.tree, "fbx")
            if self.filter_button.isChecked():
                self.reset_filter_button()
    
    def reset_filter_button(self):
        if self.filter_button.isChecked():
            self.filter_button.setChecked(False)

    def appendLog(self, message):
        self.logText.append("Log event: " + message)

    def on_save_memo(self):
        if not self.current_part_no:
            QMessageBox.warning(self, "경고", "먼저 파트를 선택하세요.")
            return
        memo_content = self.memoText.toPlainText().strip()
        if not memo_content:
            QMessageBox.information(self, "알림", "메모를 입력하세요.")
            return
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {"memo": memo_content, "timestamp": timestamp}
        if self.current_part_no in self.memo_data:
            if not isinstance(self.memo_data[self.current_part_no], list):
                self.memo_data[self.current_part_no] = [self.memo_data[self.current_part_no]]
            self.memo_data[self.current_part_no].append(new_entry)
        else:
            self.memo_data[self.current_part_no] = [new_entry]
        self.save_memo_data()
        self.appendLog(f"[{timestamp}] Saved Memo for {self.current_part_no}: {memo_content}")
        self.memoText.clear()
        memo_entries = self.memo_data[self.current_part_no]
        display_text = "\n".join(
            f"[{entry.get('timestamp','').strip()}] {entry.get('memo','').strip()}"
            for entry in memo_entries
        )
        self.memoOutput.setPlainText(display_text)
    
    def on_clear_memo(self):
        if not self.current_part_no:
            QMessageBox.warning(self, "경고", "먼저 파트를 선택하세요.")
            return
        confirm = QMessageBox.question(
            self, "메모 삭제", f"'{self.current_part_no}'의 메모를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return
        self.memoText.clear()
        self.memoOutput.clear()
        if self.current_part_no in self.memo_data:
            del self.memo_data[self.current_part_no]
            self.save_memo_data()
        self.appendLog(f"Cleared Memo - Node: {self.current_part_no}")

    def load_memo_data(self):
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
            self.memo_data = {}
        else:
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        self.memo_data = {}
                    else:
                        self.memo_data = json.loads(content)
            except json.JSONDecodeError:
                self.memo_data = {}
    
    def save_memo_data(self):
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.memo_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "에러", f"JSON 파일 저장 중 오류: {str(e)}")

    def searchTree(self):
        """검색 텍스트박스에 입력한 파트넘버를 트리에서 찾아 선택하고 스크롤합니다."""
        search_text = self.searchLineEdit.text().strip().upper()
        if not search_text:
            return
        # MyTreeWidget에 구현된 find_item() 메서드를 사용
        found_item = self.tree.find_item(search_text)
        if found_item:
            self.tree.setCurrentItem(found_item)
            self.tree.scrollToItem(found_item)
            self.appendLog(f"Found node: {search_text}")
        else:
            self.appendLog(f"Node not found: {search_text}")
            QMessageBox.warning(
                self, "죄송합니다.",
                f"'{search_text}'에 해당하는 노드를 찾을 수 없습니다.",
                QMessageBox.Ok
            )

    def on_current_item_changed(self, current, previous):
        if self.firstDisplay:
            self.firstDisplay = False  # 최초 한 번만 무시
        else:
            if current:
                self.on_tree_item_clicked(current, 0)