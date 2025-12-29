# OCR 识别优化记录

## 问题描述

初始 OCR 识别效果很差，对于黑板粉笔字作业图片，识别结果是一堆单个字符：

```
n
a
o
t
o
e
e
e
e
e
e
e
i
e
e
```

## 问题排查过程

### 1. 确认图片内容

使用图像分析确认图片内容是一块黑板，上面有粉笔书写的作业：

- 顶部：12月29日-
- 语文作业：默写本全部写完。认真大声读速记卡三次。
- 数学作业：订正练习(四)，家签。S本P82-83。

### 2. 创建调试脚本

创建 `backend/scripts/test_ocr.py` 脚本，支持 `--debug` 参数查看详细识别过程。

### 3. 逐步发现问题

#### 问题一：`cls` 参数错误

**错误信息**：

```
OCR 识别失败: PaddleOCR.predict() got an unexpected keyword argument 'cls'
```

**原因**：

- 旧版 API：`ocr.ocr(img_array, cls=True)`
- 新版 PaddleOCR 不再接受调用时的 `cls` 参数

**修复**：

```python
# 修复前
result = self.ocr.ocr(img_array, cls=True)

# 修复后
result = self.ocr.ocr(img_array)
```

#### 问题二：API 弃用警告

**警告信息**：

```
DeprecationWarning: Please use `predict` instead.
result = ocr.ocr(img_array)
```

**原因**：PaddleOCR 新版推荐使用 `predict()` 方法

**修复**：

```python
# 修复前
result = self.ocr.ocr(img_array)

# 修复后
result = self.ocr.predict(img_array)
```

#### 问题三：返回格式变化

**现象**：识别结果为空

通过调试发现新版返回格式：

```
result type: <class 'list'>
result[0] type: <class 'paddlex.inference.pipelines.ocr.result.OCRResult'>
result[0] keys: ['rec_texts', 'rec_scores', ...]
```

**原因**：

- 旧版：`list[list[tuple[bbox, (text, score)]]]`
- 新版：`list[OCRResult]`，OCRResult 是 dict-like 对象

**修复**：

```python
# 修复前
def _extract_text(self, ocr_result) -> str:
    if not ocr_result or not ocr_result[0]:
        return ""
    texts = []
    for line in ocr_result[0]:
        if line and line[1] and line[1][0]:
            texts.append(line[1][0])
    return '\n'.join(texts)

# 修复后
def _extract_text(self, ocr_result) -> str:
    if not ocr_result or not isinstance(ocr_result, list) or len(ocr_result) == 0:
        return ""
    first = ocr_result[0]
    texts = first.get('rec_texts', [])
    return '\n'.join(texts)
```

#### 问题四：初始化参数废弃

**警告信息**：

```
DeprecationWarning: The parameter `use_angle_cls` has been deprecated
```

**修复**：

```python
# 修复前
self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 修复后
self.ocr = PaddleOCR(lang='ch')
```

## 最终效果

修复后识别结果（置信度都很高）：

```
[0] 12月29日一 (置信度: 0.91)
[1] 语：1默写本全部写完。 (置信度: 0.89)
[2] 2认真大声读速记卡 (置信度: 0.99)
[3] 三次。 (置信度: 0.96)
[4] 数：1、订正练习(四)，家签 (置信度: 0.87)
[5] 2.S本P82-83。 (置信度: 0.91)
```

## 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/services/ocr_service.py` | 更新 API 调用，修复返回值处理 |
| `backend/scripts/test_ocr.py` | 创建调试脚本，支持新 API |

## 关键代码变更

### OCR 服务初始化

```python
# 旧代码
self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 新代码
self.ocr = PaddleOCR(lang='ch')
```

### OCR 识别调用

```python
# 旧代码
result = self.ocr.ocr(img_array)

# 新代码
result = self.ocr.predict(img_array)
```

### 结果提取

```python
# 旧代码
for line in ocr_result[0]:
    bbox, (text, confidence) = line
    texts.append(text)

# 新代码
first = ocr_result[0]
texts = first.get('rec_texts', [])
scores = first.get('rec_scores', [])
```

## 附录：测试脚本使用

```bash
# 基本使用
uv run python -m backend.scripts.test_ocr <图片路径>

# 调试模式（显示详细信息）
uv run python -m backend.scripts.test_ocr <图片路径> --debug
```
