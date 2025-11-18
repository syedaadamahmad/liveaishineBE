"""
DOCX Parser for Knowledge Base
Extracts structured content from MODULE-1_KB.docx and converts to JSON format.
"""
import os
import re
import json
import logging
from typing import List, Dict, Any
from docx import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DOCXParser:
    """Parse DOCX knowledge base into structured JSON chunks."""
    
    def __init__(self, enhanced_kb_path: str):
        """
        Initialize parser with enhanced KB for keyword mapping.
        
        Args:
            enhanced_kb_path: Path to Enhanced_Module1_KB.json
        """
        self.enhanced_kb = self._load_enhanced_kb(enhanced_kb_path)
        self.topic_to_keywords = {item['topic']: item['keywords'] for item in self.enhanced_kb}
        logger.info(f"[PARSER] Loaded {len(self.enhanced_kb)} topic mappings")
    
    def _load_enhanced_kb(self, path: str) -> List[Dict[str, Any]]:
        """Load enhanced KB JSON."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"[PARSER] Loaded enhanced KB: {len(data)} entries")
            return data
        except Exception as e:
            logger.error(f"[PARSER_ERR] Failed to load enhanced KB: {e}")
            return []
    
    def parse_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """
        Parse DOCX file into structured JSON chunks.
        
        Args:
            docx_path: Path to MODULE-1_KB.docx
        
        Returns:
            List of structured KB entries
        """
        try:
            doc = Document(docx_path)
            logger.info(f"[PARSER] Parsing DOCX: {docx_path}")
            
            chunks = []
            current_topic = None
            current_content = []
            
            for para in doc.paragraphs:
                text = para.text.strip()
                
                if not text:
                    continue
                
                # Detect topic headers (typically bold or larger font)
                if self._is_topic_header(para):
                    # Save previous topic
                    if current_topic and current_content:
                        chunk = self._create_chunk(current_topic, current_content)
                        if chunk:
                            chunks.append(chunk)
                    
                    # Start new topic
                    current_topic = text
                    current_content = []
                    logger.info(f"[PARSER] Found topic: {current_topic}")
                else:
                    # Accumulate content
                    current_content.append(text)
            
            # Save last topic
            if current_topic and current_content:
                chunk = self._create_chunk(current_topic, current_content)
                if chunk:
                    chunks.append(chunk)
            
            logger.info(f"[PARSER_OK] Parsed {len(chunks)} chunks from DOCX")
            return chunks
        
        except Exception as e:
            logger.error(f"[PARSER_ERR] Failed to parse DOCX: {e}")
            return []
    
    def _is_topic_header(self, paragraph) -> bool:
        """
        Detect if paragraph is a topic header.
        
        Heuristics:
        - Bold text
        - Font size > 12pt
        - Short length (< 150 chars)
        """
        if not paragraph.text.strip():
            return False
        
        # Check if any run is bold
        has_bold = any(run.bold for run in paragraph.runs if run.text.strip())
        
        # Check length
        is_short = len(paragraph.text.strip()) < 150
        
        # Check if matches known topics
        matches_known_topic = any(
            topic.lower() in paragraph.text.lower()
            for topic in self.topic_to_keywords.keys()
        )
        
        return (has_bold or matches_known_topic) and is_short
    
    def _create_chunk(self, topic: str, content: List[str]) -> Dict[str, Any]:
        """
        Create a structured chunk from topic and content.
        
        Args:
            topic: Topic header text
            content: List of content paragraphs
        
        Returns:
            Structured chunk dict
        """
        # Join content
        full_content = "\n\n".join(content)
        
        # Find matching enhanced KB entry
        enhanced_entry = None
        for entry in self.enhanced_kb:
            if self._topics_match(entry['topic'], topic):
                enhanced_entry = entry
                break
        
        if not enhanced_entry:
            logger.warning(f"[PARSER] No enhanced KB match for: {topic}")
            # Create basic entry
            enhanced_entry = {
                "topic": topic,
                "category": "General",
                "level": "All",
                "type": "Content",
                "summary": full_content[:200] + "...",
                "keywords": self._extract_keywords(full_content)
            }
        
        # Create chunk
        chunk = {
            "topic": topic,
            "category": enhanced_entry.get('category', 'General'),
            "level": enhanced_entry.get('level', 'All'),
            "type": enhanced_entry.get('type', 'Content'),
            "summary": enhanced_entry.get('summary', ''),
            "content": full_content,  # Full DOCX content
            "keywords": enhanced_entry.get('keywords', []),
            "module_name": "module1_kb"
        }
        
        return chunk
    
    def _topics_match(self, enhanced_topic: str, docx_topic: str) -> bool:
        """Check if topics match (fuzzy matching)."""
        enhanced_clean = re.sub(r'[^\w\s]', '', enhanced_topic.lower())
        docx_clean = re.sub(r'[^\w\s]', '', docx_topic.lower())
        
        # Exact match
        if enhanced_clean == docx_clean:
            return True
        
        # Substring match (one contains other)
        if enhanced_clean in docx_clean or docx_clean in enhanced_clean:
            return True
        
        # Word overlap (>50% words match)
        enhanced_words = set(enhanced_clean.split())
        docx_words = set(docx_clean.split())
        
        if not enhanced_words or not docx_words:
            return False
        
        overlap = len(enhanced_words & docx_words)
        min_words = min(len(enhanced_words), len(docx_words))
        
        return overlap / min_words > 0.5
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract basic keywords from text (fallback)."""
        # Simple extraction: capitalized words and common AI terms
        words = re.findall(r'\b[A-Z][a-z]+\b|\b(?:AI|ML|data|learning|neural|model)\b', text)
        return list(set(words))[:15]  # Limit to 15 keywords
    
    def save_parsed_kb(self, chunks: List[Dict[str, Any]], output_path: str):
        """Save parsed chunks to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            logger.info(f"[PARSER] Saved {len(chunks)} chunks to {output_path}")
        except Exception as e:
            logger.error(f"[PARSER_ERR] Failed to save: {e}")


def main():
    """Main execution: parse DOCX and save to JSON."""
    # Paths
    enhanced_kb_path = r"C:\Users\newbr\OneDrive\Desktop\AISHINEBE_CLAUDE\Enhanced_Module1_KB.json"
    docx_path = r"C:\Users\newbr\OneDrive\Desktop\AISHINEBE_CLAUDE\MODULE-1 KB.docx"
    output_path = "Parsed_Module1_KB.json"
    
    # Parse
    parser = DOCXParser(enhanced_kb_path)
    chunks = parser.parse_docx(docx_path)
    
    if chunks:
        parser.save_parsed_kb(chunks, output_path)
        logger.info(f"\n✅ Successfully parsed {len(chunks)} chunks")
        logger.info(f"📄 Output saved to: {output_path}")
    else:
        logger.error("\n❌ Parsing failed - no chunks generated")


if __name__ == "__main__":
    main()