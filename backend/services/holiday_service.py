"""
中国法定节假日服务

数据来源：timor.tech API (基于国务院发布的年度节假日安排)
"""
from datetime import date, datetime, timedelta
from typing import Set, Optional, Dict
import requests


class HolidayService:
    """中国法定节假日服务"""

    API_BASE = "https://timor.tech/api/holiday"

    def __init__(self):
        # 缓存：{year: {month: {day: info}}}
        self._cache: Dict[int, Dict[str, Dict]] = {}
        # 缓存已加载的月份
        self._loaded_months: Set[str] = set()

    def _load_month(self, year: int, month: int) -> None:
        """
        加载指定月份的假期数据

        Args:
            year: 年份
            month: 月份
        """
        key = f"{year}-{month:02d}"
        if key in self._loaded_months:
            return

        try:
            url = f"{self.API_BASE}/year/{year}-{month:02d}"
            headers = {
                'accept': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()

            if data.get('code') == 0 and 'holiday' in data:
                if year not in self._cache:
                    self._cache[year] = {}
                self._cache[year].update(data['holiday'])
                self._loaded_months.add(key)
        except Exception as e:
            # 网络请求失败时静默处理，使用默认逻辑
            pass

    def _get_day_info(self, target_date: date) -> Optional[Dict]:
        """
        获取指定日期的假期信息

        Args:
            target_date: 目标日期

        Returns:
            日期信息字典，不存在则返回 None
        """
        self._load_month(target_date.year, target_date.month)
        return self._cache.get(target_date.year, {}).get(
            target_date.strftime("%m-%d")
        )

    def is_holiday(self, target_date: date) -> bool:
        """
        判断是否为法定节假日

        Args:
            target_date: 目标日期

        Returns:
            是否为节假日
        """
        info = self._get_day_info(target_date)
        if info is None:
            # API 数据获取失败，使用默认逻辑（周末）
            return target_date.weekday() >= 5
        return info.get('holiday', False)

    def is_workday(self, target_date: date) -> bool:
        """
        判断是否为工作日

        规则：
        - 非节假日 且 非补班日
        - 补班日（after=true）是工作日

        Args:
            target_date: 目标日期

        Returns:
            是否为工作日
        """
        info = self._get_day_info(target_date)
        if info is None:
            # API 数据获取失败，使用默认逻辑（周一到周五）
            return target_date.weekday() < 5

        # 补班日是工作日
        if info.get('after', False):
            return True
        # 节假日不是工作日
        if info.get('holiday', False):
            return False
        # 普通工作日
        return target_date.weekday() < 5

    def get_next_workday(self, target_date: date) -> date:
        """
        获取下一个工作日

        Args:
            target_date: 基准日期

        Returns:
            下一个工作日
        """
        next_day = target_date
        while True:
            next_day = next_day + timedelta(days=1)
            if self.is_workday(next_day):
                return next_day

    def is_holiday_period(self, target_date: date) -> bool:
        """
        判断是否处于假期期间（包括假期本身和假期前的非工作日）

        用于判断当前是否处于学生放假状态

        Args:
            target_date: 目标日期

        Returns:
            是否处于假期期间
        """
        # 如果当天是假期
        if self.is_holiday(target_date):
            return True

        # 如果前一天是假期，今天可能是假期延续
        yesterday = target_date - timedelta(days=1)
        if self.is_holiday(yesterday):
            # 检查今天是否需要补班
            info = self._get_day_info(target_date)
            if info and not info.get('after', False):
                return True

        return False


# 全局单例
_holiday_service = None


def get_holiday_service() -> HolidayService:
    """获取假期服务单例"""
    global _holiday_service
    if _holiday_service is None:
        _holiday_service = HolidayService()
    return _holiday_service
