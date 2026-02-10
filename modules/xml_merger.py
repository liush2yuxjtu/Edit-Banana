"""
XML Merger Module
XML 文件合并工具
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os


class XMLMerger:
    """XML 合并器"""
    
    @staticmethod
    def merge_xml_files(file_paths: List[str], output_path: str) -> bool:
        """
        合并多个 XML 文件
        
        Args:
            file_paths: XML 文件路径列表
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 读取第一个文件作为基础
            if not file_paths:
                return False
            
            tree = ET.parse(file_paths[0])
            root = tree.getroot()
            
            # 合并其他文件
            for file_path in file_paths[1:]:
                try:
                    other_tree = ET.parse(file_path)
                    other_root = other_tree.getroot()
                    
                    # 将其他文件的子元素添加到根节点
                    for child in other_root:
                        root.append(child)
                        
                except Exception as e:
                    print(f"⚠️  跳过文件 {file_path}: {e}")
                    continue
            
            # 写入输出文件
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            return True
            
        except Exception as e:
            print(f"❌ XML 合并失败: {e}")
            return False
    
    @staticmethod
    def merge_drawio_files(file_paths: List[str], output_path: str) -> bool:
        """
        合并 draw.io 文件
        
        Args:
            file_paths: draw.io 文件路径列表
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            if not file_paths:
                return False
            
            # 读取第一个文件
            with open(file_paths[0], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析 XML
            root = ET.fromstring(content)
            
            # 查找 mxGraphModel 元素
            graph_model = root.find('.//mxGraphModel')
            if graph_model is None:
                raise ValueError("未找到 mxGraphModel 元素")
            
            # 获取根节点
            root_node = graph_model.find('root')
            if root_node is None:
                raise ValueError("未找到 root 元素")
            
            # 合并其他文件
            for file_path in file_paths[1:]:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        other_content = f.read()
                    
                    other_root = ET.fromstring(other_content)
                    other_graph_model = other_root.find('.//mxGraphModel')
                    other_root_node = other_graph_model.find('root') if other_graph_model is not None else None
                    
                    if other_root_node is not None:
                        # 复制除默认节点外的所有子节点
                        for child in other_root_node:
                            if child.attrib.get('id') != '0' and child.attrib.get('id') != '1':
                                root_node.append(child)
                                
                except Exception as e:
                    print(f"⚠️  跳过文件 {file_path}: {e}")
                    continue
            
            # 写入输出文件
            xml_str = ET.tostring(root, encoding='utf-8', method='xml')
            with open(output_path, 'wb') as f:
                f.write(xml_str)
                
            return True
            
        except Exception as e:
            print(f"❌ draw.io 合并失败: {e}")
            return False
    
    @staticmethod
    def extract_elements_from_drawio(file_path: str) -> List[Dict[str, Any]]:
        """
        从 draw.io 文件中提取元素
        
        Args:
            file_path: draw.io 文件路径
            
        Returns:
            List[Dict]: 元素列表
        """
        elements = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            root = ET.fromstring(content)
            
            # 查找所有 mxCell 元素
            cells = root.findall('.//mxCell')
            
            for cell in cells:
                cell_id = cell.attrib.get('id')
                parent_id = cell.attrib.get('parent')
                style = cell.attrib.get('style')
                vertex = cell.attrib.get('vertex')
                edge = cell.attrib.get('edge')
                
                # 提取 geometry
                geometry = cell.find('mxGeometry')
                x = y = width = height = 0
                if geometry is not None:
                    x = float(geometry.attrib.get('x', '0'))
                    y = float(geometry.attrib.get('y', '0'))
                    width = float(geometry.attrib.get('width', '0'))
                    height = float(geometry.attrib.get('height', '0'))
                
                element = {
                    'id': cell_id,
                    'parent': parent_id,
                    'style': style,
                    'vertex': vertex,
                    'edge': edge,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height
                }
                
                elements.append(element)
                
        except Exception as e:
            print(f"❌ 提取 draw.io 元素失败: {e}")
        
        return elements
    
    @staticmethod
    def create_empty_drawio() -> str:
        """
        创建空的 draw.io 文件
        
        Returns:
            str: XML 字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="764" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>'''
        
        return xml_template
