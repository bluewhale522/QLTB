import os
import base64
import json
import sqlite3
import threading
import urllib.request
import urllib.error
from datetime import datetime

DEFAULT_OWNER = 'bluewhale522'
DEFAULT_REPO = 'QLTB'
DEFAULT_BRANCH = 'main'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'school_equipment.db')

def get_setting(conn, key, default=None):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default
    except Exception:
        return default

def set_setting(conn, key, value):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_settings (key, value, updated_at) 
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, str(value)))
        conn.commit()
    except Exception as e:
        print(f"[SETTING_ERROR] {e}")

def get_github_status(conn):
    owner = os.environ.get('GITHUB_OWNER') or get_setting(conn, 'github_owner', DEFAULT_OWNER)
    repo = os.environ.get('GITHUB_REPO') or get_setting(conn, 'github_repo', DEFAULT_REPO)
    branch = os.environ.get('GITHUB_BRANCH') or get_setting(conn, 'github_branch', DEFAULT_BRANCH)
    
    token = os.environ.get('GITHUB_TOKEN') or get_setting(conn, 'github_token', '')
    saved_auto = get_setting(conn, 'github_auto_sync')
    if saved_auto is not None:
        auto_sync = (saved_auto == '1')
    else:
        auto_sync = bool(token)
    last_sync = get_setting(conn, 'github_last_sync', '')
    last_sha = get_setting(conn, 'github_last_sha', '')
    
    # Che giấu một phần token khi trả về client để bảo mật
    masked_token = ''
    if token:
        masked_token = token[:4] + '...' + token[-4:] if len(token) > 8 else '****'

    return {
        'owner': owner,
        'repo': repo,
        'branch': branch,
        'has_token': bool(token),
        'masked_token': masked_token,
        'is_env_token': bool(os.environ.get('GITHUB_TOKEN')),
        'auto_sync': auto_sync,
        'last_sync': last_sync,
        'last_sha': last_sha,
        'repo_url': f"https://github.com/{owner}/{repo}"
    }

def save_github_config(conn, token=None, auto_sync=None, owner=None, repo=None, branch=None):
    if token is not None:
        set_setting(conn, 'github_token', token.strip())
    if auto_sync is not None:
        set_setting(conn, 'github_auto_sync', '1' if auto_sync else '0')
    if owner is not None and owner.strip():
        set_setting(conn, 'github_owner', owner.strip())
    if repo is not None and repo.strip():
        set_setting(conn, 'github_repo', repo.strip())
    if branch is not None and branch.strip():
        set_setting(conn, 'github_branch', branch.strip())
    return True

def make_github_request(url, method='GET', data=None, token=None):
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'QLTB-App/2.0',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    body = None
    if data is not None:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(data).encode('utf-8')
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            content = resp.read().decode('utf-8')
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8', errors='ignore')
        try:
            err_json = json.loads(err_msg)
            api_msg = err_json.get('message', err_msg)
        except Exception:
            api_msg = err_msg
        
        if e.code == 401:
            raise Exception("GitHub Token không hợp lệ hoặc đã hết hạn! Vui lòng kiểm tra lại Personal Access Token.")
        elif e.code == 403:
            raise Exception(f"Token không có quyền ghi vào repository (cần quyền 'repo' hoặc 'Contents: Read and write'): {api_msg}")
        elif e.code == 404:
            raise Exception(f"Không tìm thấy repository hoặc nhánh trên GitHub: {api_msg}")
        elif e.code == 409:
            raise Exception("Xung đột nhánh (Branch Conflict). Vui lòng thử đồng bộ lại sau vài giây.")
        else:
            raise Exception(f"Lỗi GitHub API ({e.code}): {api_msg}")
    except urllib.error.URLError as e:
        raise Exception(f"Không thể kết nối đến GitHub: {e.reason}")

def export_db_json(conn):
    """Xuất toàn bộ các bảng CSDL ra dict JSON"""
    cursor = conn.cursor()
    tables = ['users', 'locations', 'categories', 'devices', 'device_movements', 'borrow_requests', 'activity_logs', 'accounts']
    backup_data = {
        'meta': {
            'system': 'He thong Quan ly Thiet bi Truong hoc (QLTB)',
            'export_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': '2.0-pro'
        }
    }
    for t in tables:
        try:
            cursor.execute(f"SELECT * FROM {t}")
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            backup_data[t] = rows
        except Exception:
            backup_data[t] = []
    return backup_data

def sync_database_to_github(conn, commit_message=None):
    """
    Thực hiện Git Data API upload trực tiếp lên GitHub:
    1. Lấy commit SHA mới nhất của nhánh (branch)
    2. Lấy tree SHA của commit đó
    3. Tạo Blob cho school_equipment.db (base64)
    4. Tạo Blob cho backups/qltb_latest.json (base64)
    5. Tạo Tree mới chứa 2 blob trên
    6. Tạo Commit mới trỏ vào Tree mới và có parent là commit cũ
    7. Cập nhật nhánh trỏ tới commit mới
    """
    config = get_github_status(conn)
    owner = config['owner']
    repo = config['repo']
    branch = config['branch']
    token = os.environ.get('GITHUB_TOKEN') or get_setting(conn, 'github_token', '')

    if not token:
        raise Exception("Chưa cấu hình GitHub Token! Vui lòng nhập Personal Access Token trước khi đồng bộ.")

    # Đảm bảo flush dữ liệu SQLite xuống đĩa
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL);")
    except Exception:
        pass

    if not os.path.exists(DB_PATH):
        raise Exception(f"Không tìm thấy file CSDL tại: {DB_PATH}")

    # Đọc file SQLite nhị phân
    with open(DB_PATH, 'rb') as f:
        db_bytes = f.read()
    db_b64 = base64.b64encode(db_bytes).decode('ascii')

    # Xuất file JSON backup
    json_data = export_db_json(conn)
    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
    json_b64 = base64.b64encode(json_str.encode('utf-8')).decode('ascii')

    # 1. Lấy thông tin nhánh hiện tại
    ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    ref_res = make_github_request(ref_url, token=token)
    base_commit_sha = ref_res['object']['sha']

    # 2. Lấy base tree SHA
    commit_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_commit_sha}"
    commit_res = make_github_request(commit_url, token=token)
    base_tree_sha = commit_res['tree']['sha']

    # 3. Tạo Blob cho school_equipment.db
    blobs_url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs"
    db_blob_res = make_github_request(blobs_url, method='POST', data={
        'content': db_b64,
        'encoding': 'base64'
    }, token=token)
    db_blob_sha = db_blob_res['sha']

    # 4. Tạo Blob cho backups/qltb_latest.json
    json_blob_res = make_github_request(blobs_url, method='POST', data={
        'content': json_b64,
        'encoding': 'base64'
    }, token=token)
    json_blob_sha = json_blob_res['sha']

    # 5. Tạo Tree mới
    trees_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees"
    tree_payload = {
        'base_tree': base_tree_sha,
        'tree': [
            {
                'path': 'school_equipment.db',
                'mode': '100644',
                'type': 'blob',
                'sha': db_blob_sha
            },
            {
                'path': 'backups/qltb_latest.json',
                'mode': '100644',
                'type': 'blob',
                'sha': json_blob_sha
            }
        ]
    }
    tree_res = make_github_request(trees_url, method='POST', data=tree_payload, token=token)
    new_tree_sha = tree_res['sha']

    # 6. Tạo Commit mới
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = commit_message or f"data: tu dong dong bo CSDL tu he thong QLTB web [{now_str}]"
    commits_url = f"https://api.github.com/repos/{owner}/{repo}/git/commits"
    commit_payload = {
        'message': msg,
        'tree': new_tree_sha,
        'parents': [base_commit_sha]
    }
    new_commit_res = make_github_request(commits_url, method='POST', data=commit_payload, token=token)
    new_commit_sha = new_commit_res['sha']

    # 7. Cập nhật nhánh (Update reference)
    update_ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    make_github_request(update_ref_url, method='PATCH', data={
        'sha': new_commit_sha,
        'force': False
    }, token=token)

    # Cập nhật thông tin đồng bộ vào DB
    set_setting(conn, 'github_last_sync', now_str)
    set_setting(conn, 'github_last_sha', new_commit_sha)

    # Lưu thêm 1 file snapshot backup tại local nếu thư mục tồn tại
    try:
        backup_dir = os.path.join(BASE_DIR, 'backups')
        if os.path.exists(backup_dir):
            with open(os.path.join(backup_dir, 'qltb_latest.json'), 'w', encoding='utf-8') as f:
                f.write(json_str)
    except Exception:
        pass

    return {
        'success': True,
        'commit_sha': new_commit_sha,
        'commit_url': f"https://github.com/{owner}/{repo}/commit/{new_commit_sha}",
        'sync_time': now_str,
        'message': f"Đã đồng bộ thành công CSDL lên GitHub (Commit: {new_commit_sha[:7]})!"
    }

_last_auto_sync = 0

def trigger_async_github_sync(get_db_fn, log_fn=None):
    """
    Kích hoạt đồng bộ ngầm (background thread) nếu cấu hình auto_sync bật.
    Giới hạn không đồng bộ quá 1 lần trong vòng 2 phút để tránh spam GitHub API.
    """
    global _last_auto_sync
    import time
    now = time.time()
    if now - _last_auto_sync < 30:
        return
    _last_auto_sync = now

    def _worker():
        try:
            conn = get_db_fn()
            config = get_github_status(conn)
            if config.get('auto_sync') and config.get('has_token'):
                res = sync_database_to_github(conn, commit_message=f"data: auto-sync CSDL sau khi cap nhat [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                if log_fn:
                    log_fn("Tự động đồng bộ GitHub", f"Auto-sync thành công: {res['commit_sha'][:7]}", "system")
            conn.close()
        except Exception as e:
            print(f"[AUTO_SYNC_GITHUB_ERROR] {e}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
