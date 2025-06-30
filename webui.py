import gradio as gr
import os
import re
import chardet # Import chardet
from ebooklib import epub
from tqdm import tqdm
import shutil
import numpy as np
import socket
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
        "title": "TXT to EPUB Converter", "upload_label": "1. Upload TXT Files", "cleaning_label": "2. Cleaning Options",
        "merge_lines": "Merge Empty Lines", "remove_spaces": "Remove Extra Spaces", "chapter_detection_header": "3. Chapter Detection",
        "detection_mode": "Mode", "intelligent_mode": "Intelligent Detection", "smart_chinese_mode": "Smart Chinese Parser", "custom_regex_mode": "Custom Regex",
        "custom_rule_label": "Custom Regex Rule", "custom_rule_info": "Used when 'Custom Regex' mode is selected.",
        "preview_button": "Preview Detected Chapters", "author_label": "4. Author (Optional)", "cover_label": "5. Cover Image (Optional)",
        "output_header": "6. Output Location", "output_path_label": "Output Folder Path (Optional)",
        "output_path_info": "If blank, files are saved to an 'epub_output' folder.", "save_to_source": "Save to Source File Location",
        "start_button": "Start Conversion",
        "chapter_preview_header": "Chapter Preview", "results_header": "Results", "log_header": "Log", "version": "Version 0.1.3",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub Repository: https://github.com/cs2764/txt-to-epub",
    },
    "zh": {
        "title": "TXT 转 EPUB 批量转换器", "upload_label": "1. 上传 TXT 文件", "cleaning_label": "2. 清理选项",
        "merge_lines": "合并空行", "remove_spaces": "移除多余空格", "chapter_detection_header": "3. 章节检测",
        "detection_mode": "模式", "intelligent_mode": "智能检测", "smart_chinese_mode": "智能中文解析", "custom_regex_mode": "自定义正则表达式",
        "custom_rule_label": "自定义正则表达式规则", "custom_rule_info": "当选择“自定义正则表达式”模式时使用。",
        "preview_button": "预览检测到的章节", "author_label": "4. 作者（可选）", "cover_label": "5. 封面图片（可选）",
        "output_header": "6. 输出位置", "output_path_label": "输出文件夹路径（可选）",
        "output_path_info": "如果留空，文件将保存到 'epub_output' 文件夹中。", "save_to_source": "保存到源文件位置",
        "start_button": "开始转换",
        "chapter_preview_header": "章节预览", "results_header": "结果", "log_header": "日志", "version": "版本 0.1.3",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub 项目地址：https://github.com/cs2764/txt-to-epub",
    }
}

# --- Core Engine (No changes from previous version) ---
HEURISTIC_PATTERNS = [
    (re.compile(r"^\s*第\s*[0-9一二三四五六七八九十百千万]+\s*[章章节回]"), 30), (re.compile(r"^\s*卷\s*[0-9一二三四五六七八九十百千万]+"), 28),
    (re.compile(r"^\s*chapter\s*\d+", re.IGNORECASE), 25), (re.compile(r"^\s*#+"), 15),
    (re.compile(r"^\s*（[一二三四五六七八九十百千万]+\）.*"), 20), # New pattern for (一)Chapter Title
]
DISQUALIFYING_PATTERNS = [re.compile(r"[。？！“”‘’(（)）—]"), re.compile(r"^(“|‘)"), re.compile(r"(\w{3,}\s){5,}")]

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
    if not files: return [], "Please upload at least one TXT file.", ""
    
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
            # Detect encoding
            with open(file_obj.name, 'rb') as f:
                raw_data = f.read()
            detection = chardet.detect(raw_data)
            encoding = detection['encoding'] if detection['encoding'] else 'utf-8' # Default to utf-8 if detection fails
            
            logs += f"Detected encoding for {original_filename}: {encoding} (confidence: {detection['confidence']:.2f})\n"

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
    if not files: return "Upload a file to preview chapters."
    try:
        # Handle file object properly
        file_obj = files[0] if isinstance(files, list) else files
        file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
        
        # Detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        detection = chardet.detect(raw_data)
        encoding = detection['encoding'] if detection['encoding'] else 'utf-8' # Default to utf-8 if detection fails

        preview_log = f"Detected encoding for {os.path.basename(file_path)}: {encoding} (confidence: {detection['confidence']:.2f})\n"

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

# --- UI Creation Function ---
def create_ui(lang_key):
    LANG = UI_TEXT[lang_key]
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky")) as demo:
        # Language switcher is now a state component
        lang_state = gr.State(value=lang_key)

        with gr.Row():
            gr.Markdown(f"# {LANG['title']}")
            lang_radio = gr.Radio(["en", "zh"], label=LANG["lang_select"], value=lang_key, interactive=True)
        
        with gr.Row():
            with gr.Column(scale=2):
                file_input = gr.File(label=LANG["upload_label"], file_count="multiple", file_types=[".txt"])
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
                chapter_preview_output = gr.Markdown(label=LANG["chapter_preview_header"])
                results_output = gr.Dataframe(headers=["Source File", "Output Path", "Status"], label=LANG["results_header"], row_count=10)
                log_output = gr.Textbox(label=LANG["log_header"], lines=15, interactive=False)
        gr.Markdown("---")
        version_info = gr.Markdown(LANG["version"])
        github_info = gr.Markdown(LANG["github_link"])

        # --- Event Handlers ---
        detection_mode.change(lambda x: gr.update(visible=x == LANG["custom_regex_mode"]), detection_mode, custom_rule_input)
        start_button.click(
            fn=process_files_and_convert,
            inputs=[file_input, cleaning_options, detection_mode, custom_rule_input, author_input, cover_image_input, save_to_source_checkbox, custom_path_input, lang_state],
            outputs=[results_output, log_output, chapter_preview_output]
        )
        preview_button.click(
            fn=preview_chapters,
            inputs=[file_input, detection_mode, custom_rule_input, lang_state],
            outputs=chapter_preview_output
        )
        
        # The magic for language switching: re-render the UI on change
        # This is a bit of a hack, but it's the standard way in Gradio
        # It works by updating every single component with its new label from the language dict
        components_to_update = [
            file_input, cleaning_options, detection_mode, custom_rule_input, preview_button,
            author_input, cover_image_input, save_to_source_checkbox, custom_path_input, start_button,
            chapter_preview_output, results_output, log_output, version_info, github_info
        ]
        
        def update_lang_func(lang_key_new):
            NEW_LANG = UI_TEXT[lang_key_new]
            return (
                lang_key_new, # Update the state
                gr.update(label=NEW_LANG["upload_label"]),
                gr.update(label=NEW_LANG["cleaning_label"], choices=[NEW_LANG["merge_lines"], NEW_LANG["remove_spaces"]], value=[NEW_LANG["merge_lines"], NEW_LANG["remove_spaces"]]),
                gr.update(label=NEW_LANG["detection_mode"], choices=[NEW_LANG["intelligent_mode"], NEW_LANG["smart_chinese_mode"], NEW_LANG["custom_regex_mode"]]),
                gr.update(label=NEW_LANG["custom_rule_label"], info=NEW_LANG["custom_rule_info"]),
                gr.update(value=NEW_LANG["preview_button"]),
                gr.update(label=NEW_LANG["author_label"]),
                gr.update(label=NEW_LANG["cover_label"]),
                gr.update(label=NEW_LANG["save_to_source"]),
                gr.update(label=NEW_LANG["output_path_label"], info=NEW_LANG["output_path_info"]),
                gr.update(value=NEW_LANG["start_button"]),
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

def is_port_in_use(port, host="0.0.0.0"):
    """检查指定端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return True

def find_available_port(start_port=7860, max_attempts=10):
    """从指定端口开始寻找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        if not is_port_in_use(port):
            return port
    return None

def launch_app_with_port_detection():
    """启动应用并自动检测可用端口"""
    app = create_ui("zh")  # Start with Chinese as default
    
    print("🚀 Starting TXT to EPUB Converter...")
    
    # 尝试找到可用端口
    available_port = find_available_port(7860, 10)
    
    if available_port is None:
        print("❌ Error: Could not find an available port (tried 7860-7869)")
        print("💡 Please close other applications using these ports and try again.")
        return
    
    if available_port != 7860:
        print(f"⚠️  Port 7860 is in use, using port {available_port} instead")
    
    print(f"📍 Local access: http://localhost:{available_port}")
    print(f"🌐 Network access: http://0.0.0.0:{available_port}")
    print("⚠️  Using local server for better stability")
    
    try:
        app.launch(
            inbrowser=True, 
            server_name="0.0.0.0", 
            server_port=available_port,
            share=False
        )
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")
        print("💡 Please check if the port is available and try again.")

if __name__ == "__main__":
    launch_app_with_port_detection()