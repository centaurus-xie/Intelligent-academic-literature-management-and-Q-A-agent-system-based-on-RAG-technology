"""
版面分析模块
负责识别PDF页面中的文本、图片、表格等元素的位置和类型
"""
import fitz
from typing import List, Dict, Any


class LayoutAnalyzer:
    """版面分析器"""
    
    def __init__(self):
        pass
    
    def analyze_page(self, doc: fitz.Document, page_num: int) -> List[Dict[str, Any]]:
        """
        分析PDF页面的版面布局
        返回页面中各种元素的信息
        """
        page = doc[page_num]
        layout_elements = []
        
        # 获取文本块信息
        text_blocks = self._extract_text_blocks(page)
        layout_elements.extend(text_blocks)
        
        # 获取图片信息
        image_blocks = self._extract_image_blocks(page)
        layout_elements.extend(image_blocks)
        
        # 获取表格信息（通过分析线条和文本位置）
        table_blocks = self._detect_table_areas(page)
        layout_elements.extend(table_blocks)
        
        return layout_elements
    
    def _extract_text_blocks(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """提取文本块"""
        text_blocks = []
        
        # 获取文本信息，包含位置和格式
        text_dict = page.get_text('dict')
        
        for block in text_dict.get('blocks', []):
            if 'lines' in block:  # 这是文本块
                bbox = block['bbox']
                text_block = {
                    'type': 'text',
                    'bbox': bbox,
                    'content': self._extract_block_text(block),
                    'spans': block.get('lines', [])
                }
                text_blocks.append(text_block)
        
        return text_blocks
    
    def _extract_image_blocks(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """提取图片块"""
        image_blocks = []
        
        # 获取页面中的图片
        img_list = page.get_images()
        
        for img_index, img in enumerate(img_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                # 获取图片在页面上的位置
                img_bbox = self._get_image_bbox(page, xref)
                
                if pix.n < 5:  # 如果不是CMYK格式
                    image_block = {
                        'type': 'image',
                        'bbox': img_bbox,
                        'xref': xref,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.colorspace.name if pix.colorspace else 'unknown'
                    }
                    image_blocks.append(image_block)
                
                pix = None  # 释放内存
            except Exception as e:
                print(f"提取图片失败: {e}")
        
        return image_blocks
    
    def _detect_table_areas(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """检测表格区域"""
        table_areas = []
        
        # 通过分析线条来检测表格
        # 获取页面的形状信息
        shapes = page.get_drawings()
        
        # 分析线条和矩形
        horizontal_lines = []
        vertical_lines = []
        
        for shape in shapes:
            for item in shape:
                if item[0] == 'l':  # 线条
                    p1, p2 = item[1], item[2]
                    # 确保p1和p2是Point对象或包含坐标信息的元组
                    try:
                        # 如果是PyMuPDF的Point对象
                        if hasattr(p1, 'y') and hasattr(p2, 'y'):
                            if abs(p1.y - p2.y) < 1:  # 水平线
                                horizontal_lines.append((p1, p2))
                            elif abs(p1.x - p2.x) < 1:  # 垂直线
                                vertical_lines.append((p1, p2))
                        # 如果是元组或列表格式的坐标 (x, y)
                        elif isinstance(p1, (tuple, list)) and isinstance(p2, (tuple, list)) and len(p1) >= 2 and len(p2) >= 2:
                            if abs(p1[1] - p2[1]) < 1:  # 水平线 (y坐标)
                                horizontal_lines.append((p1, p2))
                            elif abs(p1[0] - p2[0]) < 1:  # 垂直线 (x坐标)
                                vertical_lines.append((p1, p2))
                    except (AttributeError, TypeError, IndexError):
                        # 如果无法访问坐标，跳过此线条
                        continue
        
        # 检测可能的表格区域
        table_bboxes = self._find_rectangular_areas(horizontal_lines, vertical_lines)
        
        for bbox in table_bboxes:
            table_area = {
                'type': 'table',
                'bbox': bbox,
                'horizontal_lines': horizontal_lines,
                'vertical_lines': vertical_lines
            }
            table_areas.append(table_area)
        
        return table_areas
    
    def _extract_block_text(self, block: Dict) -> str:
        """提取块中的文本"""
        texts = []
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                texts.append(span.get('text', ''))
        return ''.join(texts)
    
    def _get_image_bbox(self, page: fitz.Page, xref: int) -> tuple:
        """获取图片在页面上的边界框"""
        # 获取图片的引用信息
        try:
            img_dict = page.parent.extract_image(xref)
            # 这里简化处理，返回页面的大概位置
            # 实际应用中需要更精确的定位
            return (0, 0, 100, 100)  # 占位符，实际需要精确定位
        except:
            return (0, 0, 100, 100)
    
    def _find_rectangular_areas(self, h_lines: list, v_lines: list) -> List[tuple]:
        """查找矩形区域（表格候选区域）"""
        # 简化实现，查找密集的线条区域
        # 实际应用中需要更复杂的算法
        if h_lines or v_lines:  # 如果有线条存在
            return [(50, 50, 400, 300)]  # 返回一个示例区域
        return []  # 没有线条则返回空列表