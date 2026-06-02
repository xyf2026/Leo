#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成全国完整行政区划JSON (省→市→区县→乡镇/街道)
   从开源数据集 modood/Administrative-divisions-of-China 获取数据
"""

import json
import urllib.request
import ssl

OUTPUT = "address_full.json"

# 数据源（按优先级）
SOURCES = [
    "https://raw.githubusercontent.com/modood/Administrative-divisions-of-China/master/dist/pcas.json",
    "https://cdn.jsdelivr.net/gh/modood/Administrative-divisions-of-China@master/dist/pcas.json",
]

# 直辖市
MUNICIPALITIES = {'北京市', '天津市', '上海市', '重庆市'}


def download_json():
    """从多个源尝试下载JSON数据"""
    for url in SOURCES:
        print(f"尝试: {url}")
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                raw = resp.read().decode('utf-8')
                print(f"  下载成功! 大小: {len(raw) / 1024 / 1024:.1f} MB")
                return json.loads(raw)
        except Exception as e:
            print(f"  失败: {e}")
    raise RuntimeError("所有数据源均下载失败，请检查网络连接")


def convert_data(raw):
    """
    将 modood pcas.json 格式转换为目标格式:
    
    modood: [{"name":"省","children":[{"name":"市","children":[{"name":"区","children":[...]}]}]}]
    目标:   {"省": {"市": {"区": ["街道名",...]}}}
    """
    result = {}
    
    for prov in raw:
        pname = prov.get('name', '')
        children = prov.get('children', [])
        if not children:
            continue

        city_dict = {}

        # 判断结构：直辖市可能没有市级层
        if pname in MUNICIPALITIES:
            city_dict[pname] = {}
            for item in children:
                name = item['name']
                streets = [s['name'] if isinstance(s, dict) else s 
                          for s in item.get('children', [])]
                city_dict[pname][name] = streets
        else:
            # 普通省份：省 → 市 → 区县 → 街道
            for city in children:
                cname = city['name']
                city_dict[cname] = {}
                for county in city.get('children', []):
                    coname = county['name']
                    streets = [s['name'] if isinstance(s, dict) else s 
                              for s in county.get('children', [])]
                    city_dict[cname][coname] = streets

        if city_dict:
            result[pname] = city_dict

    return result


def main():
    print("=" * 60)
    print("  全国行政区划数据生成工具")
    print("  数据源: modood/Administrative-divisions-of-China")
    print("=" * 60)
    
    raw = download_json()
    print(f"\n已获取 {len(raw)} 个省级行政区数据，正在转换...")
    
    data = convert_data(raw)
    
    # 保存
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 统计
    total_cities = 0
    total_counties = 0
    total_streets = 0
    for cities in data.values():
        total_cities += len(cities)
        for counties in cities.values():
            total_counties += len(counties)
            for streets in counties.values():
                total_streets += len(streets)
    
    file_size_mb = len(json.dumps(data, ensure_ascii=False)) / 1024 / 1024
    
    print(f"\n{'=' * 60}")
    print(f"  ✅ 生成完成！")
    print(f"  省份: {len(data)} 个")
    print(f"  城市: {total_cities} 个")
    print(f"  区县: {total_counties} 个")
    print(f"  乡镇/街道: {total_streets} 个")
    print(f"  文件: {OUTPUT} ({file_size_mb:.1f} MB)")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
