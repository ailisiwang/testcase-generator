"""File processing service"""
import os
import hashlib
from typing import Optional
from pathlib import Path

from app.config import settings


class FileProcessor:
    """File processing utility"""
    
    # Supported file extensions and their processors
    PROCESSORS = {
        ".txt": "_process_text",
        ".md": "_process_text",
        ".json": "_process_json",
        ".docx": "_process_docx",
        ".pdf": "_process_pdf",
    }
    
    @staticmethod
    def save_upload(file_data: bytes, filename: str) -> str:
        """Save uploaded file and return path"""
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        safe_name = Path(filename).name
        file_hash = hashlib.sha256(file_data).hexdigest()[:12]
        ext = Path(safe_name).suffix.lower()
        unique_filename = f"{file_hash}_{safe_name}"
        
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        return str(file_path)
    
    @staticmethod
    def process_file(file_path: str) -> str:
        """Process file and extract text content"""
        ext = Path(file_path).suffix.lower()
        
        if ext not in FileProcessor.PROCESSORS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        processor_method = getattr(FileProcessor, FileProcessor.PROCESSORS[ext])
        return processor_method(file_path)
    
    @staticmethod
    def _process_text(file_path: str) -> str:
        """Process plain text or markdown file"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    @staticmethod
    def _process_json(file_path: str) -> str:
        """Process JSON file"""
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert JSON to readable text
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @staticmethod
    def _process_docx(file_path: str) -> str:
        """Process Word document"""
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except ImportError:
            raise ImportError("python-docx is required for .docx files")
    
    @staticmethod
    def _process_pdf(file_path: str) -> str:
        """Process PDF file"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF files")
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> bool:
        """Validate file type and size"""
        # Check extension
        ext = Path(Path(filename).name).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False
        
        # Check size
        if file_size > settings.MAX_FILE_SIZE:
            return False
        
        return True
    
    @staticmethod
    def delete_file(file_path: str):
        """Delete uploaded file"""
        if os.path.exists(file_path):
            os.remove(file_path)
