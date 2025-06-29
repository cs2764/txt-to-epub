import gradio as gr
import os
import re
from ebooklib import epub
from tqdm import tqdm
import shutil
import numpy as np

# --- Bilingual UI Text & Configuration ---
UI_TEXT = {
    "en": {
        "title": "TXT to EPUB Converter", "upload_label": "1. Upload TXT Files", "cleaning_label": "2. Cleaning Options",
        "merge_lines": "Merge Empty Lines", "remove_spaces": "Remove Extra Spaces", "chapter_detection_header": "3. Chapter Detection",
        "detection_mode": "Mode", "intelligent_mode": "Intelligent Detection", "custom_regex_mode": "Custom Regex",
        "custom_rule_label": "Custom Regex Rule", "custom_rule_info": "Used when 'Custom Regex' mode is selected.",
        "preview_button": "Preview Detected Chapters", "author_label": "4. Author (Optional)", "cover_label": "5. Cover Image (Optional)",
        "output_header": "6. Output Location", "output_path_label": "Output Folder Path (Optional)",
        "output_path_info": "If blank, files are saved to an 'epub_output' folder.", "save_to_source": "Save to Source File Location",
        "start_button": "Start Conversion",
        "chapter_preview_header": "Chapter Preview", "results_header": "Results", "log_header": "Log", "version": "Version 0.1.2",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub Repository: https://github.com/cs2764/txt-to-epub",
    },
    "zh": {
        "title": "TXT 转 EPUB 批量转换器", "upload_label": "1. 上传 TXT 文件", "cleaning_label": "2. 清理选项",
        "merge_lines": "合并空行", "remove_spaces": "移除多余空格", "chapter_detection_header": "3. 章节检测",
        "detection_mode": "模式", "intelligent_mode": "智能检测", "custom_regex_mode": "自定义正则表达式",
        "custom_rule_label": "自定义正则表达式规则", "custom_rule_info": "当选择“自定义正则表达式”模式时使用。",
        "preview_button": "预览检测到的章节", "author_label": "4. 作者（可选）", "cover_label": "5. 封面图片（可选）",
        "output_header": "6. 输出位置", "output_path_label": "输出文件夹路径（可选）",
        "output_path_info": "如果留空，文件将保存到 'epub_output' 文件夹中。", "save_to_source": "保存到源文件位置",
        "start_button": "开始转换",
        "chapter_preview_header": "章节预览", "results_header": "结果", "log_header": "日志", "version": "版本 0.1.2",
        "lang_select": "Language / 语言", "github_link": "📦 GitHub 项目地址：https://github.com/cs2764/txt-to-epub",
    }
}

# --- Core Engine (No changes from previous version) ---
HEURISTIC_PATTERNS = [
    (re.compile(r"^\s*第\s*[0-9一二三四五六七八九十百千万]+\s*[章章节回]"), 30), (re.compile(r"^\s*卷\s*[0-9一二三四五六七八九十百千万]+"), 28),
    (re.compile(r"^\s*chapter\s*\d+", re.IGNORECASE), 25), (re.compile(r"^\s*#+"), 15),
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
            with open(file_obj.name, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
            if clean_options: text = clean_text(text, clean_options, lang_key)
            if detection_mode == UI_TEXT[lang_key]["intelligent_mode"]:
                chapters, error_msg = intelligent_chapter_detection(text)
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
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: 
            text = f.read()
        
        if detection_mode == UI_TEXT[lang_key]["intelligent_mode"]:
            chapters, error_msg = intelligent_chapter_detection(text)
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
                detection_mode = gr.Radio([LANG["intelligent_mode"], LANG["custom_regex_mode"]], label=LANG["detection_mode"], value=LANG["intelligent_mode"])
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
                gr.update(label=NEW_LANG["detection_mode"], choices=[NEW_LANG["intelligent_mode"], NEW_LANG["custom_regex_mode"]]),
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

if __name__ == "__main__":
    app = create_ui("zh") # Start with Chinese as default
    print("🚀 Starting TXT to EPUB Converter...")
    print("📍 Local access: http://localhost:7860")
    print("🌐 Network access: http://0.0.0.0:7860")
    print("⚠️  Using local server for better stability")
    app.launch(inbrowser=True, server_name="0.0.0.0", share=False)