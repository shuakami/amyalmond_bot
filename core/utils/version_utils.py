"""
AmyAlmond Project - core/utils/version_utils.py

Open Source Repository: https://github.com/shuakami/amyalmond_bot
Developer: Shuakami <3 LuoXiaoHei
Copyright (c) 2024 Amyalmond_bot. All rights reserved.
Version: 1.3.0 (Stable_923001)

version_utils.py 包含用于解析和比较版本号的工具函数。
"""

import re
from typing import Dict, Optional, Tuple

VERSION_PATTERN = r'^v?(\d+)\.(\d+)\.(\d+)(?:[-_ ]?([a-zA-Z]+)[-_ ]?(\d+))?(?:\s*\(([a-zA-Z]+)[-_ ]?(\d+)\))?$'


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

    major, minor, patch, pre_release_label, pre_release_num, stability, build_num = match.groups()

    return {
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch),
        "stability": stability.lower() if stability else (pre_release_label.lower() if pre_release_label else "stable"),
        "build_num": int(build_num or pre_release_num or 0)
    }


def compare_stability(a: str, b: str) -> int:
    """
    比较两个稳定性标签。

    参数:
        a, b (str): 稳定性标签

    返回:
        int: 如果 a > b 返回 1，如果 a < b 返回 -1，如果 a == b 返回 0
    """
    stability_order = {'alpha': 0, 'beta': 1, 'pre': 2, 'stable': 3}
    a_order = stability_order.get(a, -1)
    b_order = stability_order.get(b, -1)

    if a_order > b_order:
        return 1
    elif a_order < b_order:
        return -1
    else:
        return 0


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

    stability_comparison = compare_stability(v1['stability'], v2['stability'])
    if stability_comparison != 0:
        return stability_comparison

    if v1['build_num'] > v2['build_num']:
        return 1
    elif v1['build_num'] < v2['build_num']:
        return -1
    else:
        return 0


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
        update_type = "强烈建议" if latest_parsed['stability'] in ['stable', 'pre'] else "建议"
        return True, f"{update_type}更新: 新版本 {latest} 可用"
    elif comparison < 0:
        return False, f"当前版本 {current} 已经是最新"
    else:
        stability_comparison = compare_stability(latest_parsed['stability'], current_parsed['stability'])
        if stability_comparison > 0:
            update_type = "强烈建议" if latest_parsed['stability'] in ['stable', 'pre'] else "建议"
            return True, f"{update_type}更新: 新的稳定版本 {latest} 可用"
        elif stability_comparison < 0:
            return False, f"当前版本 {current} 比服务器版本 {latest} 更稳定，无需更新"
        else:
            return False, "已是最新，无需更新"