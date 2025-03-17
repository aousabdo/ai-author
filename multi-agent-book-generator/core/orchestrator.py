"""
Book Generation Orchestrator
Manages the multi-agent workflow for book generation
"""
import os
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from .llm_provider import LLMProvider
from .agent import Agent

# Import all agent types
from agents.plot_architect import PlotArchitectAgent
from agents.character_designer import CharacterDesignerAgent
from agents.writer import WriterAgent
from agents.continuity_checker import ContinuityCheckerAgent
from agents.style_reviewer import StyleReviewerAgent
from agents.pacing_advisor import PacingAdvisorAgent
from agents.dialogue_expert import DialogueExpertAgent
from agents.quality_analyst import QualityAnalystAgent
from agents.cover_designer import CoverDesignerAgent

# Import utilities
from utils.parsing import parse_outline
from utils.text_processing import chunk_text
from utils.epub_builder import create_epub

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BookGenerationOrchestrator:
    """Main orchestrator for the book generation process"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the book generation orchestrator
        
        Args:
            config: Configuration dictionary with book generation parameters
        """
        self.config = config
        self.book_data = {
            "metadata": {
                "title": "",
                "author": "AI",
                "creation_date": datetime.now().isoformat(),
                "genre": config.get("genre", "fiction"),
                "writing_style": config.get("writing_style", "descriptive")
            },
            "outline": "",
            "structured_outline": [],
            "character_profiles": [],
            "chapters": [],
            "reviews": [],
            "revisions": [],
            "final_score": {}
        }
        
        # Initialize the LLM provider
        self.llm_provider = LLMProvider(config)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Set the workflow phases
        self.phases = ["planning", "creation", "refinement", "qa", "publishing"]
        self.current_phase = 0
        
        # Create output directory
        self.output_dir = config.get("output_settings", {}).get("output_directory", "./output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Track execution metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "phase_times": {},
            "token_usage": {
                "total": 0,
                "by_agent": {}
            }
        }
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents needed for the book generation process"""
        agents = {
            "plot_architect": PlotArchitectAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "character_designer": CharacterDesignerAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "writer": WriterAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "continuity_checker": ContinuityCheckerAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "style_reviewer": StyleReviewerAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "pacing_advisor": PacingAdvisorAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "dialogue_expert": DialogueExpertAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "quality_analyst": QualityAnalystAgent(
                config=self.config,
                llm_provider=self.llm_provider
            ),
            "cover_designer": CoverDesignerAgent(
                config=self.config,
                llm_provider=self.llm_provider
            )
        }
        return agents
    
    def run(self) -> bool:
        """
        Execute the full book generation process
        
        Returns:
            True if the book generation was successful
        """
        self.metrics["start_time"] = datetime.now().isoformat()
        
        logger.info("Starting book generation process")
        logger.info(f"Genre: {self.config.get('genre', 'fiction')}")
        logger.info(f"Style: {self.config.get('writing_style', 'descriptive')}")
        logger.info(f"Chapters: {self.config.get('num_chapters', 10)}")
        
        try:
            # Execute each phase
            for phase in self.phases:
                phase_start = time.time()
                logger.info(f"Beginning {phase} phase")
                
                if phase == "planning":
                    self._execute_planning_phase()
                elif phase == "creation":
                    self._execute_creation_phase()
                elif phase == "refinement":
                    self._execute_refinement_phase()
                elif phase == "qa":
                    self._execute_qa_phase()
                elif phase == "publishing":
                    self._execute_publishing_phase()
                
                phase_end = time.time()
                self.metrics["phase_times"][phase] = phase_end - phase_start
                logger.info(f"Completed {phase} phase in {phase_end - phase_start:.2f} seconds")
            
            self.metrics["end_time"] = datetime.now().isoformat()
            self._save_metrics()
            
            logger.info(f"Book generation completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error in book generation process: {e}", exc_info=True)
            return False
    
    def _execute_planning_phase(self) -> None:
        """Execute the planning phase to create the book outline and character profiles"""
        logger.info("Planning Phase: Generating book outline and character profiles")
        
        # Generate plot outline
        plot_architect = self.agents["plot_architect"]
        self.book_data["outline"] = plot_architect.create_outline(
            genre=self.config.get("genre", "fiction"),
            description=self.config.get("description", ""),
            num_chapters=self.config.get("num_chapters", 10),
            writing_style=self.config.get("writing_style", "descriptive")
        )
        
        # Parse the outline
        self.book_data["structured_outline"] = parse_outline(self.book_data["outline"])
        
        # Generate character profiles
        character_designer = self.agents["character_designer"]
        self.book_data["character_profiles"] = character_designer.create_character_profiles(
            outline=self.book_data["outline"],
            genre=self.config.get("genre", "fiction")
        )
        
        # Save intermediate results if configured
        if self.config.get("output_settings", {}).get("save_intermediates", True):
            self._save_intermediate_results("planning")
    
    def _execute_creation_phase(self) -> None:
        """Execute the creation phase to write the chapters"""
        logger.info("Creation Phase: Writing chapters based on outline")
        
        writer = self.agents["writer"]
        structured_outline = self.book_data["structured_outline"]
        
        for i, chapter_info in enumerate(structured_outline):
            chapter_num = i + 1
            logger.info(f"Writing chapter {chapter_num}: {chapter_info['title']}")
            
            # Add chapter number to the info
            chapter_info["chapter_num"] = chapter_num
            
            # Get previous chapters for context (limit to prevent token issues)
            prev_chapters = self.book_data["chapters"][-2:] if self.book_data["chapters"] else []
            
            # Generate the chapter content
            chapter = writer.write_chapter(
                chapter_info=chapter_info,
                previous_chapters=prev_chapters,
                character_profiles=self.book_data["character_profiles"],
                writing_style=self.config.get("writing_style", "descriptive")
            )
            
            self.book_data["chapters"].append(chapter)
            
            # Quick continuity check every few chapters
            if len(self.book_data["chapters"]) > 1 and chapter_num % 3 == 0:
                self._perform_interim_check(chapter_num)
            
            # Save progress periodically
            if self.config.get("output_settings", {}).get("save_intermediates", True):
                self._save_chapter(chapter_num, chapter)
        
        # Save all chapters together
        self._save_intermediate_results("creation")
    
    def _execute_refinement_phase(self) -> None:
        """Execute the refinement phase to improve the generated content"""
        logger.info("Refinement Phase: Checking and improving story quality")
        
        # Store original versions before refinement
        original_chapters = self.book_data["chapters"].copy()
        
        # Check for continuity issues
        continuity_checker = self.agents["continuity_checker"]
        continuity_report = continuity_checker.check_story_continuity(
            chapters=self.book_data["chapters"],
            character_profiles=self.book_data["character_profiles"],
            structured_outline=self.book_data["structured_outline"]
        )
        
        self.book_data["reviews"].append({
            "type": "continuity",
            "report": continuity_report
        })
        
        # Check for style consistency
        style_reviewer = self.agents["style_reviewer"]
        style_report = style_reviewer.review_style_consistency(
            chapters=self.book_data["chapters"],
            writing_style=self.config.get("writing_style", "descriptive")
        )
        
        self.book_data["reviews"].append({
            "type": "style",
            "report": style_report
        })
        
        # Check for pacing issues
        pacing_advisor = self.agents["pacing_advisor"]
        pacing_report = pacing_advisor.analyze_pacing(
            chapters=self.book_data["chapters"],
            structured_outline=self.book_data["structured_outline"]
        )
        
        self.book_data["reviews"].append({
            "type": "pacing",
            "report": pacing_report
        })
        
        # Refine dialogue
        dialogue_expert = self.agents["dialogue_expert"]
        dialogue_report = dialogue_expert.refine_dialogue(
            chapters=self.book_data["chapters"],
            character_profiles=self.book_data["character_profiles"]
        )
        
        self.book_data["reviews"].append({
            "type": "dialogue",
            "report": dialogue_report
        })
        
        # Apply refinements
        for i, chapter in enumerate(self.book_data["chapters"]):
            chapter_num = i + 1
            logger.info(f"Refining chapter {chapter_num}")
            
            # Apply continuity fixes
            continuity_fixes = continuity_report.get("chapter_fixes", {}).get(str(chapter_num), [])
            if continuity_fixes:
                chapter = continuity_checker.apply_fixes(chapter, continuity_fixes)
            
            # Apply style improvements
            style_fixes = style_report.get("chapter_fixes", {}).get(str(chapter_num), [])
            if style_fixes:
                chapter = style_reviewer.apply_fixes(chapter, style_fixes)
            
            # Apply pacing improvements
            pacing_fixes = pacing_report.get("chapter_fixes", {}).get(str(chapter_num), [])
            if pacing_fixes:
                chapter = pacing_advisor.apply_fixes(chapter, pacing_fixes)
            
            # Apply dialogue improvements
            dialogue_fixes = dialogue_report.get("chapter_fixes", {}).get(str(chapter_num), [])
            if dialogue_fixes:
                chapter = dialogue_expert.apply_fixes(chapter, dialogue_fixes)
            
            # Update the chapter
            self.book_data["chapters"][i] = chapter
        
        # Save refined chapters
        self._save_intermediate_results("refinement")
        
        # Record changes made
        self.book_data["revisions"] = {
            "continuity_fixes": continuity_report.get("total_fixes", 0),
            "style_fixes": style_report.get("total_fixes", 0),
            "pacing_fixes": pacing_report.get("total_fixes", 0),
            "dialogue_fixes": dialogue_report.get("total_fixes", 0)
        }
    
    def _execute_qa_phase(self) -> None:
        """Execute the quality assurance phase for final checks"""
        logger.info("QA Phase: Performing final quality checks")
        
        # Final quality check
        quality_analyst = self.agents["quality_analyst"]
        qa_report = quality_analyst.evaluate_book_quality(
            chapters=self.book_data["chapters"],
            character_profiles=self.book_data["character_profiles"],
            outline=self.book_data["outline"],
            genre=self.config.get("genre", "fiction"),
            writing_style=self.config.get("writing_style", "descriptive")
        )
        
        self.book_data["reviews"].append({
            "type": "quality",
            "report": qa_report
        })
        
        # Store final quality score
        self.book_data["final_score"] = qa_report.get("scores", {})
        
        # If quality score is too low, attempt improvements
        overall_score = qa_report.get("scores", {}).get("overall", 0)
        if overall_score < 7:  # Threshold for acceptable quality
            logger.warning(f"Book quality score ({overall_score}) is below threshold. Attempting improvements.")
            
            # Apply critical improvements
            critical_issues = qa_report.get("critical_issues", [])
            if critical_issues:
                for i, chapter in enumerate(self.book_data["chapters"]):
                    chapter_issues = [issue for issue in critical_issues if issue.get("chapter") == i+1]
                    if chapter_issues:
                        self.book_data["chapters"][i] = quality_analyst.fix_critical_issues(
                            chapter=chapter,
                            issues=chapter_issues
                        )
        
        # Generate a book title if not already set
        if not self.book_data["metadata"]["title"]:
            self.book_data["metadata"]["title"] = quality_analyst.generate_title(
                chapters=self.book_data["chapters"],
                outline=self.book_data["outline"],
                genre=self.config.get("genre", "fiction")
            )
        
        # Save QA results
        self._save_intermediate_results("qa")
    
    def _execute_publishing_phase(self) -> None:
        """Execute the publishing phase to create the final book files"""
        logger.info("Publishing Phase: Creating final book files")
        
        # If we don't have a title yet, generate one
        if not self.book_data["metadata"]["title"]:
            quality_analyst = self.agents["quality_analyst"]
            self.book_data["metadata"]["title"] = quality_analyst.generate_title(
                chapters=self.book_data["chapters"][:1],  # Just use first chapter for speed
                outline=self.book_data["outline"],
                genre=self.config.get("genre", "fiction")
            )
        title = self.book_data["metadata"]["title"]
        logger.info(f"Book title: {title}")
        
        # Check if title is a dictionary and extract just the title string
        if isinstance(title, dict) and 'title' in title:
            title = title['title']
            self.book_data["metadata"]["title"] = title
            logger.info(f"Extracted title string: {title}")
        
        # Create output formats
        formats = self.config.get("output_settings", {}).get("formats", ["txt", "epub"])
        if "txt" in formats:
            # Save as plain text
            self._save_as_text(title)
        
        if "epub" in formats:
            # Generate cover image if configured
            cover_image_path = None
            if self.config.get("output_settings", {}).get("generate_cover", True):
                cover_designer = self.agents["cover_designer"]
                try:
                    title = self.book_data["metadata"]["title"]
                    genre = self.config.get("genre", "fiction")
                    outline = self.book_data["outline"]
                    
                    cover_dir = os.path.join(self.output_dir, "images")
                    os.makedirs(cover_dir, exist_ok=True)
                    cover_image_path = os.path.join(cover_dir, "cover.png")
                    
                    logger.info(f"Generating cover image for '{title}'")
                    cover_image_path = cover_designer.generate_cover_image(
                        title=title,
                        genre=genre,
                        outline=outline,
                        output_path=cover_image_path,
                        orientation=self.config.get("output_settings", {}).get("cover_defaults", {}).get("orientation", "portrait")
                    )
                    
                    if cover_image_path:
                        logger.info(f"Cover image created: {cover_image_path}")
                    else:
                        logger.warning("Failed to generate cover image")
                except Exception as e:
                    logger.error(f"Error generating cover image: {e}")
                    cover_image_path = None
            
            # Create EPUB
            self._save_as_epub(title, cover_image_path)
        # Save final metadata
        metadata_path = os.path.join(self.output_dir, "book_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(self.book_data["metadata"], f, indent=2)
        
        logger.info(f"Book generation complete. Files saved to {self.output_dir}")
    
    def _perform_interim_check(self, chapter_num: int) -> None:
        """Perform a quick continuity check during chapter creation"""
        logger.info(f"Performing interim continuity check after chapter {chapter_num}")
        
        continuity_checker = self.agents["continuity_checker"]
        check_results = continuity_checker.quick_check(
            chapters=self.book_data["chapters"],
            character_profiles=self.book_data["character_profiles"]
        )
        
        if check_results.get("issues", []):
            logger.warning(f"Found {len(check_results['issues'])} continuity issues")
            
            # Record issues for later refinement
            self.book_data["reviews"].append({
                "type": "interim_continuity",
                "chapter": chapter_num,
                "results": check_results
            })
    
    def _save_intermediate_results(self, phase: str) -> None:
        """Save intermediate results from the current phase"""
        if not self.config.get("output_settings", {}).get("save_intermediates", True):
            return
            
        os.makedirs(os.path.join(self.output_dir, "intermediates"), exist_ok=True)
        phase_dir = os.path.join(self.output_dir, "intermediates", phase)
        os.makedirs(phase_dir, exist_ok=True)
        
        # Save relevant data based on phase
        if phase == "planning":
            # Save outline
            outline_path = os.path.join(phase_dir, "outline.txt")
            with open(outline_path, "w") as f:
                f.write(self.book_data["outline"])
            
            # Save character profiles
            profiles_path = os.path.join(phase_dir, "character_profiles.txt")
            with open(profiles_path, "w") as f:
                f.write(self.book_data["character_profiles"])
            
        elif phase == "creation":
            # Save all chapters
            combined_path = os.path.join(phase_dir, "all_chapters.txt")
            with open(combined_path, "w") as f:
                for i, chapter in enumerate(self.book_data["chapters"]):
                    f.write(f"Chapter {i+1}: {self.book_data['structured_outline'][i]['title']}\n\n")
                    f.write(chapter)
                    f.write("\n\n---\n\n")
        
        elif phase == "refinement" or phase == "qa":
            # Save reviews
            reviews_path = os.path.join(phase_dir, f"{phase}_reviews.json")
            with open(reviews_path, "w") as f:
                json.dump(self.book_data["reviews"], f, indent=2)
            
            # Save refined chapters
            refined_path = os.path.join(phase_dir, "refined_chapters.txt")
            with open(refined_path, "w") as f:
                for i, chapter in enumerate(self.book_data["chapters"]):
                    f.write(f"Chapter {i+1}: {self.book_data['structured_outline'][i]['title']}\n\n")
                    f.write(chapter)
                    f.write("\n\n---\n\n")
    
    def _save_chapter(self, chapter_num: int, content: str) -> None:
        """Save an individual chapter file"""
        chapters_dir = os.path.join(self.output_dir, "intermediates", "chapters")
        os.makedirs(chapters_dir, exist_ok=True)
        
        chapter_path = os.path.join(chapters_dir, f"chapter_{chapter_num:02d}.txt")
        with open(chapter_path, "w") as f:
            chapter_title = self.book_data["structured_outline"][chapter_num-1]["title"]
            f.write(f"Chapter {chapter_num}: {chapter_title}\n\n")
            f.write(content)
    
    def _save_as_text(self, title: str) -> None:
        """Save the book as a plain text file"""
        sanitized_title = self._sanitize_filename(title)
        text_path = os.path.join(self.output_dir, f"{sanitized_title}.txt")
        
        with open(text_path, "w") as f:
            f.write(f"{title}\n")
            f.write(f"by {self.book_data['metadata']['author']}\n\n")
            
            for i, chapter in enumerate(self.book_data["chapters"]):
                chapter_title = self.book_data["structured_outline"][i]["title"]
                f.write(f"Chapter {i+1}: {chapter_title}\n\n")
                f.write(chapter)
                f.write("\n\n")
        
        logger.info(f"Book saved as text file: {text_path}")
    
    def _save_as_epub(self, title: str, cover_image_path: Optional[str] = None) -> None:
        """Save the book as an EPUB file"""
        sanitized_title = self._sanitize_filename(title)
        epub_path = os.path.join(self.output_dir, f"{sanitized_title}.epub")
        
        # Create the EPUB
        create_epub(
            title=title,
            author=self.book_data["metadata"]["author"],
            chapters=self.book_data["chapters"],
            chapter_titles=[chapter["title"] for chapter in self.book_data["structured_outline"]],
            cover_image_path=cover_image_path,
            output_path=epub_path
        )
        
        logger.info(f"Book saved as EPUB file: {epub_path}")
    
    def _save_metrics(self) -> None:
        """Save execution metrics to a file"""
        metrics_path = os.path.join(self.output_dir, "generation_metrics.json")
        
        # Calculate total execution time
        start_time = datetime.fromisoformat(self.metrics["start_time"])
        end_time = datetime.fromisoformat(self.metrics["end_time"])
        self.metrics["total_time"] = (end_time - start_time).total_seconds()
        
        with open(metrics_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to be safe for use in file systems"""
        import re
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
        # Limit the filename length
        return sanitized[:100]