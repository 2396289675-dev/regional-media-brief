#!/usr/bin/env bash
# 区域媒体情况简报生成器 —— 一键安装到 ~/.workbuddy/skills/
set -e

SRC="$(cd "$(dirname "$0")" && pwd)"
NAME="regional-media-brief"
DEST="${HOME}/.workbuddy/skills/${NAME}"

echo "==> 安装 ${NAME}"
echo "    源: ${SRC}"
echo "    目标: ${DEST}"

# --- 1. Python 版本检查（3.8+） ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ 未找到 python3，请先安装 Python 3.8 或更高版本"
  exit 1
fi
PY_OK=$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 8) else 0)')
if [ "$PY_OK" != "1" ]; then
  echo "✗ Python 版本过低：$(python3 --version)，需要 3.8+"
  exit 1
fi
echo "    Python: $(python3 --version)"

# --- 2. 备份旧版本（移到 /tmp，避免 .bak 被识别成重复技能） ---
if [ -d "$DEST" ]; then
  BAK="/tmp/${NAME}.bak.$(date +%Y%m%d%H%M%S)"
  echo "==> 旧版本已存在，备份到 ${BAK}"
  mv "$DEST" "$BAK"
fi

# --- 3. 复制（排除运行时噪音） ---
mkdir -p "${HOME}/.workbuddy/skills"
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'archive/' \
    "${SRC}/" "${DEST}/"
else
  mkdir -p "$DEST"
  (cd "$SRC" && tar --exclude='.DS_Store' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='archive' -cf - .) | (cd "$DEST" && tar -xf -)
fi

# --- 4. 运行时目录骨架 ---
mkdir -p "${DEST}/archive"

# rsync 的 --exclude 'archive' 会把目标侧同名目录清空，
# 装完把备份里的历史归档迁回来，避免丢掉已积累的区域成稿
if [ -n "${BAK:-}" ] && [ -d "${BAK}/archive" ]; then
  cp -R "${BAK}/archive/." "${DEST}/archive/" 2>/dev/null || true
  echo "==> 已迁回历史归档（${BAK}/archive -> ${DEST}/archive）"
fi

# --- 5. 冒烟测试 ---
echo "==> 冒烟测试"
python3 -m py_compile "${DEST}/scripts/build_docx.py" "${DEST}/scripts/build_html.py"
echo "    ✓ 脚本语法通过"

# HTML 渲染器零依赖，直接跑真实用例
TMP="$(mktemp -d)"
python3 "${DEST}/scripts/build_html.py" "${DEST}/examples/黑龙江-示例成品.md" "${TMP}/smoke.html" >/dev/null
if [ -s "${TMP}/smoke.html" ]; then
  echo "    ✓ HTML 渲染通过（$(wc -c < "${TMP}/smoke.html" | tr -d ' ') bytes）"
else
  echo "    ✗ HTML 渲染失败"
  rm -rf "$TMP"
  exit 1
fi
rm -rf "$TMP"
find "$DEST" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# docx 渲染器需要 python-docx
if python3 -c 'import docx' >/dev/null 2>&1; then
  echo "    ✓ python-docx 已就绪，docx 渲染可用"
else
  echo "    ! 未检测到 python-docx，docx 渲染暂不可用。安装："
  echo "      pip3 install -r ${DEST}/requirements.txt"
fi

echo
echo "==> 安装完成：${DEST}"
echo "    用法：在对话里直接说区域名，例如「帮我写浙江媒体情况简报」"
