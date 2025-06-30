import gradio as gr
import os
import re
import chardet # Import chardet
from ebooklib import epub
from tqdm import tqdm
import shutil
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

# --- Smart Chapter Parser Data Structures ---

@dataclass
class Chapter:
    """最终输出的章节结构"""
    title: str
    content: str

@dataclass
class PotentialChapter:
    """用于内部处理的候选章节结构"""
    title_text: str
    start_index: int
    end_index: int
    confidence_score: int
    pattern_type: str

    def __repr__(self):
        return f"'{self.title_text}' (Score: {self.confidence_score}, Pos: {self.start_index})"

# --- Smart Chapter Parser Class ---

class SmartChapterParser:
    """
    一个智能中文章节解析器，能够从纯文本中识别章节并提取内容。
    """

    def __init__(self,
                 min_chapter_distance: int = 50,
                 merge_title_distance: int = 25):
        """
        初始化解析器。
        :param min_chapter_distance: 两个章节标题之间的最小字符距离，用于过滤伪章节。
        :param merge_title_distance: 两行文字被视作同一标题的最大字符距离。
        """
        self.min_chapter_distance = min_chapter_distance
        self.merge_title_distance = merge_title_distance

        # 定义模式，按置信度从高到低排列
        self.patterns = [
            # 高置信度: 第X章/回/节/卷
            ("结构化模式", 100, re.compile(r"^\s*(第|卷)\s*[一二三四五六七八九十百千万零\d]+\s*[章回节卷].*$", re.MULTILINE)),
            # 中高置信度: 关键词
            ("关键词模式", 80, re.compile(r"^\s*(序|前言|引子|楔子|后记|番外|尾声|序章|序幕)\s*$", re.MULTILINE)),
            # 【更新】为处理 (一)少年 / (1) / （2）少年 / （卅五）赌船嬉戏 等格式，加入专用模式并提高其置信度
            ("全半角括号模式", 65, re.compile(r"^\s*[（(]\s*[一二三四五六七八九十百千万零廿卅卌\d]+\s*[)）]\s*.*$", re.MULTILINE)),
            # 中置信度: 普通序号列表（包含特殊中文数字简写）
            ("序号模式", 60, re.compile(r"^\s*[一二三四五六七八九十百千万廿卅卌\d]+\s*[、.．].*$", re.MULTILINE)),
            # 低置信度: 启发式短标题 - 加强过滤条件
            ("启发式模式", 30, re.compile(r"^\s*[^。\n！？]{1,15}\s*$", re.MULTILINE))
        ]
        
        # 定义排除模式，用于过滤明显不是章节的内容
        self.exclusion_patterns = [
            # 文件名和URL
            re.compile(r'.*\.(html?|htm|txt|doc|pdf|jpg|png|gif|css|js)$', re.IGNORECASE),
            # 纯数字或数字+文件扩展名
            re.compile(r'^\s*\d+(\.\w+)?\s*$'),
            # 包含URL特征
            re.compile(r'.*(http|www|\.com|\.cn|\.org).*', re.IGNORECASE),
            # 包含代码特征
            re.compile(r'.*[<>{}[\]();=&%#].*'),
            # 包含过多数字的行（如日期、ID等）
            re.compile(r'^\s*\d{4,}\s*$'),
            # HTML标签
            re.compile(r'<[^>]+>'),
            # 特殊符号开头
            re.compile(r'^\s*[*+\-=_~`]+\s*$'),
        ]

    def _preprocess(self, text: str) -> str:
        """文本预处理，规范化空白符。"""
        text = text.replace('　', ' ')
        return text

    def _scan_for_candidates(self, text: str) -> List[PotentialChapter]:
        """
        多模式扫描文本，生成所有可能的候选章节列表。
        """
        candidates = []
        for pattern_type, score, regex in self.patterns:
            for match in regex.finditer(text):
                title_text = match.group(0).strip()
                
                # 检查排除模式
                should_exclude = False
                for exclusion_pattern in self.exclusion_patterns:
                    if exclusion_pattern.match(title_text):
                        should_exclude = True
                        break
                
                if should_exclude:
                    continue
                
                if pattern_type == "启发式模式":
                    start_line = text.rfind('\n', 0, match.start()) + 1
                    end_line = text.find('\n', match.end())
                    if end_line == -1: end_line = len(text)
                    
                    prev_line = text[text.rfind('\n', 0, start_line-2)+1:start_line-1].strip()
                    next_line = text[end_line+1:text.find('\n', end_line+1)].strip()

                    if not (prev_line == "" and next_line == ""):
                        continue 
                    
                    # 对启发式模式进行额外检查
                    # 排除纯数字或过短的标题
                    if len(title_text) < 2 or title_text.isdigit():
                        continue
                    
                    # 排除只包含数字和标点的标题
                    if re.match(r'^[\d\s\.\-_]+$', title_text):
                        continue

                is_duplicate = False
                for cand in candidates:
                    if cand.start_index == match.start():
                        is_duplicate = True
                        break
                if not is_duplicate:
                    candidates.append(PotentialChapter(
                        title_text=title_text,
                        start_index=match.start(),
                        end_index=match.end(),
                        confidence_score=score,
                        pattern_type=pattern_type
                    ))
        return sorted(candidates, key=lambda x: x.start_index)
        
    def _filter_and_merge_candidates(self, candidates: List[PotentialChapter]) -> List[PotentialChapter]:
        """
        过滤、消歧和合并候选章节，这是算法的智能核心。
        """
        if not candidates:
            return []

        # 按置信度降序排序，优先保留高置信度的章节
        sorted_candidates = sorted(candidates, key=lambda x: (-x.confidence_score, x.start_index))
        
        final_candidates = []
        
        for current in sorted_candidates:
            should_add = True
            
            # 检查与已接受章节的距离
            for accepted in final_candidates:
                char_distance = abs(current.start_index - accepted.start_index)
                
                # 动态调整最小距离要求
                if current.confidence_score >= 80 and accepted.confidence_score >= 80:
                    # 高置信度章节之间允许更近的距离
                    min_distance = 15  
                elif current.confidence_score >= 60 and accepted.confidence_score >= 60:
                    # 中等置信度章节之间的距离
                    min_distance = 30
                else:
                    # 低置信度章节需要更大的距离
                    min_distance = self.min_chapter_distance
                
                if char_distance < min_distance:
                    should_add = False
                    break
            
            if should_add:
                final_candidates.append(current)
        
        # 按位置重新排序
        final_candidates.sort(key=lambda x: x.start_index)
        
        return final_candidates

    def _extract_content(self, text: str, chapters: List[PotentialChapter]) -> List[Chapter]:
        """
        根据最终的章节标记列表，切分文本并提取内容。
        """
        if not chapters:
            return [Chapter(title="全文", content=text.strip())]

        final_chapters = []
        
        first_chapter_start = chapters[0].start_index
        if first_chapter_start > 0:
            prologue_content = text[:first_chapter_start].strip()
            if prologue_content:
                final_chapters.append(Chapter(title="前言", content=prologue_content))

        for i in range(len(chapters)):
            current_chap = chapters[i]
            
            if i + 1 < len(chapters):
                next_chap_start = chapters[i+1].start_index
            else:
                next_chap_start = len(text)
                
            content_start = current_chap.end_index
            content = text[content_start:next_chap_start].strip()

            final_chapters.append(Chapter(title=current_chap.title_text, content=content))
            
        return final_chapters

    def parse(self, text: str) -> List[Chapter]:
        """
        执行完整的解析流程。
        :param text: 完整的文章纯文本。
        :return: 一个包含Chapter对象的列表。
        """
        processed_text = self._preprocess(text)
        candidates = self._scan_for_candidates(processed_text)
        final_chapter_markers = self._filter_and_merge_candidates(candidates)
        result = self._extract_content(processed_text, final_chapter_markers)
        return result

# --- Bilingual UI Text & Configuration ---
UI_TEXT = {
    "en": {
        "title": "TXT to EPUB Converter", "upload_label": "1. Select TXT File", "add_file_button": "Add File to List", "file_list_header": "Selected Files", "clear_all_button": "Clear All", "cleaning_label": "2. Cleaning Options",
        "merge_lines": "Merge Empty Lines", "remove_spaces": "Remove Extra Spaces", "chapter_detection_header": "3. Chapter Detection",
        "detection_mode": "Mode", "intelligent_mode": "Intelligent Detection", "smart_chinese_mode": "Smart Chinese Parser", "custom_regex_mode": "Custom Regex",
        "custom_rule_label": "Custom Regex Rule", "custom_rule_info": "Used when 'Custom Regex' mode is selected.",
        "preview_button": "Preview Detected Chapters", "author_label": "4. Author (Optional)", "cover_label": "5. Cover Image (Optional)",
        "output_header": "6. Output Location", "output_path_label": "Output Folder Path (Optional)",
        "output_path_info": "If blank, files are saved to an 'epub_output' folder.", "save_to_source": "Save to Source File Location",
        "start_button": "Start Conversion",
        "chapter_preview_header": "Chapter Preview", "file_content_preview_header": "File Content Preview", "results_header": "Results", "log_header": "Log", "version": "Version 0.1.4",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub Repository: https://github.com/cs2764/txt-to-epub", "no_files_selected": "No files selected. Please add TXT files to the list.", "files_count": "files selected", "remove": "Remove",
    },
    "zh": {
        "title": "TXT 转 EPUB 批量转换器", "upload_label": "1. 选择 TXT 文件", "add_file_button": "添加文件到列表", "file_list_header": "已选择的文件", "clear_all_button": "清空所有", "cleaning_label": "2. 清理选项",
        "merge_lines": "合并空行", "remove_spaces": "移除多余空格", "chapter_detection_header": "3. 章节检测",
        "detection_mode": "模式", "intelligent_mode": "智能检测", "smart_chinese_mode": "智能中文解析", "custom_regex_mode": "自定义正则表达式",
        "custom_rule_label": "自定义正则表达式规则", "custom_rule_info": "当选择\"自定义正则表达式\"模式时使用。",
        "preview_button": "预览检测到的章节", "author_label": "4. 作者（可选）", "cover_label": "5. 封面图片（可选）",
        "output_header": "6. 输出位置", "output_path_label": "输出文件夹路径（可选）",
        "output_path_info": "如果留空，文件将保存到 'epub_output' 文件夹中。", "save_to_source": "保存到源文件位置",
        "start_button": "开始转换",
        "chapter_preview_header": "章节预览", "file_content_preview_header": "文件内容预览", "results_header": "结果", "log_header": "日志", "version": "版本 0.1.4",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub 项目地址：https://github.com/cs2764/txt-to-epub", "no_files_selected": "未选择文件。请添加 TXT 文件到列表中。", "files_count": "个文件已选择", "remove": "删除",
    }
}

# --- Core Engine (No changes from previous version) ---
HEURISTIC_PATTERNS = [
    (re.compile(r"^\s*第\s*[0-9一二三四五六七八九十百千万]+\s*[章章节回]"), 30), (re.compile(r"^\s*卷\s*[0-9一二三四五六七八九十百千万]+"), 28),
    (re.compile(r"^\s*chapter\s*\d+", re.IGNORECASE), 25), (re.compile(r"^\s*#+"), 15),
    (re.compile(r"^\s*（[一二三四五六七八九十百千万]+\）.*"), 20), # New pattern for (一)Chapter Title
]
DISQUALIFYING_PATTERNS = [re.compile(r"[。？！""''(（)）—]"), re.compile(r'^("|\')'), re.compile(r"(\w{3,}\s){5,}")]

def clean_text(text, options, lang):
    if UI_TEXT[lang]["merge_lines"] in options:
        text = re.sub(r'\n\s*\n', '\n', text)
    if UI_TEXT[lang]["remove_spaces"] in options:
        text = '\n'.join(line.strip() for line in text.split('\n'))
    return text

def is_valid_chapter_candidate(line, text_len, line_pos):
    for pattern in DISQUALIFYING_PATTERNS:
        if pattern.search(line): return False
    if line_pos / text_len > 0.95: return False
    for pattern, _ in HEURISTIC_PATTERNS:
        if pattern.search(line): return True
    return False

def intelligent_chapter_detection(text):
    lines = text.split('\n')
    text_len = len(text)
    if text_len == 0: return [], None
    chapters = []
    line_positions = [m.start() for m in re.finditer(r'^.*$', text, re.MULTILINE)]
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue
        line_pos = line_positions[i]
        if is_valid_chapter_candidate(line, text_len, line_pos):
             is_preceded = (i == 0 or not lines[i-1].strip())
             is_followed = (i == len(lines) - 1 or not lines[i+1].strip())
             if is_preceded and is_followed:
                 chapters.append((line, line_pos))
    if not chapters:
        simple_pattern = re.compile(r"^\s*(chapter\s*\d+|第\s*\d+\s*章)", re.IGNORECASE | re.MULTILINE)
        chapters = [(m.group(0).strip(), m.start()) for m in simple_pattern.finditer(text)]
    return chapters, None

def smart_chinese_chapter_detection(text):
    """
    使用智能中文章节解析器进行章节检测
    """
    try:
        parser = SmartChapterParser()
        chapters = parser.parse(text)
        
        # 转换为现有程序期望的格式 (title, position)
        result_chapters = []
        
        # 重新解析原文以获取准确的章节位置
        processed_text = parser._preprocess(text)
        candidates = parser._scan_for_candidates(processed_text)
        final_chapter_markers = parser._filter_and_merge_candidates(candidates)
        
        # 如果有前言，先处理前言
        if chapters and chapters[0].title == "前言":
            result_chapters.append((chapters[0].title, 0))
            # 从第二个章节开始处理
            start_idx = 1
        else:
            start_idx = 0
        
        # 处理实际的章节标记
        for i, marker in enumerate(final_chapter_markers):
            chapter_idx = start_idx + i
            if chapter_idx < len(chapters):
                result_chapters.append((chapters[chapter_idx].title, marker.start_index))
        
        return result_chapters, None
    except Exception as e:
        return [], f"Smart Chinese parser error: {str(e)}"

def detect_chapters_from_custom_pattern(text, pattern_str):
    if not pattern_str: return [], "Custom pattern cannot be empty."
    try:
        pattern = re.compile(pattern_str, re.MULTILINE)
        return [(match.group(0).strip(), match.start()) for match in pattern.finditer(text)], None
    except re.error:
        return [], "Invalid Custom Regex Pattern."

def convert_to_epub(text, filename, author, cover_image_path, chapters):
    book = epub.EpubBook()
    book.set_identifier(os.path.basename(filename))
    book.set_title(os.path.splitext(os.path.basename(filename))[0])
    book.set_language('zh')
    if author: book.add_author(author)
    if cover_image_path and os.path.exists(cover_image_path):
        book.set_cover("cover.jpg", open(cover_image_path, 'rb').read())
    if not chapters: chapters = [("Content", 0)]
    book.toc = []
    book.spine = ['nav']
    for i, (title, start) in enumerate(chapters):
        end = chapters[i + 1][1] if i + 1 < len(chapters) else len(text)
        content_html = text[start:end].replace('\n', '<br/>')
        chapter_filename = f'chap_{i+1}.xhtml'
        c = epub.EpubHtml(title=title, file_name=chapter_filename, lang='zh_cn')
        c.content = f'<h1>{title}</h1>{content_html}'
        book.add_item(c)
        book.toc.append(epub.Link(chapter_filename, title, f'chap_{i+1}'))
        book.spine.append(c)
    book.add_item(epub.EpubNcx()); book.add_item(epub.EpubNav())
    return book

def process_files_and_convert(files, clean_options, detection_mode, custom_rule, author, cover_image, save_to_source, custom_path, lang_key):
    if not files: 
        error_msg = "Please add at least one TXT file to the list." if lang_key == "en" else "请至少添加一个 TXT 文件到列表中。"
        return [], error_msg, ""
    
    # Default output directory
    default_output_dir = custom_path if custom_path and os.path.isdir(custom_path) else os.path.join(os.getcwd(), "epub_output")
    
    logs = ""; results_data = []
    for file_obj in tqdm(files, desc="Converting files"):
        original_filename = os.path.basename(file_obj.name)
        
        # Determine output directory for this file
        if save_to_source:
            # Try to save to source file location
            source_dir = os.path.dirname(file_obj.name)
            try:
                # Test if we can write to the source directory
                test_path = os.path.join(source_dir, ".test_write_permission")
                with open(test_path, 'w') as test_file:
                    test_file.write("test")
                os.remove(test_path)
                output_dir = source_dir
                logs += f"Saving {original_filename} to source location: {source_dir}\n"
            except (OSError, PermissionError, IOError) as e:
                # Fallback to default directory if can't write to source
                output_dir = default_output_dir
                os.makedirs(output_dir, exist_ok=True)
                logs += f"Cannot write to source location for {original_filename} ({e}), using default: {output_dir}\n"
        else:
            output_dir = default_output_dir
            os.makedirs(output_dir, exist_ok=True)
            if not logs.startswith("Output directory:"):
                logs += f"Output directory: {output_dir}\n"
        
        try:
            # Enhanced encoding detection
            encoding, confidence, detection_method = detect_file_encoding(file_obj.name)
            
            logs += f"Detected encoding for {original_filename}: {encoding} (confidence: {confidence:.2f}, method: {detection_method})\n"

            with open(file_obj.name, 'r', encoding=encoding, errors='replace') as f:
                text = f.read()
            if clean_options: text = clean_text(text, clean_options, lang_key)
            if detection_mode == UI_TEXT[lang_key]["intelligent_mode"]:
                chapters, error_msg = intelligent_chapter_detection(text)
            elif detection_mode == UI_TEXT[lang_key]["smart_chinese_mode"]:
                chapters, error_msg = smart_chinese_chapter_detection(text)
            else:
                chapters, error_msg = detect_chapters_from_custom_pattern(text, custom_rule)
            if error_msg: logs += f"Error for {original_filename}: {error_msg}\n"
            epub_book = convert_to_epub(text, original_filename, author, cover_image, chapters)
            output_path = os.path.join(output_dir, f"{os.path.splitext(original_filename)[0]}.epub")
            epub.write_epub(output_path, epub_book)
            results_data.append([original_filename, output_path, "Success"])
            logs += f"Successfully converted {original_filename} to {output_path}\n"
        except Exception as e:
            logs += f"Failed to convert {original_filename}: {e}\n"
            results_data.append([original_filename, "", f"Failed: {e}"])
    return results_data, logs, ""

def preview_chapters(files, detection_mode, custom_rule, lang_key):
    if not files: 
        return "Upload a file to preview chapters." if lang_key == "en" else "请添加文件以预览章节。"
    try:
        # Handle file list properly - use first file for preview
        file_obj = files[0] if isinstance(files, list) and len(files) > 0 else files
        if not file_obj:
            return "No files in the list." if lang_key == "en" else "列表中没有文件。"
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        
        # Enhanced encoding detection
        encoding, confidence, detection_method = detect_file_encoding(file_path)

        preview_log = f"Detected encoding for {os.path.basename(file_path)}: {encoding} (confidence: {confidence:.2f}, method: {detection_method})\n"

        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            text = f.read()
        
        if detection_mode == UI_TEXT[lang_key]["intelligent_mode"]:
            chapters, error_msg = intelligent_chapter_detection(text)
        elif detection_mode == UI_TEXT[lang_key]["smart_chinese_mode"]:
            chapters, error_msg = smart_chinese_chapter_detection(text)
        else:
            chapters, error_msg = detect_chapters_from_custom_pattern(text, custom_rule)
        
        if error_msg: return f"Error: {error_msg}"
        if chapters: 
            chapter_list = "\n".join([f"- {c[0]}" for c in chapters])
            return f"Detected Chapters ({len(chapters)} found):\n{chapter_list}"
        return "No chapters detected."
    except Exception as e:
        return f"Error reading file: {str(e)}"

# --- Enhanced Encoding Detection Function ---
def detect_file_encoding(file_path):
    """
    增强的文件编码检测函数，支持多种检测方法
    """
    # Common encodings to try in order
    common_encodings = [
        'utf-8-sig',  # UTF-8 with BOM
        'utf-8',      # UTF-8
        'gbk',        # Chinese GBK
        'gb2312',     # Chinese GB2312
        'cp936',      # Chinese CP936 (similar to GBK)
        'big5',       # Traditional Chinese Big5
        'ascii',      # ASCII
        'utf-16',     # UTF-16
        'utf-32',     # UTF-32
    ]
    
    try:
        with open(file_path, 'rb') as f:
            # Read more data for better detection (up to 64KB)
            raw_data = f.read(65536)
        
        # Check for BOM first
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig', 1.0, 'BOM detected'
        elif raw_data.startswith(b'\xff\xfe'):
            return 'utf-16-le', 1.0, 'BOM detected'
        elif raw_data.startswith(b'\xfe\xff'):
            return 'utf-16-be', 1.0, 'BOM detected'
        elif raw_data.startswith(b'\xff\xfe\x00\x00'):
            return 'utf-32-le', 1.0, 'BOM detected'
        elif raw_data.startswith(b'\x00\x00\xfe\xff'):
            return 'utf-32-be', 1.0, 'BOM detected'
        
        # Use chardet for detection
        detection = chardet.detect(raw_data)
        detected_encoding = detection.get('encoding', '').lower()
        confidence = detection.get('confidence', 0.0)
        
        # If confidence is high enough, use detected encoding
        if confidence > 0.7 and detected_encoding:
            return detected_encoding, confidence, 'chardet'
        
        # Try common encodings and pick the one that works best
        best_encoding = None
        best_score = 0
        best_method = 'fallback'
        
        for encoding in common_encodings:
            try:
                decoded_text = raw_data.decode(encoding)
                # Score based on Chinese characters and readable content
                chinese_chars = sum(1 for c in decoded_text if '\u4e00' <= c <= '\u9fff')
                total_chars = len(decoded_text)
                
                if total_chars > 0:
                    chinese_ratio = chinese_chars / total_chars
                    # Higher score for files with Chinese content
                    score = chinese_ratio * 2 + 0.5  # Base score
                    
                    if score > best_score:
                        best_score = score
                        best_encoding = encoding
                        best_method = 'pattern_match'
                        
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If we found a good encoding, use it
        if best_encoding:
            return best_encoding, best_score, best_method
        
        # Last resort: use chardet result or utf-8
        return detected_encoding or 'utf-8', confidence, 'last_resort'
        
    except Exception as e:
        return 'utf-8', 0.0, f'error: {str(e)}'

# --- File Management Functions ---
def add_file_to_list(new_file, current_files, lang_key):
    """
    添加文件到文件列表
    """
    if not new_file:
        return current_files, format_file_list(current_files, lang_key), update_file_preview_for_list(current_files, lang_key)
    
    # 初始化文件列表
    if not current_files:
        current_files = []
    
    # 检查文件是否已存在
    new_file_path = new_file.name if hasattr(new_file, 'name') else str(new_file)
    for existing_file in current_files:
        existing_path = existing_file.name if hasattr(existing_file, 'name') else str(existing_file)
        if os.path.basename(new_file_path) == os.path.basename(existing_path):
            # 文件已存在，不重复添加
            return current_files, format_file_list(current_files, lang_key), update_file_preview_for_list(current_files, lang_key)
    
    # 添加新文件
    current_files.append(new_file)
    return current_files, format_file_list(current_files, lang_key), update_file_preview_for_list(current_files, lang_key)

def remove_file_from_list(file_index, current_files, lang_key):
    """
    从文件列表中删除指定的文件
    """
    if not current_files or file_index < 0 or file_index >= len(current_files):
        return current_files, format_file_list(current_files, lang_key)
    
    current_files.pop(file_index)
    return current_files, format_file_list(current_files, lang_key)

def clear_all_files(lang_key):
    """
    清空所有文件
    """
    return [], format_file_list([], lang_key), update_file_preview_for_list([], lang_key)

def format_file_list(files, lang_key):
    """
    格式化文件列表显示
    """
    if not files:
        return UI_TEXT[lang_key]["no_files_selected"]
    
    file_count = len(files)
    if lang_key == "en":
        header = f"**{file_count} {UI_TEXT[lang_key]['files_count']}**\n\n"
    else:
        header = f"**{file_count} {UI_TEXT[lang_key]['files_count']}**\n\n"
    
    file_lines = []
    for i, file_obj in enumerate(files):
        filename = os.path.basename(file_obj.name) if hasattr(file_obj, 'name') else str(file_obj)
        file_size = os.path.getsize(file_obj.name) if hasattr(file_obj, 'name') and os.path.exists(file_obj.name) else 0
        size_str = f"{file_size:,} bytes" if lang_key == "en" else f"{file_size:,} 字节"
        file_lines.append(f"{i+1}. **{filename}** ({size_str})")
    
    return header + "\n".join(file_lines)

def update_file_preview_for_list(files, lang_key):
    """
    为文件列表更新预览内容（显示第一个文件的预览）
    """
    if not files:
        return UI_TEXT[lang_key]["no_files_selected"]
    
    return preview_file_content(files, lang_key)

# --- NEW: File Content Preview Function ---
def preview_file_content(files, lang_key):
    """
    预览文件的前10行内容，使用增强的编码检测
    """
    if not files: 
        return "Please upload a file to preview content." if lang_key == "en" else "请上传文件以预览内容。"
    
    try:
        # Handle file object properly
        file_obj = files[0] if isinstance(files, list) else files
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        
        # Enhanced encoding detection
        encoding, confidence, detection_method = detect_file_encoding(file_path)
        
        # Read and preview file content with detected encoding
        lines = []
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                for i, line in enumerate(f):
                    if i >= 10:  # Only read first 10 lines
                        break
                    lines.append(line.rstrip())
        except Exception as read_error:
            # Fallback to utf-8 with error replacement
            encoding = 'utf-8'
            detection_method = 'fallback_utf8'
            confidence = 0.0
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    lines.append(line.rstrip())
        
        # Create detailed preview header
        if lang_key == "en":
            preview_header = (
                f"**File**: {filename}\n"
                f"**Size**: {file_size:,} bytes\n"
                f"**Encoding**: {encoding} (confidence: {confidence:.2f}, method: {detection_method})\n"
                f"\n**Preview (First 10 lines):**\n"
            )
            more_content = f"\n\n*(File contains more content beyond these 10 lines)*" if len(lines) == 10 else ""
        else:
            preview_header = (
                f"**文件**: {filename}\n"
                f"**大小**: {file_size:,} 字节\n"
                f"**编码**: {encoding} (置信度: {confidence:.2f}, 检测方法: {detection_method})\n"
                f"\n**预览 (前10行):**\n"
            )
            more_content = f"\n\n*(文件包含更多内容，超出这10行)*" if len(lines) == 10 else ""
        
        # Format the preview with line numbers and handle empty lines
        preview_lines = []
        for i, line in enumerate(lines, 1):
            display_line = line if line.strip() else '(空行)'
            preview_lines.append(f"{i:2d}: {display_line}")
        
        # Add warning for low confidence
        warning = ""
        if confidence < 0.5 and lang_key == "zh":
            warning = "\n⚠️ **注意**: 编码检测置信度较低，如果显示乱码，文件可能使用了其他编码格式。"
        elif confidence < 0.5 and lang_key == "en":
            warning = "\n⚠️ **Warning**: Low encoding detection confidence. If text appears garbled, the file may use a different encoding."
        
        preview_content = preview_header + "\n".join(preview_lines) + more_content + warning
        
        return preview_content
        
    except Exception as e:
        error_msg = f"Error reading file: {str(e)}" if lang_key == "en" else f"读取文件错误: {str(e)}"
        return error_msg

# --- UI Creation Function ---
def create_ui(lang_key):
    LANG = UI_TEXT[lang_key]
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky")) as demo:
        # Language switcher is now a state component
        lang_state = gr.State(value=lang_key)
        # File list state to store selected files
        file_list_state = gr.State(value=[])

        with gr.Row():
            gr.Markdown(f"# {LANG['title']}")
            lang_radio = gr.Radio(["en", "zh"], label=LANG["lang_select"], value=lang_key, interactive=True)
        
        with gr.Row():
            with gr.Column(scale=2):
                # File selection section
                file_input = gr.File(label=LANG["upload_label"], file_count="single", file_types=[".txt"])
                with gr.Row():
                    add_file_button = gr.Button(LANG["add_file_button"], variant="secondary")
                    clear_all_button = gr.Button(LANG["clear_all_button"], variant="secondary")
                
                # File list display
                file_list_display = gr.Markdown(LANG["no_files_selected"], label=LANG["file_list_header"])
                
                cleaning_options = gr.CheckboxGroup([LANG["merge_lines"], LANG["remove_spaces"]], label=LANG["cleaning_label"], value=[LANG["merge_lines"], LANG["remove_spaces"]])
                gr.Markdown(f"### {LANG['chapter_detection_header']}")
                detection_mode = gr.Radio([LANG["intelligent_mode"], LANG["smart_chinese_mode"], LANG["custom_regex_mode"]], label=LANG["detection_mode"], value=LANG["intelligent_mode"])
                custom_rule_input = gr.Textbox(label=LANG["custom_rule_label"], info=LANG["custom_rule_info"], visible=False)
                preview_button = gr.Button(LANG["preview_button"])
                author_input = gr.Textbox(label=LANG["author_label"])
                cover_image_input = gr.Image(label=LANG["cover_label"], type="filepath")
                gr.Markdown(f"### {LANG['output_header']}")
                save_to_source_checkbox = gr.Checkbox(label=LANG["save_to_source"], value=False)
                custom_path_input = gr.Textbox(label=LANG["output_path_label"], info=LANG["output_path_info"])
                start_button = gr.Button(LANG["start_button"], variant="primary")
            with gr.Column(scale=3):
                # NEW: File Content Preview
                file_content_preview_output = gr.Markdown(label=LANG["file_content_preview_header"])
                chapter_preview_output = gr.Markdown(label=LANG["chapter_preview_header"])
                results_output = gr.Dataframe(headers=["Source File", "Output Path", "Status"], label=LANG["results_header"], row_count=10)
                log_output = gr.Textbox(label=LANG["log_header"], lines=15, interactive=False)
        gr.Markdown("---")
        version_info = gr.Markdown(LANG["version"])
        github_info = gr.Markdown(LANG["github_link"])

        # --- Event Handlers ---
        detection_mode.change(lambda x: gr.update(visible=x == LANG["custom_regex_mode"]), detection_mode, custom_rule_input)
        
        # File management event handlers
        add_file_button.click(
            fn=add_file_to_list,
            inputs=[file_input, file_list_state, lang_state],
            outputs=[file_list_state, file_list_display, file_content_preview_output]
        )
        
        clear_all_button.click(
            fn=clear_all_files,
            inputs=[lang_state],
            outputs=[file_list_state, file_list_display, file_content_preview_output]
        )
        
        # Note: Removed file_list_state.change() as it's not supported in Gradio 3.50.2
        # File preview will be updated through add_file and clear_all functions
        
        start_button.click(
            fn=process_files_and_convert,
            inputs=[file_list_state, cleaning_options, detection_mode, custom_rule_input, author_input, cover_image_input, save_to_source_checkbox, custom_path_input, lang_state],
            outputs=[results_output, log_output, chapter_preview_output]
        )
        preview_button.click(
            fn=preview_chapters,
            inputs=[file_list_state, detection_mode, custom_rule_input, lang_state],
            outputs=chapter_preview_output
        )
        
        # The magic for language switching: re-render the UI on change
        # This is a bit of a hack, but it's the standard way in Gradio
        # It works by updating every single component with its new label from the language dict
        components_to_update = [
            file_input, add_file_button, clear_all_button, file_list_display, cleaning_options, detection_mode, custom_rule_input, preview_button,
            author_input, cover_image_input, save_to_source_checkbox, custom_path_input, start_button,
            file_content_preview_output, chapter_preview_output, results_output, log_output, version_info, github_info
        ]
        
        def update_lang_func(lang_key_new):
            NEW_LANG = UI_TEXT[lang_key_new]
            return (
                lang_key_new, # Update the state
                gr.update(label=NEW_LANG["upload_label"]),
                gr.update(value=NEW_LANG["add_file_button"]),
                gr.update(value=NEW_LANG["clear_all_button"]),
                gr.update(label=NEW_LANG["file_list_header"], value=NEW_LANG["no_files_selected"]),
                gr.update(label=NEW_LANG["cleaning_label"], choices=[NEW_LANG["merge_lines"], NEW_LANG["remove_spaces"]], value=[NEW_LANG["merge_lines"], NEW_LANG["remove_spaces"]]),
                gr.update(label=NEW_LANG["detection_mode"], choices=[NEW_LANG["intelligent_mode"], NEW_LANG["smart_chinese_mode"], NEW_LANG["custom_regex_mode"]]),
                gr.update(label=NEW_LANG["custom_rule_label"], info=NEW_LANG["custom_rule_info"]),
                gr.update(value=NEW_LANG["preview_button"]),
                gr.update(label=NEW_LANG["author_label"]),
                gr.update(label=NEW_LANG["cover_label"]),
                gr.update(label=NEW_LANG["save_to_source"]),
                gr.update(label=NEW_LANG["output_path_label"], info=NEW_LANG["output_path_info"]),
                gr.update(value=NEW_LANG["start_button"]),
                gr.update(label=NEW_LANG["file_content_preview_header"]),
                gr.update(label=NEW_LANG["chapter_preview_header"]),
                gr.update(label=NEW_LANG["results_header"]),
                gr.update(label=NEW_LANG["log_header"]),
                gr.update(value=NEW_LANG["version"]),
                gr.update(value=NEW_LANG["github_link"]),
            )

        lang_radio.change(
            fn=update_lang_func,
            inputs=lang_radio,
            outputs=[lang_state] + components_to_update
        )
    return demo

if __name__ == "__main__":
    app = create_ui("zh") # Start with Chinese as default
    print("🚀 Starting TXT to EPUB Converter...")
    print("📍 Local access: http://localhost:7860")
    print("🌐 Network access: http://0.0.0.0:7860")
    print("⚠️  Using local server for better stability")
    app.launch(inbrowser=True, server_name="0.0.0.0", share=False)