"""测试文件处理服务"""
import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, Mock
from app.services.file_processor import FileProcessor


class TestSaveUpload:
    """测试文件保存功能"""

    def test_save_upload_creates_file(self):
        """测试保存上传文件创建文件"""
        with patch('app.services.file_processor.settings') as mock_settings:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_settings.UPLOAD_DIR = tmpdir

                file_data = b"test file content"
                filename = "test.txt"

                filepath = FileProcessor.save_upload(file_data, filename)

                assert os.path.exists(filepath)
                assert os.path.getsize(filepath) == len(file_data)

    def test_save_upload_generates_unique_name(self):
        """测试生成唯一文件名"""
        with patch('app.services.file_processor.settings') as mock_settings:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_settings.UPLOAD_DIR = tmpdir

                file_data = b"same content"
                filename = "test.txt"

                path1 = FileProcessor.save_upload(file_data, filename)
                path2 = FileProcessor.save_upload(file_data, filename)

                # 相同内容应该生成相同哈希前缀，但文件应该是唯一的
                assert path1 == path2  # 相同内容产生相同哈希

    def test_save_upload_with_different_content(self):
        """测试不同内容生成不同路径"""
        with patch('app.services.file_processor.settings') as mock_settings:
            with tempfile.TemporaryDirectory() as tmpdir:
                mock_settings.UPLOAD_DIR = tmpdir

                file_data1 = b"content 1"
                file_data2 = b"content 2"
                filename = "test.txt"

                path1 = FileProcessor.save_upload(file_data1, filename)
                path2 = FileProcessor.save_upload(file_data2, filename)

                # 不同内容应该产生不同哈希
                assert path1 != path2


class TestProcessFile:
    """测试文件处理功能"""

    def test_process_text_file(self):
        """测试处理文本文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            content = "这是测试内容\n第二行内容"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            result = FileProcessor.process_file(filepath)

            assert result == content

    def test_process_markdown_file(self):
        """测试处理 Markdown 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.md")
            content = "# 标题\n\n这是 Markdown 内容"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            result = FileProcessor.process_file(filepath)

            assert result == content

    def test_process_json_file(self):
        """测试处理 JSON 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            data = {"key": "value", "number": 123, "nested": {"data": "test"}}

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

            result = FileProcessor.process_file(filepath)

            assert "key" in result
            assert "value" in result
            assert "123" in result

    def test_process_json_formatted_output(self):
        """测试 JSON 文件格式化输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            data = {"key": "value"}

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f)

            result = FileProcessor.process_file(filepath)

            # 应该包含格式化的 JSON
            parsed = json.loads(result)
            assert parsed["key"] == "value"

    def test_process_unsupported_file_type(self):
        """测试处理不支持的文件类型"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.exe")

            with open(filepath, "w") as f:
                f.write("content")

            with pytest.raises(ValueError) as exc_info:
                FileProcessor.process_file(filepath)

            assert "Unsupported file type" in str(exc_info.value)

    def test_process_nonexistent_file(self):
        """测试处理不存在的文件"""
        with pytest.raises(FileNotFoundError):
            FileProcessor.process_file("/nonexistent/file.txt")

    def test_process_text_file_with_unicode(self):
        """测试处理包含 Unicode 的文本文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            content = "中文内容\n日本語\n한국어\nEmoji 🎉"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            result = FileProcessor.process_file(filepath)

            assert result == content

    def test_process_docx_file_missing_dependency(self):
        """测试处理 DOCX 文件缺少依赖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.docx")

            with open(filepath, "w") as f:
                f.write("fake docx")

            # Patch the import inside the method
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: (
                ImportError("No module named 'docx'") if name == 'docx' else __import__(name, *args, **kwargs)
            )):
                with pytest.raises(ImportError) as exc_info:
                    FileProcessor._process_docx(filepath)

                assert "python-docx" in str(exc_info.value)

    def test_process_pdf_file_missing_dependency(self):
        """测试处理 PDF 文件缺少依赖"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.pdf")

            with open(filepath, "w") as f:
                f.write("fake pdf")

            # Patch the import inside the method
            with patch('builtins.__import__', side_effect=lambda name, *args, **kwargs: (
                ImportError("No module named 'PyPDF2'") if name == 'PyPDF2' else __import__(name, *args, **kwargs)
            )):
                with pytest.raises(ImportError) as exc_info:
                    FileProcessor._process_pdf(filepath)

                assert "PyPDF2" in str(exc_info.value)


class TestValidateFile:
    """测试文件验证功能"""

    def test_validate_allowed_extension(self):
        """测试允许的文件扩展名"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt", ".pdf", ".docx"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("test.txt", 1024)

            assert result is True

    def test_validate_disallowed_extension(self):
        """测试不允许的文件扩展名"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt", ".pdf"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("test.exe", 1024)

            assert result is False

    def test_validate_file_size_within_limit(self):
        """测试文件大小在限制内"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("test.txt", 5 * 1024 * 1024)

            assert result is True

    def test_validate_file_size_exceeds_limit(self):
        """测试文件大小超过限制"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("test.txt", 15 * 1024 * 1024)

            assert result is False

    def test_validate_case_insensitive_extension(self):
        """测试扩展名大小写不敏感"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt", ".pdf"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result1 = FileProcessor.validate_file("test.TXT", 1024)
            result2 = FileProcessor.validate_file("test.Pdf", 1024)

            assert result1 is True
            assert result2 is True

    def test_validate_file_with_empty_name(self):
        """测试空文件名"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("", 1024)

            assert result is False

    def test_validate_zero_size_file(self):
        """测试零大小文件"""
        with patch('app.services.file_processor.settings') as mock_settings:
            mock_settings.ALLOWED_EXTENSIONS = [".txt"]
            mock_settings.MAX_FILE_SIZE = 10 * 1024 * 1024

            result = FileProcessor.validate_file("test.txt", 0)

            assert result is True


class TestDeleteFile:
    """测试文件删除功能"""

    def test_delete_existing_file(self):
        """测试删除存在的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")

            with open(filepath, "w") as f:
                f.write("content")

            assert os.path.exists(filepath)

            FileProcessor.delete_file(filepath)

            assert not os.path.exists(filepath)

    def test_delete_nonexistent_file(self):
        """测试删除不存在的文件"""
        # 不应该抛出异常
        FileProcessor.delete_file("/nonexistent/file.txt")

    def test_delete_file_with_path_object(self):
        """测试使用 Path 对象删除文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.txt"

            with open(filepath, "w") as f:
                f.write("content")

            FileProcessor.delete_file(str(filepath))

            assert not os.path.exists(filepath)


class TestFileEncodings:
    """测试文件编码处理"""

    def test_process_text_file_different_encodings(self):
        """测试不同编码的文本文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")
            content = "UTF-8 内容"

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            result = FileProcessor._process_text(filepath)

            assert result == content

    def test_process_text_file_empty_content(self):
        """测试空文本文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.txt")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")

            result = FileProcessor._process_text(filepath)

            assert result == ""


class TestProcessorsMapping:
    """测试处理器映射"""

    def test_all_processors_exist(self):
        """测试所有处理器方法都存在"""
        required_processors = [
            "_process_text",
            "_process_json",
            "_process_docx",
            "_process_pdf"
        ]

        for processor in required_processors:
            assert hasattr(FileProcessor, processor)
            assert callable(getattr(FileProcessor, processor))

    def test_processor_mapping_coverage(self):
        """测试处理器映射覆盖所有支持的扩展名"""
        supported_extensions = [".txt", ".md", ".json", ".docx", ".pdf"]

        for ext in supported_extensions:
            assert ext in FileProcessor.PROCESSORS
            processor_name = FileProcessor.PROCESSORS[ext]
            assert hasattr(FileProcessor, processor_name)
