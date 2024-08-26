"""
AmyAlmond Project - core/utils/version_utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <ByteFreeze>
Last Edited: 2024/8/18 14:00
Copyright (c) 2024 ByteFreeze. All rights reserved.
Version: 1.2.0 (Beta_826010)

version_utils.py 包含用于解析和比较版本号的工具函数。
"""

import re
from typing import Dict, Optional, Tuple

VERSION_PATTERN = r'^v?(\d+)\.(\d+)\.(\d+)(?:[-_ ]?([a-zA-Z]+)[-_ ]?(\d+)?)?(?:\s*\([a-zA-Z]+[-_ ]?\d+\))?$'


def parse_version(version: str) -> Optional[Dict[str, any]]:
    """
    解析版本字符串，返回结构化的版本信息。

    参数:
        version (str): 版本字符串

    返回:
        Optional[Dict[str, any]]: 包含版本信息的字典，如果解析失败则返回 None
    """
    match = re.match(VERSION_PATTERN, version)
    if not match:
        return None

    major, minor, patch, pre_release_label, pre_release_num = match.groups()

    return {
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch),
        "pre_release_label": pre_release_label.lower() if pre_release_label else None,
        "pre_release_num": int(pre_release_num) if pre_release_num else None
    }


def compare_pre_release(a: Optional[str], a_num: Optional[int],
                        b: Optional[str], b_num: Optional[int]) -> int:
    """
    比较两个预发布版本。

    参数:
        a, b (Optional[str]): 预发布标签
        a_num, b_num (Optional[int]): 预发布版本号

    返回:
        int: 如果 a > b 返回 1，如果 a < b 返回 -1，如果 a == b 返回 0
    """
    pre_release_order = {'alpha': 0, 'beta': 1, 'rc': 2}

    if a is None and b is None:
        return 0
    if a is None:
        return 1  # 正式版本大于预发布版本
    if b is None:
        return -1  # 预发布版本小于正式版本

    a_order = pre_release_order.get(a, -1)
    b_order = pre_release_order.get(b, -1)

    if a_order != b_order:
        return 1 if a_order > b_order else -1

    if a_num is None and b_num is None:
        return 0
    if a_num is None:
        return -1
    if b_num is None:
        return 1

    return 1 if a_num > b_num else (-1 if a_num < b_num else 0)


def compare_versions(v1: Dict[str, any], v2: Dict[str, any]) -> int:
    """
    比较两个版本。

    参数:
        v1, v2 (Dict[str, any]): 通过 parse_version 解析的版本信息

    返回:
        int: 如果 v1 > v2 返回 1，如果 v1 < v2 返回 -1，如果 v1 == v2 返回 0
    """
    for key in ['major', 'minor', 'patch']:
        if v1[key] > v2[key]:
            return 1
        if v1[key] < v2[key]:
            return -1

    return compare_pre_release(v1['pre_release_label'], v1['pre_release_num'],
                               v2['pre_release_label'], v2['pre_release_num'])


def is_newer_version(current: str, latest: str) -> Tuple[bool, str]:
    """
    检查最新版本是否比当前版本更新。

    参数:
        current (str): 当前版本字符串
        latest (str): 最新版本字符串

    返回:
        Tuple[bool, str]: (是否需要更新, 详细信息)
    """
    current_parsed = parse_version(current)
    latest_parsed = parse_version(latest)

    if not current_parsed or not latest_parsed:
        return False, f"无法解析版本号: 当前版本 '{current}', 最新版本 '{latest}'"

    comparison = compare_versions(latest_parsed, current_parsed)

    if comparison > 0:
        return True, f"新版本可用: {latest}"
    elif comparison < 0:
        return False, f"当前版本 {current} 已经是最新"
    else:
        # 版本号相同，但可能预发布标签不同
        if current_parsed['pre_release_label'] and not latest_parsed['pre_release_label']:
            return True, f"新正式版本可用: {latest}"
        elif not current_parsed['pre_release_label'] and latest_parsed['pre_release_label']:
            return False, f"当前版本 {current} 是正式版，无需更新到预发布版 {latest}"
        else:
            return False, "版本相同，无需更新"
