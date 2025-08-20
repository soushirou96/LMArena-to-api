import json
from pathlib import Path

# 输入文件（model_updater.py 生成的）
AVAILABLE_MODELS_FILE = Path("available_models.json")
# 输出文件（LMArenaBridge 核心配置）
MODELS_JSON_FILE = Path("models.json")

def main():
    if not AVAILABLE_MODELS_FILE.exists():
        print(f"❌ 找不到 {AVAILABLE_MODELS_FILE}，请先运行 model_updater.py 生成它。")
        return

    with open(AVAILABLE_MODELS_FILE, "r", encoding="utf-8") as f:
        models_data = json.load(f)

    models_json = {}

    for item in models_data:
        public_name = item.get("publicName")
        model_id = item.get("id")
        output_caps = item.get("capabilities", {}).get("outputCapabilities", {})

        if not public_name or not model_id:
            continue

        # 如果输出能力包含 image，则加上 :image
        if "image" in output_caps:
            models_json[f"{public_name}:image"] = f"{model_id}:image"
        else:
            models_json[public_name] = model_id

    # 保存到 models.json
    with open(MODELS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(models_json, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成 {MODELS_JSON_FILE}，共 {len(models_json)} 个模型。")

if __name__ == "__main__":
    main()
