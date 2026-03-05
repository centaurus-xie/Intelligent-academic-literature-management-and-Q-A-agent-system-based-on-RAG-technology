"""
元素提取模块
根据版面分析结果，提取特定类型的元素
"""
import fitz
import base64
from io import BytesIO
from typing import List, Dict, Any


class ElementExtractor:
    """元素提取器"""
    
    def __init__(self):
        pass
    
    def extract_elements(self, doc: fitz.Document, page_num: int, layout_elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根据版面分析结果提取元素
        """
        page = doc[page_num]
        extracted = {
            'text_elements': [],
            'image_elements': [],
            'table_elements': [],
            'formula_elements': []
        }
        
        for element in layout_elements:
            if element['type'] == 'text':
                extracted['text_elements'].append(element)
            elif element['type'] == 'image':
                # 提取图片数据
                image_data = self._extract_image_data(page, element)
                if image_data:
                    element['image_data'] = image_data
                    extracted['image_elements'].append(element)
            elif element['type'] == 'table':
                # 提取表格数据
                table_data = self._extract_table_data(page, element)
                if table_data:
                    element['table_data'] = table_data
                    extracted['table_elements'].append(element)
        
        return extracted
    
    def _extract_image_data(self, page: fitz.Page, element: Dict[str, Any]) -> str:
        """提取图片数据为Base64编码"""
        try:
            xref = element['xref']
            pix = fitz.Pixmap(page.parent, xref)
            
            if pix.n < 5:  # 如果不是CMYK格式
                img_data = pix.tobytes(output='png')
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                pix = None  # 释放内存
                return img_base64
            else:
                # CMYK转RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix.tobytes(output='png')
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                pix = None  # 释放内存
                return img_base64
        except Exception as e:
            print(f"提取图片数据失败: {e}")
            return None
    
    def _extract_table_data(self, page: fitz.Page, element: Dict[str, Any]) -> Dict[str, Any]:
        """提取表格数据"""
        try:
            # 从页面文本中查找表格内容
            # 这里简化实现，实际应用中需要更复杂的表格识别算法
            bbox = element['bbox']
            
            # 提取指定区域的文本
            table_text = page.get_textbox(bbox)
            
            # 检查是否包含表格特征
            if self._is_table_content(table_text):
                return {
                    'bbox': bbox,
                    'raw_text': table_text,
                    'structured_data': self._parse_simple_table(table_text)
                }
        except Exception as e:
            print(f"提取表格数据失败: {e}")
        
        return None
    
    def _is_table_content(self, text: str) -> bool:
        """判断文本是否为表格内容"""
        # 简单规则：如果文本包含多个分隔符，则认为是表格
        lines = text.split('\n')
        for line in lines:
            if '|' in line and line.count('|') > 2:  # 包含多个竖线
                return True
            if '\t' in line and line.count('\t') > 1:  # 包含多个制表符
                return True
        return False
    
    def _parse_simple_table(self, text: str) -> List[List[str]]:
        """简单表格解析"""
        rows = []
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                row = [cell.strip() for cell in line.split('|')]
                row = [cell for cell in row if cell]  # 移除空单元格
                if row:
                    rows.append(row)
            elif '\t' in line:
                row = [cell.strip() for cell in line.split('\t')]
                if row:
                    rows.append(row)
        return rows