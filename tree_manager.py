#tree_manager.py

import os
import sys
import time
import pandas as pd
from PyQt5.QtWidgets import QTreeWidgetItem, QMessageBox, QHeaderView
from PyQt5.QtGui import QPixmap, QBrush, QColor
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# ─────────────────────────────────────────────────────────────
# 전역 변수들
# ─────────────────────────────────────────────────────────────
nodeCount = 0
g_NodeDictionary = {}  # 파트넘버 -> 트리 아이템

# 파일 관련 딕셔너리를 중첩 구조로 관리
files_dict = {
    "image": {},   # 파트넘버 -> 이미지 파일 경로
    "xml3d": {},   # 파트넘버 -> 3DXML 파일 경로
    "fbx": {}      # 파트넘버 -> FBX 파일 경로
}

def get_base_path():
    """실행 파일(또는 스크립트)이 있는 폴더를 반환"""
    if getattr(sys, 'frozen', False):  # PyInstaller로 빌드된 경우
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

def build_xml3d_dict(window):
    """
    02_3dxml 폴더에서 .3dxml 파일을 스캔하여,
    파일명 예: aaa_bbb_ccc_PARTNO.3dxml 의 형식이라고 가정하고,
    PARTNO를 추출하여 files_dict["xml3d"][PARTNO] = 파일 경로 로 저장.
    디버깅을 위해 전체 파일 처리 결과를 로그에 출력함.
    """
    files_dict["xml3d"].clear()  # 기존 데이터 초기화
    base_path = get_base_path()  
    folder_path = os.path.join(base_path, "02_3dxml")
    
    if not os.path.exists(folder_path):
        window.appendLog(f"[build_xml3d_dict] 02_3dxml 폴더를 찾을 수 없습니다: {folder_path}")
        return
    
    all_files = os.listdir(folder_path)
    window.appendLog(f"[build_xml3d_dict] 전체 파일 수: {len(all_files)}")
    
    # 폴더 내 3DXML 파일 수
    window.xml3d_folder_count = len([fname for fname in all_files if fname.lower().endswith(".3dxml")])
    
    invalid_files = []   # 파일명 형식 오류
    duplicates = {}      # {PARTNO: [중복된 파일명, ...]}
    processed_files = 0  # 실제로 딕셔너리에 추가된 파일 수
    
    for fname in all_files:
        lower_name = fname.lower()
        if lower_name.endswith(".3dxml"):
            file_parts = fname.split("_")
            if len(file_parts) < 4:
                invalid_files.append(fname)
                window.appendLog(f"[build_xml3d_dict] 파일명 형식 오류(언더스코어 분리 부족): {fname}")
                continue
            
            # 네 번째 요소에서 확장자 제거 후 대문자 변환하여 PARTNO 추출
            part_number = os.path.splitext(file_parts[3])[0].upper()
            if part_number in files_dict["xml3d"]:
                # 중복 발생 시, duplicates 딕셔너리에 추가
                if part_number in duplicates:
                    duplicates[part_number].append(fname)
                else:
                    duplicates[part_number] = [fname]
                continue
            
            files_dict["xml3d"][part_number] = os.path.join(folder_path, fname)
            processed_files += 1
    
    # 중복 로그: 각 파트넘버에 대해 최초 파일과 중복 파일을 모두 보여줌
    if duplicates:
        duplicate_log_lines = []
        duplicate_log_lines.append("[build_xml3d_dict] 중복된 PARTNO 로그:")
        for part_number, dup_file_list in duplicates.items():
            original_file = os.path.basename(files_dict["xml3d"][part_number])
            duplicate_log_lines.append(f"[{part_number}]")
            duplicate_log_lines.append(f"-> {original_file}")
            for dup in dup_file_list:
                duplicate_log_lines.append(f"-> {dup}")
        duplicate_log_message = "\n".join(duplicate_log_lines)
        window.appendLog(duplicate_log_message)
    
    window.appendLog(f"[build_xml3d_dict] 유효한 3DXML 파일 처리 수: {processed_files}")
    window.appendLog(f"총 {len(files_dict['xml3d'])}개의 3DXML 파일이 추가되었습니다.")
    
    window.xml3d_duplicate_count = sum(len(v) for v in duplicates.values())
    window.xml3d_registered_count = len(files_dict["xml3d"])
    
    if invalid_files:
        window.appendLog(f"[build_xml3d_dict] 올바르지 않은 형식의 파일: {invalid_files}")
        
def build_image_dict(window):
    """
    00_image 폴더에서 PNG/JPG 파일을 스캔하여,
    파일명 예: aaa_bbb_ccc_PARTNO.png 의 형식이라고 가정하고,
    PARTNO를 추출하여 files_dict["image"][PARTNO] = 파일 경로 로 저장.
    디버깅을 위해 전체 파일 처리 결과를 로그에 출력함.
    """
    files_dict["image"].clear()
    base_path = get_base_path()
    folder_path = os.path.join(base_path, "00_image")
    
    if not os.path.exists(folder_path):
        window.appendLog(f"[build_image_dict] 00_image 폴더를 찾을 수 없습니다: {folder_path}")
        return
    
    all_files = os.listdir(folder_path)
    window.appendLog(f"[build_image_dict] 전체 파일 수: {len(all_files)}")
    
    # 폴더 내 이미지 파일 수 (확장자 기준 필터)
    window.image_folder_count = len([fname for fname in all_files if fname.lower().endswith((".png", ".jpg"))])
    
    invalid_files = []   # 파일명 형식 오류
    duplicates = {}      # {PARTNO: [중복된 파일명, ...]}
    processed_files = 0  # 실제로 딕셔너리에 추가된 파일 수
    
    for fname in all_files:
        lower_name = fname.lower()
        if lower_name.endswith(".png") or lower_name.endswith(".jpg"):
            file_parts = fname.split("_")
            if len(file_parts) < 4:
                invalid_files.append(fname)
                window.appendLog(f"[build_image_dict] 파일명 형식 오류(언더스코어 분리 부족): {fname}")
                continue
            
            # 네 번째 요소에서 확장자 제거 후 대문자 변환하여 PARTNO 추출
            part_number = os.path.splitext(file_parts[3])[0].upper()
            if part_number in files_dict["image"]:
                # 중복 발생 시, duplicates 딕셔너리에 추가
                if part_number in duplicates:
                    duplicates[part_number].append(fname)
                else:
                    duplicates[part_number] = [fname]
                continue
            
            files_dict["image"][part_number] = os.path.join(folder_path, fname)
            processed_files += 1

    # 중복 로그: 각 파트넘버에 대해 최초 파일과 중복 파일을 모두 보여줌
    if duplicates:
        duplicate_log_lines = []
        duplicate_log_lines.append("[build_image_dict] 중복된 PARTNO 로그:")
        for part_number, dup_file_list in duplicates.items():
            original_file = os.path.basename(files_dict["image"][part_number])
            duplicate_log_lines.append(f"[{part_number}]")
            duplicate_log_lines.append(f"-> {original_file}")
            for dup in dup_file_list:
                duplicate_log_lines.append(f"-> {dup}")
        duplicate_log_message = "\n".join(duplicate_log_lines)
        window.appendLog(duplicate_log_message)
    
    window.appendLog(f"[build_image_dict] 유효한 이미지 파일 처리 수: {processed_files}")
    window.appendLog(f"총 {len(files_dict['image'])}개의 이미지 파일이 추가되었습니다.")
    
    window.image_duplicate_count = sum(len(v) for v in duplicates.values())
    window.image_registered_count = len(files_dict["image"])
    
    if invalid_files:
        window.appendLog(f"[build_image_dict] 올바르지 않은 형식의 파일: {invalid_files}")

def build_fbx_dict(window):
    """
    03_fbx 폴더에서 .fbx 파일을 스캔하여,
    파일명 예: aaa_bbb_ccc_PARTNO.fbx 의 형식이라고 가정하고,
    PARTNO를 추출하여 files_dict["fbx"][PARTNO] = 파일 경로 로 저장.
    """
    files_dict["fbx"].clear()
    base_path = get_base_path()
    folder_path = os.path.join(base_path, "03_fbx")
    
    if not os.path.exists(folder_path):
        window.appendLog(f"[build_fbx_dict] 03_fbx 폴더를 찾을 수 없습니다: {folder_path}")
        return
    
    all_files = os.listdir(folder_path)
    # 폴더 내 FBX 파일 수 (확장자 기준)
    window.fbx_folder_count = len([fname for fname in all_files if fname.lower().endswith(".fbx")])
    # 중복은 고려하지 않음
    window.fbx_duplicate_count = 0
    
    for fname in all_files:
        lower_name = fname.lower()
        if lower_name.endswith(".fbx"):
            file_parts = fname.split("_")
            if len(file_parts) >= 4:
                part_number = os.path.splitext(file_parts[3])[0].upper()
                if part_number not in files_dict["fbx"]:
                    files_dict["fbx"][part_number] = os.path.join(folder_path, fname)
    window.appendLog(f"총 {len(files_dict['fbx'])}개의 FBX 파일이 추가되었습니다.")
    window.fbx_registered_count = len(files_dict["fbx"])

def safe_int(value, default="nan"):
    """
    안전하게 int 변환.
    NaN, None, 빈 문자열은 기본값(default)으로 변환
    """
    try:
        if pd.isna(value) or value is None or value == "":
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def display_part_info(part_no, window):
    """
    엑셀의 메타데이터를 로그창(window.logText)에 출력
    """
    try:
        df = window.df
        if df is None or df.empty:
            window.appendLog("엑셀 데이터가 로드되지 않았습니다.")
            return
        
        if "Part No" not in df.columns:
            raise KeyError("컬럼 'Part No'가 엑셀 데이터에 없습니다. 컬럼명을 확인하세요.")
        
        row = df[df["Part No"].str.strip() == part_no]
        if row.empty:
            window.appendLog(f"해당하는 '{part_no}' 값을 찾을 수 없습니다.")
            return
        
        row = row.iloc[0]
        metadataStr = (
            f"S/N: {row.get('S/N', 'N/A')}\n"
            f"Level: {safe_int(row.get('Level', 'N/A'))}\n"
            f"Type: {row.get('Type', 'N/A')}\n"
            f"Part No: {row.get('Part No', 'N/A')}\n"
            f"Part Rev: {row.get('Part Rev', 'N/A')}\n"
            f"Part Status: {row.get('Part Status', 'N/A')}\n"
            f"Latest: {row.get('Latest', 'N/A')}\n"
            f"Nomenclature: {row.get('Nomenclature', 'N/A')}\n"
            f"Instance ID 총수량(ALL DB): {safe_int(row.get('Instance ID 총수량(ALL DB)', 'N/A'))}\n"
            f"Qty: {safe_int(row.get('Qty', 'N/A'))}\n"
            f"NextPart: {row.get('NextPart', 'N/A')}"
        )
        # 줄바꿈(\n)을 <br>로 변환
        formatted_metadata = metadataStr.replace('\n', '<br>')
        formatted_html = f"<b>{formatted_metadata}</b>"
        window.logText.clear()
        window.logText.setHtml(formatted_html)
    except Exception as e:
        window.appendLog("에러 발생: " + str(e))

def add_nodes_original(tree_widget, parent_item, dict_rel, node_keys):
    """
    엑셀 데이터 기반 트리뷰 구성용 재귀 함수
    """
    global nodeCount, g_NodeDictionary
    parent_key = parent_item.text(0)
    if parent_key not in dict_rel:
        return
    for child_key in dict_rel[parent_key]:
        new_key = child_key
        is_duplicate = False
        if child_key in node_keys:
            dup_counter = 1
            while new_key in node_keys:
                new_key = f"{child_key}dup{dup_counter}"
                dup_counter += 1
            is_duplicate = True
        node_keys[new_key] = True
        
        child_item = QTreeWidgetItem(parent_item)
        child_item.setText(0, child_key)
        g_NodeDictionary[child_key] = child_item
        
        global nodeCount
        nodeCount += 1
        if not is_duplicate:
            add_nodes_original(tree_widget, child_item, dict_rel, node_keys)

def apply_tree_view_styles(tree_widget, style):
    # mode에 따른 파일 딕셔너리 및 브러시 설정 (기존과 동일)
    if style == "image":
        active_brush = QBrush(QColor(255, 0, 0))  # 빨간색
        file_dict_local = files_dict["image"]
    elif style == "3dxml":
        active_brush = QBrush(QColor(0, 0, 255))  # 파란색
        file_dict_local = files_dict["xml3d"]
    elif style == "fbx":
        active_brush = QBrush(QColor(0, 128, 0))  # 녹색
        file_dict_local = files_dict["fbx"]
    else:
        active_brush = QBrush(QColor(0, 0, 0))
        file_dict_local = {}
    default_brush = QBrush(QColor(0, 0, 0))

    def recurse(item):
        part_no = item.text(0)
        part_no_upper = part_no.upper()
        # 현재 노드의 활성 여부 (파일 딕셔너리에 존재하는지)
        visible_self = part_no_upper in file_dict_local

        # 자식 노드들을 재귀적으로 처리하여 활성 여부 계산
        visible_child = False
        for i in range(item.childCount()):
            if recurse(item.child(i)):
                visible_child = True

        # 최종 활성 여부: 현재 노드나 자식 중 하나라도 활성이면 True
        visible = visible_self or visible_child
        # 캐싱: 계산한 활성 여부를 노드의 사용자 데이터(Qt.UserRole)에 저장
        item.setData(0, Qt.UserRole, visible)

        # 스타일 적용: 파일 목록에 직접 존재하는 경우(active)
        font = item.font(0)
        font.setBold(False)
        item.setFont(0, font)
        item.setForeground(0, default_brush)
        if visible_self:
            font.setBold(True)
            item.setFont(0, font)
            item.setForeground(0, active_brush)
        return visible

    for i in range(tree_widget.topLevelItemCount()):
        recurse(tree_widget.topLevelItem(i))
    
    tree_widget.repaint()

def build_tree_view(excel_path, window):
    """
    엑셀 데이터를 읽어 트리뷰를 구성하는 함수
    """
    global nodeCount, g_NodeDictionary
    start_time = time.time()
    
    # 이미지, 3DXML, FBX 파일 정보 딕셔너리 갱신
    build_image_dict(window)
    build_xml3d_dict(window)
    build_fbx_dict(window)
    
    df = pd.read_excel(excel_path, sheet_name="Sheet1")
    if "PartNo" in df.columns and "NextPart" in df.columns:
        part_nos = df["PartNo"].astype(str).str.strip()
        next_parts = df["NextPart"].astype(str).str.strip()
    else:
        part_nos = df.iloc[:, 3].astype(str).str.strip()
        next_parts = df.iloc[:, 13].astype(str).str.strip()
    
    window.df = df  # 엑셀 데이터를 MainWindow에 저장
    
    total_parts = 0
    nodeCount = 0
    dict_rel = {}
    g_NodeDictionary = {}
    
    final_roots = set()
    for i in range(len(df)):
        part_no = part_nos.iloc[i]
        next_part = next_parts.iloc[i]
        if part_no != "":
            total_parts += 1
            if next_part == "" or next_part.lower() == "nan":
                final_roots.add(part_no)
            else:
                if next_part not in dict_rel:
                    dict_rel[next_part] = []
                dict_rel[next_part].append(part_no)
    
    if len(final_roots) == 0:
        window.appendLog("[build_tree_view] 최종 루트(final root)가 없습니다.")
        return
    root_key = list(final_roots)[0]
    
    window.tree.clear()
    
    # 헤더 마지막 컬럼 자동 확장 해제
    header = window.tree.header()
    header.setStretchLastSection(False)
    header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    
    # 가로 스크롤바 필요시 표시
    window.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    
    g_NodeDictionary = {}
    
    root_item = QTreeWidgetItem(window.tree)
    root_item.setText(0, root_key)
    nodeCount += 1
    node_keys = {root_key: True}
    g_NodeDictionary[root_key] = root_item
    root_item.setExpanded(True)
    
    add_nodes_original(window.tree, root_item, dict_rel, node_keys)
    # 기본 스타일 적용 (초기에는 image 스타일 적용)
    apply_tree_view_styles(window.tree, "image")
    
    # 최종 요약정보 작성
    summary_log = "===== Operation Summary =====\n"
    summary_log += f"Log event: Image - 폴더 내 파일: {window.image_folder_count}, 중복 파일: {window.image_duplicate_count}, 등록된 파일: {window.image_registered_count}\n"
    summary_log += f"Log event: 3DXML - 폴더 내 파일: {window.xml3d_folder_count}, 중복 파일: {window.xml3d_duplicate_count}, 등록된 파일: {window.xml3d_registered_count}\n"
    summary_log += f"Log event: FBX - 폴더 내 파일: {window.fbx_folder_count}, 중복 파일: {window.fbx_duplicate_count}, 등록된 파일: {window.fbx_registered_count}\n"
    summary_log += f"Log event: 총 유효 파트 수: {total_parts}\n"
    summary_log += f"Log event: 트리뷰에 추가된 전체 노드 수: {nodeCount}\n"
    window.appendLog(summary_log)
    
    elapsed_time = time.time() - start_time
    window.appendLog(f"트리뷰 생성시간: {elapsed_time:.2f} seconds")
