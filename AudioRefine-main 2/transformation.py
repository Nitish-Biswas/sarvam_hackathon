from google.cloud import speech, texttospeech
import tempfile
from pydub import AudioSegment
import subprocess
import os

class transforming:
    def transcribe_audio(audio_file_path):
        try:
            client = speech.SpeechClient()

            with open(audio_file_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code="en-US",  
                enable_word_time_offsets=True, 
            )

            response = client.recognize(config=config, audio=audio)
            
            transcript = ""
            word_timings = []
                
            for result in response.results:
                for word_info in result.alternatives[0].words:
                    word_timings.append({
                        'word': word_info.word,
                        'start_time': word_info.start_time.total_seconds(),
                        'end_time': word_info.end_time.total_seconds()
                    })
                transcript += result.alternatives[0].transcript + " "
                    
            return [True, word_timings]
        except Exception as e:
            return [False, e]


    def generate_timed_speech(enhanced_segments):
        
        try:
            segment_audios = []
            seg_record=[]
            client = texttospeech.TextToSpeechClient()
            
            for segment in enhanced_segments:
                if not segment['text'] or segment['text'] == "em404$":
                    continue
                input_text = texttospeech.SynthesisInput(text=segment['text'])
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-IN",
                    name="en-IN-Journey-D"
                )
                
                # Calculate desired duration for this segment
                desired_duration = segment['timing']['end'] - segment['timing']['start']
                
                # First generate with normal rate to get base duration
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                    speaking_rate=1.0
                )
                
                response = client.synthesize_speech(
                    input=input_text,
                    voice=voice,
                    audio_config=audio_config
                )
                
        
                temp_check = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                with open(temp_check.name, "wb") as out:
                    out.write(response.audio_content)
                
                # Get duration of generated audio
                temp_audio = AudioSegment.from_file(temp_check.name)
                base_duration = len(temp_audio)/1000
                
                speaking_rate = base_duration / desired_duration
                
                speaking_rate = max(0.25, min(4.0, speaking_rate))
                
                temp_segment = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                command = [
                    "ffmpeg","-y", "-i", temp_check.name, 
                    "-filter:a", f"atempo={speaking_rate}", 
                    "-vn", temp_segment.name
                ]
                subprocess.run(command)
                
                
                os.unlink(temp_check.name)
                
                segment_audios.append({
                    'path': temp_segment.name,
                    'timing': segment['timing'],
                })
            
            return [True,segment_audios]
        except Exception as e:
        
            return [False,e]