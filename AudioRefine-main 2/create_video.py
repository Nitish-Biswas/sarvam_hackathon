import os
import tempfile
from moviepy.editor import VideoFileClip,AudioFileClip
from pydub import AudioSegment

class creating_video:

    def combine_audio_segments(orginal_audio,segment_audios):
        
        try:

            orginal = AudioSegment.from_file(orginal_audio)
            total_duration = len(orginal)/1000

            
            # Create base silent audio
            silent_audio = AudioSegment.silent(duration=total_duration * 1000)  
            
            # Overlay each segment at its specific time
            combined_audio = silent_audio
            
            for segment in segment_audios:
                print("alf")
                segment_audio = AudioSegment.from_wav(segment['path'])
                position = (segment['timing']['start']) * 1000 
                combined_audio = combined_audio.overlay(segment_audio, position=int(position))
            
            # Export combined audio
            temp_combined = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            combined_audio.export(temp_combined.name, format="wav")
            
            # Clean up segment files
            for segment in segment_audios:
                os.unlink(segment['path'])
            
            return [True,temp_combined.name]
        except Exception as e:
            return [False,e]

    def sync_audio_with_video(video_path, new_audio_path):
        
        try:
            video = VideoFileClip(video_path)
            audio = AudioFileClip(new_audio_path)
            
            # Combine video with new audio
            final_video = video.set_audio(audio)
            
            temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            
            final_video.write_videofile(temp_video.name, codec='libx264', audio_codec='aac')
            
            return [True,temp_video.name]
        except Exception as e:
            return [False,e]
        