# inference_server/services/ingest.py
"""문서 업로드 및 RAG 저장 서비스"""

import os
import re
import tempfile
import logging
from fastapi import UploadFile, File, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .. import state

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """
    PDF에서 텍스트 추출 (pdfplumber → PyPDF2 fallback)
    
    Args:
        file_path: PDF 파일 경로
        
    Returns:
        추출된 텍스트 (문자열)
        
    Raises:
        ValueError: 텍스트 추출 실패 시
    """
    text = ""

    # Method 1: pdfplumber (권장 - 더 정확한 추출)
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n{page_text}"

        if len(text.strip()) > 100:
            logger.info(f"✅ pdfplumber 추출 성공: {len(text)}자")
            return text
        else:
            logger.warning(f"pdfplumber 추출 결과 부족 ({len(text)}자), PyPDF2 fallback 시도")

    except Exception as e:
        logger.warning(f"pdfplumber 실패: {e}, PyPDF2로 fallback")

    # Method 2: PyPDF2 (fallback)
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        logger.info(f"PyPDF2로 PDF 읽기 시도: {len(reader.pages)} 페이지")

        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {page_num} ---\n{page_text}"

        logger.info(f"✅ PyPDF2 추출 완료: {len(text)}자")

    except Exception as e:
        logger.error(f"PyPDF2도 실패: {e}")
        raise ValueError(f"PDF 텍스트 추출 실패: {str(e)}")

    # 텍스트 검증
    if len(text.strip()) < 50:
        raise ValueError(f"PDF 텍스트가 너무 짧습니다 ({len(text)}자). 스캔 이미지 PDF일 수 있습니다.")

    # 반복 패턴 감지
    if re.search(r'(.{20,})\1{3,}', text):
        logger.warning("⚠️ 반복 패턴 감지 - 스캔 PDF이거나 추출 오류 가능성")

    return text.strip()


async def ingest_document(file: UploadFile) -> dict:
    """
    문서 업로드 및 ChromaDB RAG 저장
    
    지원 형식: PDF, TXT
    """
    if not state.vectordb:
        raise HTTPException(status_code=500, detail="VectorDB not initialized")

    try:
        # 1. 임시 파일 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        with temp_file as tf:
            content = await file.read()
            tf.write(content)
            temp_path = tf.name

        logger.info(f"📄 파일 업로드: {file.filename} ({len(content)} bytes)")

        # 2. 파일 형식별 텍스트 추출
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(temp_path)
            logger.info(f"✅ PDF 텍스트 추출 완료: {len(text)}자")

        elif file.filename.endswith(".txt"):
            with open(temp_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"✅ TXT 파일 읽기 완료: {len(text)}자")

        else:
            os.unlink(temp_path)
            raise HTTPException(
                status_code=400,
                detail="지원되지 않는 파일 형식입니다. PDF 또는 TXT 파일만 업로드 가능합니다."
            )

        # 3. 텍스트 청킹
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,  # ✅ 20% 오버랩 (문맥 보존 강화)
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        logger.info(f"📦 텍스트 청킹 완료: {len(chunks)}개 청크")

        # 4. ChromaDB에 저장
        metadatas = [
            {
                "source": file.filename,
                "chunk_id": i,
                "total_chunks": len(chunks)
            }
            for i in range(len(chunks))
        ]
        state.vectordb.add_texts(chunks, metadatas=metadatas)
        logger.info("✅ ChromaDB 저장 완료")

        # 5. 임시 파일 삭제
        os.unlink(temp_path)

        return {
            "ok": True,
            "message": f"'{file.filename}' 업로드 및 처리 완료",
            "chunks": len(chunks),
            "total_chars": len(text),
            "filename": file.filename
        }

    except ValueError as ve:
        logger.error(f"❌ 문서 처리 실패: {ve}")
        if 'temp_path' in locals():
            os.unlink(temp_path)
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"❌ 문서 업로드 실패: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
