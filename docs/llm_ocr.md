# 使用 LLM 完成 OCR 解析和数据解析

## 现状分析

当前的实现是通过 PaddleOCR 进行文字识别，识别的准确率的确是有保障了，但还是面临几个后续处理要做的事情.

- 为图片打标签（homework、reference）
- 通过对一个批次的图片识别文字，理解文字后再提取 HomeworkItems ,还要将 reference 关联回到 HomeworkItem

所以现在想要通过 LLM 直接来完成这些部分的工作，基于 VLM 的能力让模型输出：OCR 结果、HomeworkItems、references-HomeworkItem关系、图片 label。

模型选择: <https://docs.bigmodel.cn/cn/guide/models/free/glm-4.6v-flash>
zhipu 免费多模态 模型

## Prompt

你的任务是帮助学生从教师布置的作业图片列表中提取作业信息。

图片为黑板板书的照片，或者是参考资料（书本、作业示例）。

你会收到一组图片，对应的是一批的作业。你需要按照下面的要求处理：

1. 先识别图片中的文字内容，然后为图片分类为两类：作业图片（homework）和参考资料图片（reference）。
2. 对每张 homework 的图片，识别其中的内容，提取为 HomeworkItem 信息。注意理解作业图片内容，将相关的参考资料图片与之关联(referenceFileName)。
3. 构建 Data 对象，输出 JSON 格式数据，符合下面的 Pydantic 模型定义。

关于 HomeworkItem 拆解的注意事项：

- HomeworkItem 是作业独立单元，每个 HomeworkItem 都是可以独立完成的作业任务。
- 需要注意，有时候图片中可能同一个 HomeworkItem 会出现换行的情况，你需要根据语义的相关性来判断是否为同一个 HomeworkItem。
- 你应该尽可能将一张 homework 图片中的多个作业任务拆解为多个 HomeworkItem。
- 一张 reference 图片，可以对应到一个 HomeworkItem

```python
class HomeworkItem(BaseModel):
    subject: str = Field(..., description="科目名称")
    text: str = Field(..., description="作业文本内容")
    imageFileName: str = Field(..., description="作业图片文件名")
    has_reference: bool = Field(..., description="是否有参考资料")
    referenceFileName: str = Field(..., description="参考资料文件名，无则为空字符串")


class Data(BaseModel):
    referenceFileName: List[str] = Field(..., description="reference类型图片列表，通过图片的索引值命名")
    homeworkFileName: List[str] = Field(..., description="homework类型图片列表，通过图片的索引值命名")
    homework_items: List[HomeworkItem] = Field(..., description="作业项目列表")
```

输出 JSON 示例：

```json
{
    "referenceFileName": ["index2"],
    "homeworkFileName": ["index0", "index1"],
    "homework_items": [
        {
            "subject": "数学",
            "text": "1.完成练习册第10页",
            "imageFileName": "index0",
            "has_reference": False,
            "referenceFileName": ""
        },
        {
            "subject": "数学",
            "text": "2.完成课本第20页练习题",
            "imageFileName": "index0",
            "has_reference": True,
            "referenceFileName": "index2"
        },
        {
            "subject": "语文",
            "text": "背诵古诗",
            "imageFileName": "index1",
            "has_reference": Flase,
            "referenceFileName": ""
        }
    ]
}
```
