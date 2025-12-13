
import re
from docx import Document
import PyPDF2
import pdfplumber

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

class ResumeParser:
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.text = ""
        
    def extract_text(self):
        """Extract text from different file formats"""
        if self.file_path.endswith('.pdf'):
            self.text = self._extract_from_pdf()
        elif self.file_path.endswith('.docx'):
            self.text = self._extract_from_docx()
        elif self.file_path.endswith('.txt'):
            self.text = self._extract_from_txt()
        return self.text
    
    def _extract_from_pdf(self):
        """Extract text from PDF"""
        text = ""
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except:
            # Fallback to PyPDF2
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        return text
    
    def _extract_from_docx(self):
        """Extract text from DOCX"""
        doc = Document(self.file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    def _extract_from_txt(self):
        """Extract text from TXT"""
        with open(self.file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def extract_name(self):
        """Extract name using NLP"""
        doc = nlp(self.text[:1000])  # Check first 1000 chars
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text
        return ""
    
    def extract_email(self):
        """Extract email using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, self.text)
        return match.group(0) if match else ""
    
    def extract_phone(self):
        """Extract phone number"""
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        match = re.search(phone_pattern, self.text)
        return match.group(0) if match else ""
    
    def extract_skills(self):
        """Extract skills - basic keyword matching"""
        skills_keywords = [
            'python', 'java', 'javascript', 'c++', 'sql', 'react', 
            'django', 'flask', 'nodejs', 'aws', 'docker', 'kubernetes',
            'machine learning', 'data analysis', 'project management'
        ]
        found_skills = []
        text_lower = self.text.lower()
        for skill in skills_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        return ", ".join(found_skills)
    
    def extract_education(self):
        """Extract education section"""
        education_keywords = ['education', 'academic', 'university', 'college', 'degree']
        lines = self.text.split('\n')
        education_lines = []
        capture = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in education_keywords):
                capture = True
            if capture:
                education_lines.append(line)
                if len(education_lines) > 10:  # Limit to 10 lines
                    break
        
        return "\n".join(education_lines[:10])
    
    def generate_summary(self):
        """Generate a simple summary"""
        # Take first 500 characters as summary
        summary = self.text[:500].strip()
        return summary + "..." if len(self.text) > 500 else summary
