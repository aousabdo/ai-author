"""
Dialogue Expert Agent
Specializes in analyzing and improving dialogue quality and character voices.
"""
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from core.agent import Agent
from utils.text_processing import extract_dialogue

logger = logging.getLogger(__name__)

class DialogueExpertAgent(Agent):
    """
    Agent specialized in improving dialogue quality and character voices.
    """
    
    def __init__(self, config: Dict[str, Any], llm_provider):
        """Initialize the Dialogue Expert Agent"""
        super().__init__(name="Dialogue Expert", config=config, llm_provider=llm_provider)
    
    def refine_dialogue(self, chapters: List[str], character_profiles: str) -> Dict[str, Any]:
        """
        Analyze and refine dialogue across all chapters
        
        Args:
            chapters: List of chapters to analyze
            character_profiles: Character profiles for reference
            
        Returns:
            Dictionary with dialogue analysis and improvements
        """
        logger.info(f"Analyzing dialogue across {len(chapters)} chapters")
        
        # First, create a dialogue style guide
        style_guide = self._create_dialogue_style_guide(character_profiles)
        
        # Extract character names for voice analysis
        character_names = self._extract_character_names(character_profiles)
        
        # Analyze each chapter's dialogue
        chapter_analyses = {}
        chapter_fixes = {}
        total_fixes = 0
        
        for i, chapter in enumerate(chapters):
            chapter_num = i + 1
            logger.info(f"Analyzing dialogue in Chapter {chapter_num}")
            
            # Extract dialogue from the chapter
            dialogue_samples = extract_dialogue(chapter)
            
            # Skip if no dialogue found
            if not dialogue_samples:
                chapter_analyses[str(chapter_num)] = {
                    "dialogue_count": 0,
                    "issues": [],
                    "quality_score": 0
                }
                continue
            
            # Format dialogue samples for analysis
            dialogue_text = "\n".join([
                f"{sample.get('speaker', 'Unknown')}: \"{sample.get('dialogue', '')}\""
                for sample in dialogue_samples[:15]  # Limit to 15 samples
            ])
            
            analysis_prompt = f"""
            Analyze the dialogue in this chapter based on the dialogue style guide.
            
            Dialogue Style Guide:
            {style_guide}
            
            Character Names: {', '.join(character_names)}
            
            Dialogue Samples from Chapter {chapter_num}:
            {dialogue_text}
            
            Evaluate for:
            1. Character voice consistency
            2. Dialogue naturalness and flow
            3. Speech pattern distinctiveness
            4. Dialogue tag usage (said, asked, etc.)
            5. Balance of dialogue and narrative
            6. Subtext and purpose of dialogue
            
            Identify issues where:
            - Character voice doesn't match their profile
            - Dialogue sounds unnatural or stilted
            - Characters all sound too similar
            - Dialogue tags are repetitive or unnecessary
            - Dialogue lacks purpose or doesn't advance plot/character
            
            Format your response as JSON with:
            - "dialogue_count": Number of dialogue exchanges analyzed
            - "issues": Array of specific dialogue issues
            - "examples": Array of problematic dialogue examples
            - "improved_versions": Array of improved versions for each example
            - "quality_score": Overall dialogue quality score (1-10)
            """
            
            response = self.generate(analysis_prompt, temperature=0.4)
            
            # Parse and store results
            analysis = self.parse_json_response(response, default={
                "dialogue_count": len(dialogue_samples),
                "issues": [],
                "examples": [],
                "improved_versions": [],
                "quality_score": 5
            })
            
            chapter_analyses[str(chapter_num)] = analysis
            
            # Collect specific fixes needed
            issues = analysis.get("issues", [])
            examples = analysis.get("examples", [])
            improved = analysis.get("improved_versions", [])
            
            if not issues or not examples or not improved:
                continue
                
            fix_count = min(len(issues), len(examples), len(improved))
            chapter_fixes[str(chapter_num)] = []
            
            for j in range(fix_count):
                chapter_fixes[str(chapter_num)].append({
                    "issue": issues[j] if j < len(issues) else "",
                    "original": examples[j] if j < len(examples) else "",
                    "improved": improved[j] if j < len(improved) else ""
                })
            
            total_fixes += fix_count
        
        # Analyze voice consistency across chapters
        voice_consistency = self._analyze_voice_consistency(chapter_analyses, character_names)
        
        # Create the final report
        dialogue_report = {
            "style_guide": style_guide,
            "voice_consistency": voice_consistency,
            "chapter_analyses": chapter_analyses,
            "chapter_fixes": chapter_fixes,
            "total_fixes": total_fixes
        }
        
        logger.info(f"Dialogue analysis complete. Found {total_fixes} issues across {len(chapter_fixes)} chapters.")
        return dialogue_report
    
    def _create_dialogue_style_guide(self, character_profiles: str) -> str:
        """
        Create a dialogue style guide based on character profiles
        
        Args:
            character_profiles: Character profiles
            
        Returns:
            Dialogue style guide
        """
        guide_prompt = f"""
        Create a comprehensive dialogue style guide for the characters in this story.
        
        Character Profiles:
        {character_profiles}
        
        For each main character, define:
        1. Distinctive speech patterns and vocabulary
        2. Common phrases or verbal tics
        3. Formality level and tone
        4. Typical sentence structures and length
        5. Cultural or background influences on speech
        
        Then provide general guidelines for:
        - Dialogue tag usage and variation
        - Balance of dialogue and action/narrative
        - Handling internal thoughts vs. spoken dialogue
        - Maintaining consistent character voices
        - Creating natural-sounding conversation flow
        
        This guide will be used to ensure dialogue quality and consistency throughout the story.
        """
        
        return self.generate(guide_prompt, temperature=0.6)
    
    def _extract_character_names(self, character_profiles: str) -> List[str]:
        """
        Extract character names from profiles
        
        Args:
            character_profiles: Character profiles
            
        Returns:
            List of character names
        """
        # Try to extract names using regex patterns
        patterns = [
            r'(?:Character|Name):\s*([A-Z][a-zA-Z\s\-\']+)',
            r'(?:\d+\.\s+|\*\*|\#\#)([A-Z][a-zA-Z\s\-\']+)'
        ]
        
        names = []
        for pattern in patterns:
            matches = re.findall(pattern, character_profiles)
            if matches:
                names.extend([name.strip() for name in matches if name.strip()])
        
        # If no names found, use generic placeholders
        if not names:
            return ["Protagonist", "Antagonist", "Supporting Character"]
            
        return names
    
    def _analyze_voice_consistency(self, chapter_analyses: Dict[str, Any], 
                                 character_names: List[str]) -> Dict[str, Any]:
        """
        Analyze voice consistency across chapters
        
        Args:
            chapter_analyses: Chapter dialogue analyses
            character_names: List of character names
            
        Returns:
            Voice consistency analysis
        """
        # Format chapter analyses for the prompt
        analyses_summary = "\n".join([
            f"Chapter {num}: Score {analysis.get('quality_score', 'N/A')}, " +
            f"Issues: {len(analysis.get('issues', []))}"
            for num, analysis in chapter_analyses.items()
        ])
        
        consistency_prompt = f"""
        Analyze character voice consistency across all chapters.
        
        Character Names: {', '.join(character_names)}
        
        Chapter Dialogue Analyses Summary:
        {analyses_summary}
        
        Evaluate:
        1. Whether each character maintains a consistent and distinctive voice
        2. If dialogue quality varies significantly between chapters
        3. Any patterns of dialogue issues across chapters
        4. Overall dialogue quality and effectiveness
        
        Provide recommendations for maintaining voice consistency.
        
        Format your response as JSON with:
        - "character_voice_ratings": Object mapping character names to consistency scores (1-10)
        - "consistency_issues": Array of voice consistency issues found
        - "recommendations": Array of recommendations for improvement
        - "overall_rating": Overall voice consistency rating (1-10)
        """
        
        response = self.generate(consistency_prompt, temperature=0.5)
        return self.parse_json_response(response, default={
            "character_voice_ratings": {},
            "consistency_issues": [],
            "recommendations": [],
            "overall_rating": 5
        })
    
    def _extract_text(self, obj) -> str:
        """
        Extract text from potentially complex objects (dictionaries, etc.)
        
        Args:
            obj: The object to extract text from
            
        Returns:
            The extracted text as a string
        """
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            # If it's a dictionary, try common keys that might contain text
            for key in ['text', 'dialogue', 'content', 'original', 'value']:
                if key in obj:
                    return self._extract_text(obj[key])
            # If no known keys, just use the first string value found
            for value in obj.values():
                if isinstance(value, str):
                    return value
        # Default fallback
        return str(obj) if obj is not None else ""

    def apply_fixes(self, chapter: str, issues: List[Dict[str, Any]]) -> str:
        """
        Apply dialogue fixes to a chapter
        
        Args:
            chapter: The chapter content
            issues: List of dialogue issues to fix
            
        Returns:
            Updated chapter with dialogue fixes applied
        """
        if not issues:
            return chapter
        
        # Try to apply direct replacements first for exact matches
        for issue in issues:
            # Extract text safely
            original_text = self._extract_text(issue.get('original', ''))
            improved_text = self._extract_text(issue.get('improved', ''))
            
            if original_text and improved_text and original_text in chapter:
                chapter = chapter.replace(original_text, improved_text)
        
        # For remaining issues or if direct replacement didn't work well,
        # use a more sophisticated approach with context
        remaining_issues = []
        for issue in issues:
            # Use _extract_text here as well to handle dictionaries
            original_text = self._extract_text(issue.get('original', ''))
            if original_text and original_text not in chapter:
                remaining_issues.append(issue)
        
        if remaining_issues:
            # Create a batch prompt that includes all remaining fixes
            issues_text = "\n".join([
                f"{i+1}. Issue: {issue.get('issue', '')}\n"
                f"   Original: \"{self._extract_text(issue.get('original', ''))}\"\n"
                f"   Improved: \"{self._extract_text(issue.get('improved', ''))}\""
                for i, issue in enumerate(remaining_issues)
            ])
            
            fix_prompt = f"""
            Revise the dialogue in this chapter to implement the suggested improvements.
            
            Chapter content:
            {chapter[:2000]}...
            [middle of chapter omitted for brevity]
            ...{chapter[-2000:]}
            
            Dialogue issues to fix:
            {issues_text}
            
            Instructions:
            1. For each issue, identify similar dialogue in the chapter
            2. Apply the suggested improvements, adapting as needed
            3. Ensure the revisions blend naturally with surrounding text
            4. Maintain the same basic events and content
            
            Return the complete revised chapter with improved dialogue.
            """
            
            # If the chapter is very long, use a different approach
            if len(chapter) > 8000:
                # Just keep the direct replacements we've already made
                logger.info("Chapter too long for complete dialogue revision; using direct replacements only")
                return chapter
            
            return self.generate(fix_prompt, temperature=0.6)
        
        return chapter
    
    def improve_character_voice(self, character_name: str, dialogue_samples: List[str], 
                               character_profile: str) -> List[str]:
        """
        Improve dialogue for a specific character to enhance voice consistency
        
        Args:
            character_name: Name of the character
            dialogue_samples: List of dialogue samples to improve
            character_profile: Character's profile
            
        Returns:
            List of improved dialogue samples
        """
        samples_text = "\n".join([f"- \"{sample}\"" for sample in dialogue_samples])
        
        voice_prompt = f"""
        Improve these dialogue samples for {character_name} to create a more consistent and distinctive voice.
        
        Character Profile:
        {character_profile}
        
        Current Dialogue Samples:
        {samples_text}
        
        Enhance these dialogue samples to:
        1. Better reflect the character's personality and background
        2. Use more distinctive vocabulary and speech patterns
        3. Maintain consistent tone and manner of speaking
        4. Sound natural and authentic to the character
        
        Format your response as JSON with an "improved_samples" array containing the enhanced dialogue.
        Each improved line should preserve the same basic meaning and intent as the original.
        """
        
        response = self.generate(voice_prompt, temperature=0.7)
        result = self.parse_json_response(response, default={"improved_samples": dialogue_samples})
        
        return result.get("improved_samples", dialogue_samples)
    
    def create_dialogue_exchange(self, characters: List[str], scene_context: str, 
                                purpose: str, word_count: int = 200) -> str:
        """
        Create a dialogue exchange between characters
        
        Args:
            characters: List of character names involved
            scene_context: Context of the scene
            purpose: Purpose of the dialogue (e.g., "reveal secret", "build tension")
            word_count: Target word count for the dialogue
            
        Returns:
            Created dialogue exchange
        """
        exchange_prompt = f"""
        Create a natural dialogue exchange between {', '.join(characters)} for the following scene.
        
        Scene Context:
        {scene_context}
        
        Dialogue Purpose:
        {purpose}
        
        Guidelines:
        - Target length: Approximately {word_count} words
        - Create distinctive voices for each character
        - Balance dialogue with brief action/gesture descriptions
        - Advance the plot and reveal character
        - Include subtext and natural conversational elements
        - Avoid exposition dumps or "as you know" dialogue
        
        Write the dialogue exchange as it would appear in a novel, with dialogue tags,
        character actions, and narrative elements as appropriate.
        """
        
        return self.generate(exchange_prompt, temperature=0.8)