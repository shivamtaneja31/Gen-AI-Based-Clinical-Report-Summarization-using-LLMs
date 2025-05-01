from enum import Enum
from typing import Dict, List, Optional, Any
import logging
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    DISCHARGE_NOTE = "discharge_note"
    RADIOLOGY_REPORT = "radiology_report"
    LAB_RESULT = "lab_result"


class Summary(BaseModel):
    report_id: str
    report_type: ReportType
    summary_text: str
    key_findings: List[str]
    recommendations: Optional[List[str]] = None
    metadata: Dict[str, Any] = {}


class AISummaryGenerator:
    """Generator for clinical report summaries using LLMs"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )
        self._setup_prompt_templates()

    def _setup_prompt_templates(self):
        """Set up prompt templates for different report types"""
        # Discharge Note Template
        self.discharge_template = PromptTemplate(
            input_variables=["report_text"],
            template="""
            You are a healthcare AI assistant helping medical professionals by summarizing discharge notes. 
            Please analyze the following discharge note and provide:
            1. A concise summary (3-5 sentences)
            2. Key findings (bullet points)
            3. Follow-up recommendations (bullet points)
            
            Discharge Note:
            {report_text}
            
            Format your response as follows:
            SUMMARY:
            [Your summary here]
            
            KEY FINDINGS:
            - [Finding 1]
            - [Finding 2]
            ...
            
            RECOMMENDATIONS:
            - [Recommendation 1]
            - [Recommendation 2]
            ...
            """,
        )

        # Radiology Report Template
        self.radiology_template = PromptTemplate(
            input_variables=["report_text"],
            template="""
            You are a healthcare AI assistant helping radiologists by summarizing radiology reports.
            Please analyze the following radiology report and provide:
            1. A concise summary (2-3 sentences)
            2. Key findings (bullet points)
            3. Impression and recommendations (bullet points)
            
            Radiology Report:
            {report_text}
            
            Format your response as follows:
            SUMMARY:
            [Your summary here]
            
            KEY FINDINGS:
            - [Finding 1]
            - [Finding 2]
            ...
            
            RECOMMENDATIONS:
            - [Recommendation 1]
            - [Recommendation 2]
            ...
            """,
        )

        # Lab Result Template
        self.lab_result_template = PromptTemplate(
            input_variables=["report_text"],
            template="""
            You are a healthcare AI assistant helping medical professionals by summarizing laboratory results.
            Please analyze the following lab report and provide:
            1. A concise summary (2-3 sentences)
            2. Abnormal findings (bullet points)
            3. Action items (bullet points, if any)
            
            Lab Report:
            {report_text}
            
            Format your response as follows:
            SUMMARY:
            [Your summary here]
            
            KEY FINDINGS:
            - [Finding 1]
            - [Finding 2]
            ...
            
            RECOMMENDATIONS:
            - [Recommendation 1]
            - [Recommendation 2]
            ...
            """,
        )

    def _get_template_for_report_type(self, report_type: ReportType) -> PromptTemplate:
        """Get the appropriate template for the report type"""
        if report_type == ReportType.DISCHARGE_NOTE:
            return self.discharge_template
        elif report_type == ReportType.RADIOLOGY_REPORT:
            return self.radiology_template
        elif report_type == ReportType.LAB_RESULT:
            return self.lab_result_template
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data"""
        sections = {
            "summary_text": "",
            "key_findings": [],
            "recommendations": []
        }
        
        current_section = None
        
        for line in llm_response.split('\n'):
            line = line.strip()
            
            if not line:
                continue
                
            if "SUMMARY:" in line:
                current_section = "summary_text"
                continue
            elif "KEY FINDINGS:" in line:
                current_section = "key_findings"
                continue
            elif "RECOMMENDATIONS:" in line:
                current_section = "recommendations"
                continue
            
            if current_section == "summary_text":
                if sections[current_section]:
                    sections[current_section] += " " + line
                else:
                    sections[current_section] = line
            elif current_section in ["key_findings", "recommendations"]:
                if line.startswith("- "):
                    sections[current_section].append(line[2:])
                elif line and not line.startswith("- ") and sections[current_section]:
                    # Continuation of previous bullet point
                    sections[current_section][-1] += " " + line
        
        return sections

    async def generate_summary(
        self, report_id: str, report_type: ReportType, report_text: str
    ) -> Summary:
        """Generate a summary for a clinical report"""
        logger.info(f"Generating summary for report {report_id} of type {report_type}")
        
        template = self._get_template_for_report_type(report_type)
        chain = LLMChain(llm=self.llm, prompt=template)
        
        # Track token usage and costs
        with get_openai_callback() as cb:
            response = await chain.arun(report_text=report_text)
            logger.debug(f"Token usage - Total: {cb.total_tokens}, Cost: ${cb.total_cost}")
        
        # Parse the response
        parsed_response = self._parse_llm_response(response)
        
        # Create and return the summary
        summary = Summary(
            report_id=report_id,
            report_type=report_type,
            summary_text=parsed_response["summary_text"],
            key_findings=parsed_response["key_findings"],
            recommendations=parsed_response["recommendations"],
            metadata={
                "model": settings.LLM_MODEL_NAME,
                "temperature": settings.LLM_TEMPERATURE,
            }
        )
        
        logger.info(f"Summary generated for report {report_id}")
        return summary