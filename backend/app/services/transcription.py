import whisper
import logging
import tempfile
import os
from fastapi import UploadFile
import torch

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, model_size="small"):
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        logger.info(f"TranscriptionService initialized for {model_size} model on {self.device}")

    def load_model(self):
        """Load the Whisper model if not already loaded"""
        if self.model is None:
            logger.info(f"Loading Whisper {self.model_size} model on {self.device}")
            try:
                self.model = whisper.load_model(self.model_size)
                logger.info(f"Whisper {self.model_size} model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                raise

    async def transcribe(self, file: UploadFile) -> str:
        """Transcribe audio file using Whisper"""
        try:
            logger.info(f"Starting transcription for {file.filename}")
            
            # Load model if not already loaded
            self.load_model()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp.flush()
                
                logger.info("Processing audio with Whisper...")
                result = self.model.transcribe(
                    tmp.name,
                    # language='en',
                    task='transcribe',
                    fp16=torch.cuda.is_available(),
                    verbose=False,
                    temperature=0.0,  # Use greedy decoding
                    best_of=1,        # No need for multiple samples with temperature=0
                    beam_size=5       # Beam search size
                )
                
                # Clean up the temporary file
                os.unlink(tmp.name)
                
                transcription = result["text"]
                
                # Unload model to free GPU memory
                logger.info("Transcription complete, unloading model...")
                self.unload_model()
                
                return transcription
                
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            # Ensure model is unloaded even if transcription fails
            self.unload_model()
            raise Exception(f"Transcription failed: {str(e)}")

    def unload_model(self):
        """Unload the model to free up GPU memory"""
        try:
            if hasattr(self, 'model'):
                del self.model
                self.model = None
                torch.cuda.empty_cache()
                logger.info("Whisper model unloaded successfully")
        except Exception as e:
            logger.error(f"Error unloading model: {str(e)}")
