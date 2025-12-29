"""
LLM 文本解析服务 - 用 kosong 抽象，当前用简单规则替代
"""
from typing import List, Dict, Optional
from datetime import datetime


class LLMService:
    """LLM 解析服务"""

    def __init__(self):
        """初始化"""
        # 科目关键词映射（用于简单规则解析）
        self.subject_keywords = {
            '数学': ['数学', '算术', '计算', '习题', '练习'],
            '语文': ['语文', '背诵', '古诗', '作文', '阅读'],
            '英语': ['英语', 'English', '单词', '听力'],
            '科学': ['科学', '物理', '化学', '生物', '实验']
        }

        # 作业类型关键词
        self.concept_keywords = [
            '背诵', '抄写', '练习', '复习', '预习',
            '完成', '阅读', '作文', '听写', '默写'
        ]

    def parse_homework_text(
        self,
        text: str,
        subjects: List[Dict]
    ) -> List[Dict]:
        """
        解析 OCR 文本为作业项列表

        Args:
            text: OCR 识别的原始文本
            subjects: 科目列表，格式: [{"id": 1, "name": "数学"}, ...]

        Returns:
            作业项列表，格式: [{"subject_id": 1, "subject_name": "数学", "text": "...", "key_concept": "..."}]
        """
        # 构建科目名称到 ID 的映射
        subject_name_to_id = {s['name']: s['id'] for s in subjects}
        subject_name_to_id.setdefault('其他', None)

        items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            # 跳过图片分隔符
            if line.startswith('---'):
                continue

            # 跳过空行或过短的行
            if not line or len(line) < 3:
                continue

            # 跳过纯数字行
            if line.isdigit():
                continue

            # 识别科目
            subject_name = self._identify_subject(line)
            subject_id = subject_name_to_id.get(subject_name)

            # 如果科目不在列表中，使用"其他"
            if subject_id is None:
                other_subject = next((s for s in subjects if s['name'] == '其他'), None)
                subject_id = other_subject['id'] if other_subject else None
                subject_name = '其他'

            # 提取关键概念
            key_concept = self._extract_key_concept(line)

            items.append({
                'subject_id': subject_id,
                'subject_name': subject_name,
                'text': line,
                'key_concept': key_concept
            })

        return items

    def _identify_subject(self, text: str) -> str:
        """根据文本识别科目"""
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return subject
        return '其他'

    def _extract_key_concept(self, text: str) -> Optional[str]:
        """提取关键概念"""
        for concept in self.concept_keywords:
            if concept in text:
                return concept
        return None

    async def parse_with_llm(
        self,
        text: str,
        subjects: List[Dict]
    ) -> List[Dict]:
        """
        使用 LLM 解析（预留 kosong 接口）

        Args:
            text: OCR 识别的原始文本
            subjects: 科目列表

        Returns:
            作业项列表
        """
        # TODO: 集成 kosong
        # 当前使用简单规则
        return self.parse_homework_text(text, subjects)


# 全局单例
_llm_service = None


def get_llm_service() -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
