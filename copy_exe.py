import os
import shutil

def copy_and_rename_exe():
    # 현재 작업 디렉터리: D:\KAI\Treeview\KAI\fa50-treeview-code
    current_dir = os.getcwd()
    source_file = os.path.join(current_dir, "dist", "main.exe")
    
    # 대상 폴더: D:\KAI\Treeview\KAI\fa50-treeview-data (fa50-treeview-code의 부모의 하위 폴더)
    destination_dir = os.path.abspath(os.path.join(current_dir, "..", "fa50-treeview-data"))
    if not os.path.isdir(destination_dir):
        print(f"대상 폴더가 존재하지 않습니다: {destination_dir}")
        return
    
    destination_file = os.path.join(destination_dir, "fa50m-treeviewer.exe")
    
    if not os.path.exists(source_file):
        print(f"복사할 파일이 존재하지 않습니다: {source_file}")
        return
    
    # 대상 파일이 이미 존재하면 삭제
    if os.path.exists(destination_file):
        os.remove(destination_file)
    
    shutil.copy(source_file, destination_file)
    print(f"'{source_file}' 파일이 '{destination_file}'로 복사되었습니다.")

if __name__ == "__main__":
    copy_and_rename_exe()
