#!/usr/bin/env python3
from __future__ import annotations

"""
Docker + noVNC Selenium runner for LMArena Bridge.
- Starts selenium/standalone-chrome container (WebDriver 4444, noVNC 7900)
- Injects LMArenaApiBridge userscript into every new document via CDP
- Detects Cloudflare challenge and asks user to open noVNC to solve
- Rewrites localhost endpoints in userscript to host.docker.internal for WS/HTTP back to host
"""
import argparse
import json
import os
import subprocess
import sys
import time
import re
import random
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ROOT = Path(__file__).resolve().parents[1]
USERSCRIPT_PATH = ROOT / "TampermonkeyScript" / "LMArenaApiBridge.js"
DEFAULT_IMAGE = "selenium/standalone-chrome:latest"
DEFAULT_CONTAINER = "lm_cf_browser"
WEBDRIVER_URL = "http://localhost:4444/wd/hub"
NOVNC_URL = "http://localhost:7900/?autoconnect=1&resize=scale&password=secret"
AVAILABLE_MODELS_PATH = ROOT / "available_models.json"
SOCKS_LOCK_PATH = ROOT / "socks5.lock.json"
CONFIG_PATH = ROOT / "config.jsonc"

def run(cmd: list[str], check=True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)

def is_container_running(name: str) -> bool:
    try:
        cp = run(["docker", "ps", "-q", "-f", f"name={name}"], check=False)
        return cp.stdout.strip() != ""
    except FileNotFoundError:
        print("[ERROR] Docker 未安装或未在 PATH 中。请安装 Docker Desktop。")
        sys.exit(1)

def ensure_container(image: str, name: str) -> None:
    if is_container_running(name):
        print(f"[INFO] 容器 {name} 已在运行。")
        return
    print(f"[INFO] 启动容器 {name}（镜像: {image}）...")
    cmd = [
        "docker","run","-d","--rm",
        "-p","4444:4444",
        "-p","7900:7900",
        "--shm-size=2g",
        "--name",name,
        image
    ]
    cp = run(cmd, check=True)
    cid = cp.stdout.strip()
    print(f"[INFO] 容器已启动: {cid}")

def wait_webdriver_ready(timeout_sec: int = 60) -> None:
    print("[INFO] 等待 WebDriver 服务就绪...")
    t0 = time.time()
    last_err = None
    while time.time() - t0 < timeout_sec:
        try:
            r = requests.get(WEBDRIVER_URL + "/status", timeout=2)
            if r.ok:
                data = r.json()
                ready = data.get("value",{}).get("ready", False) or data.get("ready", False)
                if ready:
                    print("[INFO] WebDriver 已就绪。")
                    return
        except Exception as e:
            last_err = e
        time.sleep(1.5)
    print(f"[ERROR] 等待 WebDriver 超时: {last_err}")
    sys.exit(1)

def patch_userscript_for_docker(raw_js: str) -> str:
    """
    将 userscript 与 polyfills 一起包裹在域名守卫 IIFE 中，并把 localhost/127.0.0.1 改写为 host.docker.internal，
    确保仅在 *.lmarena.ai 下执行，且容器内可访问宿主机服务。
    """
    patched = raw_js
    replace_pairs = [
        ("ws://localhost:5102", "ws://host.docker.internal:5102"),
        ("ws://127.0.0.1:5102", "ws://host.docker.internal:5102"),
        ("http://localhost:5102", "http://host.docker.internal:5102"),
        ("http://127.0.0.1:5102", "http://host.docker.internal:5102"),
        ("http://localhost:5103", "http://host.docker.internal:5103"),
        ("http://127.0.0.1:5103", "http://host.docker.internal:5103"),
    ]
    for a, b in replace_pairs:
        patched = patched.replace(a, b)

    wrapper = f"""
;(function() {{
  try {{
    var host = location.hostname || "";
    if (!/lmarena\\.ai$/i.test(host) && !/\\.lmarena\\.ai$/i.test(host)) return;
  }} catch (e) {{}}
  {patched}
}})();
"""
    return wrapper

def build_polyfills() -> str:
    return r"""
;(function(){
  if(!window.GM_addStyle){
    window.GM_addStyle=function(css){
      try{var s=document.createElement('style');s.textContent=css;document.documentElement.appendChild(s);return s;}catch(e){}
    };
  }
  if(!window.GM_setValue){window.GM_setValue=(k,v)=>localStorage.setItem(k,JSON.stringify(v));}
  if(!window.GM_getValue){window.GM_getValue=(k,d)=>{var v=localStorage.getItem(k);return v?JSON.parse(v):d;};}
  if(!window.GM_deleteValue){window.GM_deleteValue=(k)=>localStorage.removeItem(k);}
  if(!window.GM_xmlHttpRequest){
    window.GM_xmlHttpRequest=function({method='GET',url,headers={},data,onload,onerror}){
      fetch(url,{method,headers,body:data,credentials:'include'})
        .then(async res=>{var text=await res.text();onload&&onload({responseText:text,status:res.status,headers:Object.fromEntries(res.headers.entries())});})
        .catch(err=>onerror&&onerror(err));
    };
  }
})();
"""

def load_userscript() -> str:
    if not USERSCRIPT_PATH.exists():
        print(f"[ERROR] 找不到脚本: {USERSCRIPT_PATH}")
        sys.exit(1)
    raw = USERSCRIPT_PATH.read_text(encoding="utf-8")
    # 先拼接 polyfills + 原脚本，再统一做域名守卫与 host.docker.internal 改写
    combined = build_polyfills() + "\n" + raw
    return patch_userscript_for_docker(combined)

# ===================== SOCKS5 支持与探测 =====================

def _strip_jsonc(text: str) -> str:
    # 移除 // 行注释 与 /* ... */ 块注释（简单实现，足够解析我们用到的键）
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return text

def load_config() -> dict:
    try:
        if not CONFIG_PATH.exists():
            return {}
        raw = CONFIG_PATH.read_text(encoding="utf-8")
        clean = _strip_jsonc(raw)
        return json.loads(clean or "{}")
    except Exception:
        return {}

def normalize_socks5(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if not (v.startswith("socks5://") or v.startswith("socks5h://")):
        v = "socks5://" + v
    return v

def load_socks_candidates_from_args_and_config(args) -> list[str]:
    cands: list[str] = []
    # 来自命令行
    if getattr(args, "socks5", None):
        for part in (args.socks5 or "").split(","):
            p = normalize_socks5(part)
            if p:
                cands.append(p)
    # 来自配置（需显式开启）
    cfg = load_config()
    if cfg.get("socks5_enabled", False):
        for part in (cfg.get("socks5_candidates") or []):
            p = normalize_socks5(str(part))
            if p:
                cands.append(p)
    # 去重，保持顺序
    uniq: list[str] = []
    seen = set()
    for p in cands:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq

def read_locked_socks5() -> str | None:
    try:
        if SOCKS_LOCK_PATH.exists():
            data = json.loads(SOCKS_LOCK_PATH.read_text(encoding="utf-8"))
            p = data.get("proxy")
            p = normalize_socks5(p) if p else None
            if p:
                print(f"[SOCKS] 读取锁定代理: {p}")
            return p
    except Exception:
        pass
    return None

def write_locked_socks5(proxy: str) -> None:
    try:
        SOCKS_LOCK_PATH.write_text(
            json.dumps({"proxy": proxy, "ts": int(time.time())}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[SOCKS] 已锁定并保存 SOCKS5: {proxy} -> {SOCKS_LOCK_PATH}")
    except Exception as e:
        print(f"[SOCKS] 写入锁文件失败: {e}")

def create_chrome_options(proxy: str | None = None, user_data_dir: str | None = None) -> ChromeOptions:
    options = ChromeOptions()
    options.page_load_strategy = "eager"
    # 允许混合内容与本地自签证书，便于 https 页面对接本机 http/ws 服务
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--disable-features=BlockInsecurePrivateNetworkRequests")
    options.set_capability("acceptInsecureCerts", True)
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
        print(f"[SOCKS] 使用代理: {proxy}")
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
        print(f"[SOCKS] 使用新的用户数据目录: {user_data_dir}")
    return options

def create_driver_with(proxy: str | None = None, user_data_dir: str | None = None):
    opts = create_chrome_options(proxy, user_data_dir)
    try:
        drv = webdriver.Remote(command_executor=WEBDRIVER_URL, options=opts)
        return drv
    except Exception as e:
        print(f"[SOCKS] 创建带代理的浏览器会话失败: {e}")
        return None

def probe_site_reachable(driver, url: str, timeout_sec: int = 15) -> bool:
    try:
        driver.set_page_load_timeout(timeout_sec)
        driver.get(url)
        WebDriverWait(driver, timeout_sec).until(
            lambda d: d.execute_script("return document.readyState")== "complete"
        )
        return True
    except Exception as e:
        print(f"[SOCKS] 站点连通性检测失败: {e}")
        return False

def clear_browser_data(driver) -> None:
    # 清理缓存与 Cookie，尽可能“清空浏览器数据”
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
    except Exception:
        pass
    try:
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
    except Exception:
        pass

def add_userscript_on_new_document(driver, script_src: str) -> None:
    # 在每个新文档 document_start 注入
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script_src})

def navigate(driver, url: str) -> None:
    driver.get(url)
    WebDriverWait(driver, 60).until(lambda d: d.execute_script("return document.readyState")== "complete")

CF_SELECTORS = [
    "iframe[src*='challenges.cloudflare.com']",
    "[class*='cf-challenge']",
    "[data-sitekey]",   # turnstile
    "#challenge-form"
]

def has_element(driver, css: str) -> bool:
    try:
        elems = driver.find_elements(By.CSS_SELECTOR, css)
        return len(elems) > 0
    except Exception:
        return False

def detect_cloudflare(driver) -> bool:
    try:
        html = driver.page_source.lower()
        if any(k in html for k in ["cloudflare","challenge-platform","cf-chl","turnstile"]):
            for sel in CF_SELECTORS:
                if has_element(driver, sel):
                    return True
        return False
    except Exception:
        return False

def wait_userscript_ws_ready(driver, timeout_sec: int = 60) -> bool:
    """
    通过观察页面标题是否以 '✅ ' 前缀开头来判断油猴脚本是否已连上本机 WebSocket。
    该前缀由 Userscript 在 socket.onopen 中设置。
    """
    print("[INFO] 等待用户脚本建立 WebSocket 连接（标题前缀 '✅ '）...")
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        try:
            title = driver.execute_script("return document.title || ''") or ""
            if isinstance(title, str) and title.strip().startswith("✅"):
                print("[INFO] 检测到 WebSocket 连接成功（标题包含 ✅）。")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("[WARN] 在指定时间内未检测到 '✅' 标记，可能是 API 服务未启动或被浏览器拦截了混合内容。")
    return False

def api_server_healthcheck() -> bool:
    try:
        r = requests.get("http://127.0.0.1:5102/v1/models", timeout=3)
        # 即使 404 也说明服务在线
        print(f"[INFO] 本机 api_server 健康检查: HTTP {r.status_code}")
        return True
    except Exception as e:
        print(f"[WARN] 无法访问本机 api_server: {e}")
        return False

def run_connectivity_self_test(timeout_sec: int = 45) -> None:
    """
    端到端连通性自检：
    1) POST /internal/request_model_update 通知浏览器发送页面HTML
    2) 观察 available_models.json 是否在超时内被更新（由浏览器回传 HTML 后 api_server 写入）
    """
    print("[TEST] 启动端到端连通性自检 ...")
    start_mtime = AVAILABLE_MODELS_PATH.stat().st_mtime if AVAILABLE_MODELS_PATH.exists() else 0.0

    try:
        rr = requests.post("http://127.0.0.1:5102/internal/request_model_update", timeout=5)
        if rr.status_code != 200:
            print(f"[TEST] 请求发送指令失败: HTTP {rr.status_code} {rr.text}")
            return
        print("[TEST] 已向 api_server 发送 'send_page_source' 指令，等待浏览器回传 ...")
    except Exception as e:
        print(f"[TEST] 发送指令异常: {e}")
        return

    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        try:
            if AVAILABLE_MODELS_PATH.exists():
                cur_mtime = AVAILABLE_MODELS_PATH.stat().st_mtime
                if cur_mtime > start_mtime:
                    print(f"[TEST] ✅ available_models.json 已更新，连通性自检通过。文件时间: {time.ctime(cur_mtime)}")
                    return
        except Exception:
            pass
        time.sleep(1.0)
    print("[TEST] ❌ 自检超时：浏览器可能未成功回传页面，或混合内容被阻止。请确认 '✅' 标记已出现、以及已允许不安全内容。")

def main():
    parser = argparse.ArgumentParser(description="Docker+noVNC LMArena Bridge 浏览器引导器")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Docker 镜像（默认 selenium/standalone-chrome:latest）")
    parser.add_argument("--name", default=DEFAULT_CONTAINER, help="容器名称")
    parser.add_argument("--url", default="https://lmarena.ai/", help="启动后打开的 URL")
    parser.add_argument("--keep-container", action="store_true", help="退出时保留容器不停止")
    parser.add_argument("--self-test", action="store_true", help="启动后执行连通性自检（需本机 api_server.py 已运行）")
    parser.add_argument("--test-timeout", type=int, default=45, help="连通性自检的最大等待秒数（默认 45s）")
    # SOCKS5 相关
    parser.add_argument(
        "--socks5",
        default="",
        help="启用 SOCKS5 代理。可传入逗号分隔的多个值，例如 host1:1080,host2:1080 或 socks5://user:pass@host:1080；若留空则不启用"
    )
    parser.add_argument(
        "--socks-test-timeout",
        type=int,
        default=15,
        help="SOCKS5 可用性探测超时秒数（默认 15s）"
    )
    args = parser.parse_args()

    ensure_container(args.image, args.name)
    wait_webdriver_ready()

    # 选择/锁定 SOCKS5 并创建浏览器会话
    cfg = load_config()
    socks_enabled = bool(getattr(args, "socks5", "").strip()) or bool(cfg.get("socks5_enabled", False))
    candidates = load_socks_candidates_from_args_and_config(args) if socks_enabled else []
    locked = read_locked_socks5() if socks_enabled else None
    # 构造尝试序列：先尝试锁定，再尝试候选
    try_seq: list[str] = []
    if locked:
        try_seq.append(locked)
    for c in candidates:
        if c not in try_seq:
            try_seq.append(c)

    driver = None
    chosen_proxy: str | None = None
    need_new_profile_for_next = False

    if try_seq:
        for idx, proxy in enumerate(try_seq):
            # 先试“锁定”的原配置；若失败，再为新候选使用全新用户数据目录
            user_dir = None
            if idx == 0 and locked:
                drv = create_driver_with(proxy)
                if drv and probe_site_reachable(drv, args.url, timeout_sec=args.socks_test_timeout):
                    driver = drv
                    chosen_proxy = proxy
                    break
                else:
                    if drv:
                        try:
                            clear_browser_data(drv)
                        except Exception:
                            pass
                        try:
                            drv.quit()
                        except Exception:
                            pass
                    need_new_profile_for_next = True
                    continue
            # 其他候选：使用新的用户数据目录，等同“清除浏览器数据”
            suffix = f"{int(time.time())}-{random.randint(1000,9999)}"
            user_dir = f"/tmp/chrome-profile-{suffix}"
            drv = create_driver_with(proxy, user_data_dir=user_dir)
            if drv and probe_site_reachable(drv, args.url, timeout_sec=args.socks_test_timeout):
                driver = drv
                chosen_proxy = proxy
                break
            else:
                if drv:
                    try:
                        drv.quit()
                    except Exception:
                        pass

        if driver is None:
            print("[SOCKS] 未找到可用的 SOCKS5 代理，退出。")
            sys.exit(1)

        if chosen_proxy:
            write_locked_socks5(chosen_proxy)

    else:
        # 未设置 SOCKS5：不使用代理
        driver = create_driver_with(None)
        if not driver:
            print("[ERROR] 无法连接到 Remote WebDriver")
            sys.exit(1)

    # 对每个新 document 注入 userscript，并重新加载目标页以生效
    script_src = load_userscript()
    add_userscript_on_new_document(driver, script_src)
    navigate(driver, args.url)

    # 检测 CF
    if detect_cloudflare(driver):
        print("\n[CF] 检测到 Cloudflare 质询/验证.")
        print(f"[CF] 请在浏览器打开 noVNC: {NOVNC_URL}")
        print("[CF] 在 noVNC 中完成验证，确认页面可以正常访问后，回到此窗口按回车继续...")
        try:
            input()
        except KeyboardInterrupt:
            pass
        # 验证是否通过
        if detect_cloudflare(driver):
            print("[WARN] 仍检测到 Cloudflare 组件，可能未完成验证。你可再次 noVNC 操作，然后回车继续。按 Ctrl+C 放弃。")
            try:
                input()
            except KeyboardInterrupt:
                pass
        if not detect_cloudflare(driver):
            print("[OK] Cloudflare 验证看起来已通过。")
        else:
            print("[WARN] Cloudflare 仍存在，继续保持 noVNC 会话，稍后再试。")

    # 等待用户脚本 WebSocket 连接标志（标题前缀 ✅）
    ws_ok = wait_userscript_ws_ready(driver, timeout_sec=args.test_timeout)

    # 可选：做一次端到端自检（需要 api_server.py 正在本机运行）
    if args.self_test:
        if api_server_healthcheck() and ws_ok:
            run_connectivity_self_test(timeout_sec=args.test_timeout)
        else:
            print("[TEST] 跳过自检：api_server 未启动或用户脚本 WS 未就绪。")

    print("\n[READY] 浏览器会话已准备就绪。保持此进程运行以维持与本机 api_server.py 的 WebSocket 连接。")
    print("        你可以随时打开 noVNC 观察/操作: " + NOVNC_URL)
    print("        结束会话请按 Ctrl+C")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[EXIT] 正在退出...")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        if not args.keep_container:
            print(f"[INFO] 停止容器 {args.name} ...")
            run(["docker","rm","-f",args.name], check=False)
            print("[INFO] 容器已停止。")

if __name__ == "__main__":
    main()