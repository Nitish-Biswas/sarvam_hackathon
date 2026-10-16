from correction_gemini import correcting
from create_video import creating_video
from extract_aduio import extracting_audio
from transformation import transforming
import streamlit as st
import os
import tempfile

def main():
    st.title("Video Audio Enhancement App") 
    uploaded_video = st.file_uploader("Upload a video",type=["mp4", "mov"])
    if uploaded_video:
        if st.button("Process Video"):
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(uploaded_video.getbuffer())  # Save uploaded video to temp file
                temp_file_path = temp_file.name
            
            with st.spinner("Processing..."):

                condition,extracted_audio= extracting_audio.extract_audio_from_video(temp_file_path)
                if not condition:
                    st.error(f"Error in extracting audio from video: {str(extracted_audio)}")
                    return


                condition,mono_audio = extracting_audio.convert_stereo_to_mono(extracted_audio)
                if not condition:
                    st.error(f"Error in converting in mono from stereo: {str(mono_audio)}")
                    return
                

                condition,word_timings= transforming.transcribe_audio(mono_audio)
                if not condition:
                    st.error(f"Error in transcripting audio: {str(word_timings)}")
                    return
                print(word_timings)


                condition, enhanced_text = correcting.correct_transcription(word_timings)
                if not condition:
                    st.error(f"Error in correcting text: {str(enhanced_text)}")
                    return
                
                print(enhanced_text)
                
                condition,segment_audios = transforming.generate_timed_speech(enhanced_text)
                if not condition:
                    st.error(f"Error in timed speech generation: {str(segment_audios)}")
                    return


                condition,combined_audio_path = creating_video.combine_audio_segments(extracted_audio,segment_audios)
                if not condition:
                    st.error(f"Error in combining audio: {str(combined_audio_path)}")
                    return
                
                condition, output_path = creating_video.sync_audio_with_video(temp_file_path, combined_audio_path)
                if not condition:
                    st.error(f"Error in syncing audio and video: {str(combined_audio_path)}")
                    return

                
                
                st.video(output_path)
            os.unlink(temp_file.name)
            os.unlink(combined_audio_path)
            os.unlink(output_path)
            os.unlink(extracted_audio)
            os.unlink(mono_audio)

        
if __name__ == "__main__":
    main()