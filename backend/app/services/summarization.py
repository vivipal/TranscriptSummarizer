import logging
from typing import Dict
import requests
import json

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self):
        self.ollama_url = "http://ollama:11434"
        self.model_name = "phi4"
        self.model = None
        # Load model on initialization
        self.load_model()

    def health_check(self) -> bool:
        """Check if model is loaded and Ollama is responsive"""
        try:
            # Check if Ollama is running and model exists
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"] == self.model_name for model in models)
            return False
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def load_model(self):
        """Create the Phi model in Ollama"""
        try:
            # First check if model already exists
            if self.health_check():
                logger.info("Model already exists")
                self.model = True  # Just set a flag that model is available
                return

            logger.info("Creating Phi model in Ollama...")
            modelfile = '''
FROM phi4:14b-q4_K_M
PARAMETER temperature 0.7
PARAMETER num_ctx 131072
PARAMETER num_gpu 50
TEMPLATE """
{{- if .System }}
{{.System}}
{{- end }}

{{.Prompt}}
"""
'''
            response = requests.post(
                f"{self.ollama_url}/api/create",
                json={
                    "name": self.model_name,
                    "modelfile": modelfile,
                }
            )
            if response.status_code == 200:
                logger.info("Model created successfully")
                self.model = True  # Set flag that model is available
            else:
                logger.error(f"Failed to create model: {response.text}")
                raise Exception(f"Failed to create model: {response.text}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def generate_summary(self, text: str) -> Dict:
        """Generate summary using Ollama"""
        try:
            if not text:
                return {
                    "overview": "No text provided",
                    "main_points": [],
                    "key_insights": [],
                    "action_items_decisions": [],
                    "open_questions_next_steps": [],
                    "conclusions": [],
                    "full_text": ""
                }

            # Updated system prompt with recommended sections and instructions
            system_prompt = """
You are a helpful AI assistant specialized in summarizing transcripts from various contexts such as training sessions, business meetings, or technical discussions. Your goal is to create a concise, clear, and actionable summary of the provided text.

### Instructions

1. **Identify key topics, tasks, decisions, and any potential risks or impacts** discussed in the transcript.
2. **Do not invent information** and do not include speculation. If something is unclear, explicitly note that it was unclear.
3. **Retain important details** such as:
   - Names or roles of responsible individuals (owners)
   - Dates, deadlines, or specific milestones (when available)
   - Relevant financial or technical figures, if explicitly mentioned
4. **Use these exact section headings** in your summary:
   1. **Overview**: (1–3 sentences on the overall context and purpose)
   2. **Main Points**: (list important details, themes, or topics in bullet form)
   3. **Key Insights**: (highlight major takeaways, implications, or risks in bullet form)
   4. **Action Items / Decisions**:
      - Specify **owner** and **deadline** for each task if possible
      - Call out any direct decisions made during the meeting
   5. **Open Questions / Next Steps**:
      - List unresolved issues or future steps in bullet form
      - If deadlines or owners are known, include them
   6. **Conclusions**: (final wrap-up, including major outcomes or final statements)

### Formatting

- Present each section **clearly labeled**.
- Use **bullet points** or concise paragraphs within each section.
- **Avoid repetition** of the same details across multiple sections.
- Keep the wording **direct and clear**, focusing on essential information only.
- Summaries should be **as short as possible while remaining complete**.

### Additional Guidance

- **Highlight potential risks or impacts** where relevant (e.g., cost implications, schedule delays).
- **Do not include** speculative or hypothetical information that was not stated in the transcript.
- **Be mindful** of sensitive details (financial figures, personal info). Include them only if the transcript explicitly mentions them.
- **If anything is unclear or missing**, note that it was unclear rather than inventing details.
"""

            logger.info("Generating summary with Ollama...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "system": system_prompt,
                    "prompt": f"Please summarize this text:\n\n{text}",
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 131072,
                        "num_gpu": 50
                    }
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")

            summary_text = response.json()["response"]
            logger.info(f"Generated summary text: {summary_text}")

            # Prepare our results structure with the new sections
            sections = {
                "overview": "",
                "main_points": [],
                "key_insights": [],
                "action_items_decisions": [],
                "open_questions_next_steps": [],
                "conclusions": [],
                "full_text": summary_text
            }

            # Parsing the summary text
            current_section = None
            current_points = []

            for line in summary_text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                lower_line = line.lower()

                if 'overview:' in lower_line:
                    # Store what we have in current_points before moving on
                    if current_section == 'main_points':
                        sections['main_points'] = current_points
                    elif current_section == 'key_insights':
                        sections['key_insights'] = current_points
                    elif current_section == 'action_items_decisions':
                        sections['action_items_decisions'] = current_points
                    elif current_section == 'open_questions_next_steps':
                        sections['open_questions_next_steps'] = current_points
                    elif current_section == 'conclusions':
                        sections['conclusions'] = current_points

                    current_section = 'overview'
                    current_points = []
                    # Capture text after 'Overview:'
                    sections['overview'] = line.split(':', 1)[1].strip()

                elif 'main points:' in lower_line:
                    # Store the previous section's content
                    if current_section == 'overview':
                        # Already stored overview text
                        pass
                    elif current_section == 'key_insights':
                        sections['key_insights'] = current_points
                    elif current_section == 'action_items_decisions':
                        sections['action_items_decisions'] = current_points
                    elif current_section == 'open_questions_next_steps':
                        sections['open_questions_next_steps'] = current_points
                    elif current_section == 'conclusions':
                        sections['conclusions'] = current_points

                    current_section = 'main_points'
                    current_points = []

                elif 'key insights:' in lower_line:
                    # Store current main_points
                    if current_section == 'main_points':
                        sections['main_points'] = current_points
                    elif current_section == 'overview':
                        pass
                    elif current_section == 'action_items_decisions':
                        sections['action_items_decisions'] = current_points
                    elif current_section == 'open_questions_next_steps':
                        sections['open_questions_next_steps'] = current_points
                    elif current_section == 'conclusions':
                        sections['conclusions'] = current_points

                    current_section = 'key_insights'
                    current_points = []

                elif 'action items / decisions:' in lower_line:
                    # Store key_insights
                    if current_section == 'key_insights':
                        sections['key_insights'] = current_points
                    elif current_section == 'main_points':
                        sections['main_points'] = current_points
                    elif current_section == 'overview':
                        pass
                    elif current_section == 'open_questions_next_steps':
                        sections['open_questions_next_steps'] = current_points
                    elif current_section == 'conclusions':
                        sections['conclusions'] = current_points

                    current_section = 'action_items_decisions'
                    current_points = []

                elif 'open questions / next steps:' in lower_line:
                    # Store action_items_decisions
                    if current_section == 'action_items_decisions':
                        sections['action_items_decisions'] = current_points
                    elif current_section == 'key_insights':
                        sections['key_insights'] = current_points
                    elif current_section == 'main_points':
                        sections['main_points'] = current_points
                    elif current_section == 'overview':
                        pass
                    elif current_section == 'conclusions':
                        sections['conclusions'] = current_points

                    current_section = 'open_questions_next_steps'
                    current_points = []

                elif 'conclusions:' in lower_line:
                    # Store open_questions_next_steps
                    if current_section == 'open_questions_next_steps':
                        sections['open_questions_next_steps'] = current_points
                    elif current_section == 'action_items_decisions':
                        sections['action_items_decisions'] = current_points
                    elif current_section == 'key_insights':
                        sections['key_insights'] = current_points
                    elif current_section == 'main_points':
                        sections['main_points'] = current_points
                    elif current_section == 'overview':
                        pass

                    current_section = 'conclusions'
                    current_points = []

                elif line.startswith('-') and current_section in [
                    'main_points',
                    'key_insights',
                    'action_items_decisions',
                    'open_questions_next_steps',
                    'conclusions'
                ]:
                    current_points.append(line.lstrip('- ').strip())
                else:
                    # If it's an overview or a line that doesn't match the above sections
                    if current_section == 'overview' and sections['overview']:
                        # Append to the overview text
                        sections['overview'] += " " + line
                    elif current_section in [
                        'main_points',
                        'key_insights',
                        'action_items_decisions',
                        'open_questions_next_steps',
                        'conclusions'
                    ]:
                        # If we want to treat these as bullet items
                        current_points.append(line.strip())

            # After the loop, store the last batch of points if needed
            if current_section == 'main_points':
                sections['main_points'] = current_points
            elif current_section == 'key_insights':
                sections['key_insights'] = current_points
            elif current_section == 'action_items_decisions':
                sections['action_items_decisions'] = current_points
            elif current_section == 'open_questions_next_steps':
                sections['open_questions_next_steps'] = current_points
            elif current_section == 'conclusions':
                sections['conclusions'] = current_points

            return sections

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            logger.exception("Full traceback:")
            return {
                "overview": f"Error in summary generation: {str(e)}",
                "main_points": [],
                "key_insights": [],
                "action_items_decisions": [],
                "open_questions_next_steps": [],
                "conclusions": [],
                "full_text": f"Error in summary generation: {str(e)}"
            }