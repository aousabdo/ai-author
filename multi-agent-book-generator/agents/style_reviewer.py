"""
Style Reviewer Agent
Specializes in analyzing and improving writing style consistency.
"""
import logging
from typing import Dict, Any, List, Optional
from core.agent import Agent
from utils.text_processing import find_repeated_phrases, remove_adverbs

logger = logging.getLogger(__name__)

class StyleReviewerAgent(Agent):
    """
    Agent specialized in analyzing and improving writing style.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Style Reviewer Agent"""
        super().__init__(name="Style Reviewer", config=config, llm_provider=llm_provider)
    
    def review_style_consistency(self, chapters: List[str], writing_style: str) -> Dict[str, Any]:
        """
        Review the consistency of writing style across chapters
        
        Args:
            chapters: List of chapters to analyze
            writing_style: The target writing style
            
        Returns:
            Dictionary with style consistency analysis
        """
        logger.info(f"Reviewing style consistency for {len(chapters)} chapters")
        
        # First, analyze overall style characteristics
        style_analysis = self._analyze_style_characteristics(chapters[0][:5000], writing_style)
        
        # For each chapter, check against the target style
        chapter_analyses = {}
        chapter_fixes = {}
        total_fixes = 0
        
        for i, chapter in enumerate(chapters):
            chapter_num = i + 1
            logger.info(f"Analyzing style for Chapter {chapter_num}")
            
            # Analyze chapter excerpt 
            excerpt = chapter[:2000] + "..." + chapter[-2000:] if len(chapter) > 4000 else chapter
            
            chapter_prompt = f"""
            Analyze the writing style of this chapter excerpt, comparing it to the target style of "{writing_style}".
            
            Target Style Characteristics:
            {style_analysis}
            
            Chapter {chapter_num} Excerpt:
            {excerpt}
            
            Identify stylistic inconsistencies with the target style, focusing on:
            1. Tone and voice
            2. Sentence structure and length
            3. Level of description and detail
            4. Dialogue style
            5. Word choice and vocabulary
            6. Pacing and rhythm
            
            For each issue, provide:
            - Brief description of the inconsistency
            - Example text from the chapter
            - A suggested improvement/rewrite
            
            Format your response as JSON with these fields:
            - "issues": Array of style issues found
            - "examples": Array of problematic text examples
            - "fixes": Array of suggested rewrites
            - "consistency_score": Number from 1-10 rating overall style consistency
            """
            
            response = self.generate(chapter_prompt, temperature=0.4)
            
            # Parse and store results
            analysis = self.parse_json_response(response, default={
                "issues": [],
                "examples": [],
                "fixes": [],
                "consistency_score": 5
            })
            
            chapter_analyses[str(chapter_num)] = analysis
            
            # Collect specific fixes needed
            issues = analysis.get("issues", [])
            examples = analysis.get("examples", [])
            fixes = analysis.get("fixes", [])
            
            if not issues or not examples or not fixes:
                continue
                
            fix_count = min(len(issues), len(examples), len(fixes))
            chapter_fixes[str(chapter_num)] = []
            
            for j in range(fix_count):
                chapter_fixes[str(chapter_num)].append({
                    "description": issues[j] if j < len(issues) else "",
                    "text": examples[j] if j < len(examples) else "",
                    "fix": fixes[j] if j < len(fixes) else ""
                })
            
            total_fixes += fix_count
        
        # Create the final report
        style_report = {
            "target_style": writing_style,
            "style_characteristics": style_analysis,
            "chapter_analyses": chapter_analyses,
            "chapter_fixes": chapter_fixes,
            "total_fixes": total_fixes
        }
        
        logger.info(f"Style review complete. Found {total_fixes} issues across {len(chapter_fixes)} chapters.")
        return style_report
    
    def _analyze_style_characteristics(self, sample_text: str, writing_style: str) -> str:
        """
        Analyze the characteristics of a specific writing style
        
        Args:
            sample_text: Sample text to analyze
            writing_style: The target writing style
            
        Returns:
            Description of the writing style characteristics
        """
        style_prompt = f"""
        Analyze the characteristics of the "{writing_style}" writing style, using the following sample text as a reference.
        
        Sample Text:
        {sample_text}
        
        Define the key characteristics of this writing style by examining:
        1. Tone and voice (formal/informal, personal/impersonal, etc.)
        2. Sentence structure (simple/complex, length variations, etc.)
        3. Description style (sparse/detailed, concrete/abstract, etc.)
        4. Dialogue style (natural/stylized, sparse/abundant, etc.)
        5. Vocabulary (simple/complex, specialized/general, etc.)
        6. Pacing and rhythm (fast/slow, varied/consistent, etc.)
        
        Provide a comprehensive description of these elements that can be used to evaluate style consistency.
        """
        
        return self.generate(style_prompt, temperature=0.5)
    
    def apply_fixes(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply style fixes to a chapter
        
        Args:
            chapter: The chapter content
            issues: List of style issues to fix
            
        Returns:
            Updated chapter with style fixes applied
        """
        if not issues:
            return chapter
        
        # Create a batch prompt that includes all fixes
        issues_text = "\n".join([
            f"{i+1}. Issue: {issue.get('description', '')}\n"
            f"   Text: \"{issue.get('text', '')}\"\n"
            f"   Fix: {issue.get('fix', '')}"
            for i, issue in enumerate(issues)
        ])
        
        fix_prompt = f"""
        Revise the following chapter to fix the specified style issues.
        
        Chapter content:
        {chapter[:1000]}...
        [middle of chapter omitted for brevity]
        ...{chapter[-1000:]}
        
        Style issues to fix:
        {issues_text}
        
        Instructions:
        1. Find each problematic text passage in the chapter
        2. Replace it with the suggested fix
        3. Ensure the transitions remain smooth
        4. Return the complete revised chapter
        
        Only make the specific changes described in the issues list.
        Do not add comments or explanations - just provide the revised chapter text.
        """
        
        # For larger chapters, we'll need to apply fixes to specific sections
        if len(chapter) > 10000:
            return self._apply_fixes_to_long_chapter(chapter, issues)
        
        return self.generate(fix_prompt, temperature=0.5)
    
    def _apply_fixes_to_long_chapter(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply style fixes to a long chapter by processing it in sections
        
        Args:
            chapter: The chapter content
            issues: List of style issues to fix
            
        Returns:
            Updated chapter with style fixes applied
        """
        # Manual fix by directly replacing text
        for issue in issues:
            original_text = issue.get('text', '')
            fixed_text = issue.get('fix', '')
            
            if original_text and fixed_text and original_text in chapter:
                chapter = chapter.replace(original_text, fixed_text)
        
        return chapter
    
    def improve_prose_quality(self, text: str, target_style: str) -> str:
        """
        Improve the prose quality of text
        
        Args:
            text: The text to improve
            target_style: The target writing style
            
        Returns:
            Improved text
        """
        # First, reduce adverb usage
        text = remove_adverbs(text)
        
        # Find repeated phrases
        repeated_phrases = find_repeated_phrases(text)
        repeated_text = ""
        
        if repeated_phrases:
            repeated_text = "Repeated phrases to vary:\n"
            for phrase, count in repeated_phrases[:5]:  # Top 5 most repeated
                repeated_text += f"- '{phrase}' (used {count} times)\n"
        
        improvement_prompt = f"""
        Improve the prose quality of the following text, maintaining the "{target_style}" style.
        
        Original text:
        {text}
        
        {repeated_text}
        
        Enhance the writing by:
        1. Varying sentence structure
        2. Replacing generic descriptions with more vivid ones
        3. Reducing repetition of words and phrases
        4. Improving the rhythm and flow
        5. Using more precise and evocative language
        
        The revised text should maintain the same meaning, events, and dialogue,
        just with improved prose quality. Keep the same approximate length.
        """
        
        return self.generate(improvement_prompt, temperature=0.7)
    
    def evaluate_writing_style(self, text: str) -> Dict[str, Any]:
        """
        Evaluate the writing style of a text
        
        Args:
            text: The text to evaluate
            
        Returns:
            Dictionary with style evaluation
        """
        evaluation_prompt = f"""
        Evaluate the writing style of the following text excerpt.
        
        Text:
        {text[:3000]}
        
        Analyze:
        1. Tone (formal/informal, serious/lighthearted, etc.)
        2. Voice (first-person/third-person, limited/omniscient, etc.)
        3. Sentence complexity and variety
        4. Description density and detail level
        5. Dialogue style and realism
        6. Word choice and vocabulary range
        7. Literary devices used
        8. Overall genre fit
        
        Format your response as JSON with these categories as keys and detailed evaluations as values.
        Also include an "overall_style" field with a concise description of the style.
        """
        
        response = self.generate(evaluation_prompt, temperature=0.5)
        return self.parse_json_response(response, default={"overall_style": "mixed"})